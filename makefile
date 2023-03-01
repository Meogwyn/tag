.PHONY: run

run:
	@python -m tag
asclient:
	python tag/tests/as_client.py
setup:
	pip install -r requirements.txt
