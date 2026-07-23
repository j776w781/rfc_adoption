import os
import datetime
import fnmatch
import tempfile
import time
import dateutil

from pyspark import SparkContext, SparkConf
from pyspark.sql import SparkSession
import pyspark
import pyspark.sql.functions as psf

import boto3
import botocore
import pandas as pd







# The OpenINTEL repository endpoint (S3-capable)
OI_ENDPOINT = "https://object.openintel.nl"

# The forward DNS (fDNS) bucket, measurement data bases 
OI_BUCKET_NAME = "openintel-public"
OI_FDNS_BASE = "fdns"
OI_FDNS_ZONEBASED = OI_FDNS_BASE + "/basis=zonefile" # zonefile-based fDNS measurement data
OI_FDNS_LISTBASED = os.path.join(OI_FDNS_BASE, "basis=toplist")  # toplist-based fDNS measurement data
OI_OBJECT_SUFFIX = "gz.parquet"


# Get a boto Resource
S3R_OPENINTEL = boto3.resource(
    "s3",
    "nl-utwente",
    endpoint_url          = OI_ENDPOINT,
    # We're using anonymous access
    config = botocore.config.Config(
        signature_version = botocore.UNSIGNED,
    )
)

# Get its client, for lower-level actions, if needed
S3C_OPENINTEL = S3R_OPENINTEL.meta.client

# Prevent some request going to AWS instead of our server
S3C_OPENINTEL.meta.events.unregister('before-sign.s3', botocore.utils.fix_s3_host)

# The OpenINTEL data bucket
OI_BUCKET = S3R_OPENINTEL.Bucket(OI_BUCKET_NAME)




# The date(s) to download
DO_DATES = list(dateutil.rrule.rrule(dateutil.rrule.DAILY, dtstart=datetime.datetime(2017, 3, 1), until=datetime.datetime(2017, 3, 2)))

# The public source(s) to download (see index: https://openintel.nl/download/forward-dns/)
DO_SOURCES = {
    OI_FDNS_ZONEBASED : [
        "nu",
    ],
}

print(OI_BUCKET.name)
all_data = [] # list of dicts with data from individual objects
# Iter dates
for i_date in DO_DATES:

    # Iter source bases
    for i_source_base in DO_SOURCES.keys():

        # Iter base's sources
        if len(DO_SOURCES[i_source_base]) > 0:
            for i_source in DO_SOURCES[i_source_base]:
    
                # Build a partition path
                i3_data_partifion_prefix = "/".join([
                    i_source_base,
                    f"source={i_source}",
                    f"year={i_date.year}",
                    f"month={i_date.month:02d}",
                    f"day={i_date.day:02d}"
                ]) + "/"
                # List objects under partition path
                i3_s3_lo = S3C_OPENINTEL.list_objects_v2(Bucket="openintel-public", Prefix=i3_data_partifion_prefix, Delimiter="/")

                print(i3_data_partifion_prefix)
                #print(i3_s3_lo)
                # Are there objects?
                print("Contents" in i3_s3_lo)
                if "Contents" in i3_s3_lo:
                    print("Contents found")
                    # Iterate objects
                    for i_content in i3_s3_lo["Contents"]:
                        
                        # Load data at given key
                        if fnmatch.fnmatch(i_content["Key"], "*." + OI_OBJECT_SUFFIX):

                            # Open a temporary file to download the object into
                            with tempfile.NamedTemporaryFile(mode="w+b", prefix="{}.".format(i_date.date().isoformat()), suffix="." + OI_OBJECT_SUFFIX, delete=False) as tempFile:
                        
                                print("Opened temporary file for object download: '{}'.".format(tempFile.name))
                                
                                # Download file object
                                OI_BUCKET.download_fileobj(
                                    Key = i_content["Key"],
                                    Fileobj = tempFile,
                                    # Please note that a small chunksize may trigger the request rate limiter
                                    Config = boto3.s3.transfer.TransferConfig(multipart_chunksize = 64*1024*1024)
                                )
                                print("Downloaded '{}' [{:.2f}MiB] into '{}'.".format(os.path.join(OI_BUCKET.name, i_content["Key"]), os.path.getsize(tempFile.name) / (1024*1024), tempFile.name))
                                
                                tempFile.flush()
                                tempFile.close()    

                                ## Use Pandas to read file into a DF and append to list
                                # n.b.: this isn't exactly efficient
                                i_obj_pdf = pd.read_parquet(
                                    path = tempFile.name,
                                    # We read only the columns we are interested in (see: https://openintel.nl/background/dictionary/)
                                    columns = ["query_name", "response_type"]
                                )
                                # Add partition columns (these columns are not contained in the files themselves)
                                i_obj_pdf["source"] = i_source
                                i_obj_pdf["year"] = i_date.year
                                i_obj_pdf["month"] = i_date.month
                                i_obj_pdf["day"] = i_date.day

                                # Extend list of data records
                                all_data.extend(
                                    # We use a list of dictionaries for performance
                                    i_obj_pdf.to_dict(orient='records')
                                )
                                del i_obj_pdf
                                os.remove(tempFile.name)


# Create Pandas DF using data records from objects
pandas_df = pd.DataFrame.from_records(all_data)
print("done: read {} records".format(len(pandas_df)))