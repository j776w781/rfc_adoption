# OpenINTEL RFC-adoption matching pipeline
#
# All targets are runnable from this directory. PY can be overridden, e.g.
#   make demo PY=python3

PY          ?= python
PIP         ?= $(PY) -m pip
CHECKLISTS  ?= data/rfc_checklists/dnssec_rfc_checklists.json
DICTIONARY  ?= data/openintel_dictionary/sample_openintel_dictionary.json
PARQUET     ?= data/sample_parquet/sample_openintel.parquet
OUT         ?= demo_output
SURVEY      ?= docs/open_source_tool_survey.md

export PYTHONPATH := src

.PHONY: help install sample survey schema-check analyze demo dashboard test clean

help:
	@echo "install       Install runtime + test dependencies"
	@echo "sample        Regenerate the sample OpenINTEL Parquet file"
	@echo "survey        Generate docs/open_source_tool_survey.md"
	@echo "schema-check  Cross-check RFC indicators against the OpenINTEL dictionary"
	@echo "analyze       Run the full matching pipeline into $(OUT)/"
	@echo "demo          sample + survey + schema-check + analyze"
	@echo "dashboard     Launch the Streamlit dashboard"
	@echo "test          Run the pytest suite"
	@echo "clean         Remove generated demo output"

install:
	$(PIP) install -r requirements.txt

sample:
	$(PY) data/sample_parquet/create_sample_parquet.py

survey:
	$(PY) -m openintel_rfc.cli tool-survey --out $(SURVEY)

schema-check:
	$(PY) -m openintel_rfc.cli schema-check \
		--checklists $(CHECKLISTS) \
		--dictionary $(DICTIONARY) \
		--out $(OUT)

analyze:
	$(PY) -m openintel_rfc.cli analyze \
		--checklists $(CHECKLISTS) \
		--dictionary $(DICTIONARY) \
		--parquet $(PARQUET) \
		--out $(OUT)

demo: sample survey schema-check analyze
	@echo "Demo complete. Artefacts are in $(OUT)/"

dashboard:
	$(PY) -m streamlit run dashboard/app.py

test:
	$(PY) -m pytest

clean:
	$(PY) -c "import pathlib, shutil; d = pathlib.Path('$(OUT)'); [p.unlink() for p in d.glob('*') if p.is_file() and p.name != '.gitkeep']" || true
