# make all
# make test filter=test.parse.test_receipt

.PHONY: lint test test_once run all

all: lint test_once run

# python3 -m pip install isort ruff
lint:
	python3 -m isort .
	python3 -m ruff format .
	python3 -m ruff check --fix

test_once:
	@echo
	python3 -m unittest
	@echo

# npm install -g nodemon
test: lint
	nodemon --watch app --watch raw --watch test --ext mbox,py --exec python3 -m unittest $(filter)

run:
	python3 app/main.py "raw/dumps/Purchase-Groceries.mbox" > temp.out
