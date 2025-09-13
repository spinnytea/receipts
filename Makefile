# make test filter=test.parse.test_receipt
.PHONY: lint test run

lint:
	python3 -m isort .
	python3 -m ruff format .

test: lint
	nodemon --watch app --watch raw --watch test --ext mbox,py --exec  python3 -m unittest $(filter)

run: lint
	python3 app/main.py "raw/dumps/Purchase-Groceries.mbox" > temp.out
