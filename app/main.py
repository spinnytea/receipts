import json
import os
import sys

from parse.date import datetime_serializer, parse_date_raw
from parse.html import parse_body_html
from parse.mail import parse_mbox_file
from parse.receipt import parse_receipt_raw


def eml_to_stats(mbox_filepath):
    transactions = parse_mbox_file(mbox_filepath)
    parse_date_raw(transactions)
    parse_body_html(transactions)
    save_json("raw/receipt_raw.json", transactions)
    parse_receipt_raw(transactions)

    print(f"parse {len(transactions)} messages")
    warning_count = sum("skipped" in trans["receipt_data"] for trans in transactions)
    if warning_count:
        print(f"still have {warning_count} transactions with skipped lines")
    warning_count = sum("warning" in trans for trans in transactions)
    if warning_count:
        print(f"still have {warning_count} messages with warnings")
    print(f"{json.dumps(transactions, indent=2, default=datetime_serializer)}")

    # TODO load .eml
    # TODO load every file in folder
    # TODO de-dup (by date?)
    # TODO parse date on reciept (store day time, day time 111 222 33 000000)
    # TODO TOTAL NUMBER OF ITEMS SOLD

    # TODO keep adding test cases until there are not skipped
    # TODO stats


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
    mbox_filepath = sys.argv[1]
    eml_to_stats(mbox_filepath)
