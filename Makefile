# make all
# make test filter=test.parse.test_receipt
# make test filter=test.parse.test_receipt.TestParseReceiptUnits

.PHONY: lint test test_once run clean all

all: clean lint test_once run

# python3 -m pip install isort ruff
lint:
	@echo
	python3 -m isort .
	python3 -m ruff format .
	python3 -m ruff check --fix
	@echo

test_once:
	@echo
	python3 -m unittest
	@echo

# npm install -g nodemon
test: lint
	@echo
	nodemon --watch app --watch data --watch test --ext mbox,py --exec python3 -m unittest $(filter)
	@echo

run:
	@echo
	python3 main.py "data/dumps" > data/temp.out
	@echo

clean:
	@echo
	rm -f data/receipt_raw.json data/receipt_parsed.json data/temp.out
	@echo
