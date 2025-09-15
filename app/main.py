import json
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

    # TODO keep adding test cases until there are not skipped
    # TODO stats


def save_json(filepath, data):
    with open(filepath, "w") as file:
        file.write(json.dumps(data, indent=2, default=datetime_serializer))


if __name__ == "__main__":
    mbox_filepath = sys.argv[1]
    eml_to_stats(mbox_filepath)
