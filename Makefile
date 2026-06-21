API_HOST ?= 127.0.0.1
API_PORT ?= 8080

.PHONY: test smoke benchmark-demo chain-demo robustness-demo deep-smoke deep-defense hard-benchmark contracts-compile chain-live api api-openapi web build-web demo-app check

test:
	PYTHONPATH=src python3 -m unittest discover -s tests

smoke:
	PYTHONPATH=src python3 -m trustfacechain.cli smoke-benchmark

benchmark-demo:
	PYTHONPATH=src python3 -m trustfacechain.cli benchmark-demo --csv reports/demo_metrics.csv --json reports/demo_report.json

chain-demo:
	PYTHONPATH=src python3 -m trustfacechain.cli demo-chain-flow

robustness-demo:
	PYTHONPATH=src python3 -m trustfacechain.cli robustness-demo --csv reports/robustness_demo.csv

deep-smoke:
	PYTHONPATH=vendor/face:src python3 -m trustfacechain.cli benchmark-lfw-pairs --max-pairs 20 --models arcface,mobileface --csv reports/lfw_deep_smoke_metrics.csv --json reports/lfw_deep_smoke_report.json

deep-defense:
	PYTHONPATH=vendor/face:src python3 -m trustfacechain.cli benchmark-lfw-pairs --max-pairs $${DEEP_PAIRS:-120} --models arcface,mobileface --csv reports/lfw_deep_defense_metrics.csv --json reports/lfw_deep_defense_report.json

hard-benchmark:
	@test -n "$(PAIRS_CSV)" || (echo "Set PAIRS_CSV=path/to/pairs.csv" && exit 2)
	PYTHONPATH=$${PYTHONPATH:-src} python3 -m trustfacechain.cli benchmark-pairs-csv "$(PAIRS_CSV)" --models $${MODELS:-pixel,dct} --csv reports/hard_pairs_metrics.csv --json reports/hard_pairs_report.json

contracts-compile:
	npm run compile:contracts

chain-live: contracts-compile
	npm run chain:local

api:
	PYTHONPATH=vendor/face:src python3 -m uvicorn trustfacechain.api:app --host $(API_HOST) --port $(API_PORT)

api-openapi:
	PYTHONPATH=src python3 scripts/export-openapi.py

web:
	npm run web

build-web:
	npm run build:web

check: test smoke benchmark-demo chain-demo robustness-demo contracts-compile api-openapi build-web

demo-app:
	PYTHONPATH=src streamlit run app/streamlit_app.py --server.address 127.0.0.1 --server.port 8501 --server.headless true --browser.gatherUsageStats false
