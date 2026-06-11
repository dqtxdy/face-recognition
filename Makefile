.PHONY: test smoke benchmark-demo chain-demo robustness-demo deep-smoke contracts-compile api api-openapi demo-app check

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

contracts-compile:
	npm run compile:contracts

api:
	PYTHONPATH=src python3 -m uvicorn trustfacechain.api:app --host 127.0.0.1 --port 8080

api-openapi:
	PYTHONPATH=src python3 scripts/export-openapi.py

check: test smoke benchmark-demo chain-demo robustness-demo contracts-compile api-openapi

demo-app:
	PYTHONPATH=src streamlit run app/streamlit_app.py --server.address 127.0.0.1 --server.port 8501 --server.headless true --browser.gatherUsageStats false
