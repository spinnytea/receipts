import json
import os
import sys

from app.parse.date import datetime_serializer, parse_date_raw
from app.parse.html import parse_body_html
from app.parse.mail import traverse_files_recursive
from app.parse.receipt import parse_receipt_raw
from app.process.stats import stats_graph_agg, stats_sum_receipt_parsed


def eml_to_stats(data_dumps_directory):
    transactions = traverse_files_recursive(data_dumps_directory)
    parse_date_raw(transactions)
    parse_body_html(transactions)
    save_json("data/receipt_raw.json", transactions)
    parse_receipt_raw(transactions)
    save_json("data/receipt_parsed.json", transactions)

    print(f"parse {len(transactions)} messages")
    warning_count = sum("skipped" in trans["receipt_data"] for trans in transactions)
    if warning_count:
        print(f"still have {warning_count} transactions with skipped lines")
    warning_count = sum("warning" in trans for trans in transactions)
    if warning_count:
        print(f"still have {warning_count} messages with warnings")

    agg = stats_sum_receipt_parsed(transactions)
    # print(f"{json.dumps(agg, indent=2, default=datetime_serializer)}")
    print(f"\nFrom: {agg['date_min']}\n  To: {agg['date_max']}")
    print(stats_graph_agg(agg, half=True, log_base=1.5))

    # TODO parse date on reciept (store day time, day time 111 222 33 000000)
    # TODO TOTAL NUMBER OF ITEMS SOLD

    # XXX stats (numpy)
    #  - make a datatable
    #  - collect total categories
    #  - filter by date, sum categories
    #  - graph? (for fun)
    # XXX stats (pandas)
    #  - venv
    #  - python3.12
    #  - move ruff, isort
    #  - pandas


# @warnings.deprecated("control flow is weird")
def cached_generate(filepath, callback):
    """
    try to load json from `filepath`
    if not present, call `callback()`, and save it to `filepath` for next time
    """
    if os.path.isfile(filepath):
        return load_json(filepath)
    data = callback()
    save_json(filepath, data)
    return data


def load_json(filepath):
    print(f"loading {filepath}")
    with open(filepath, "r") as file:
        return json.loads(file.read())


def save_json(filepath, data):
    print(f"saving {filepath}")
    with open(filepath, "w") as file:
        file.write(json.dumps(data, indent=2, default=datetime_serializer))


if __name__ == "__main__":
    data_dumps_directory = sys.argv[1]
    eml_to_stats(data_dumps_directory)
