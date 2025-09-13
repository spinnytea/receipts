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
    parse_receipt_raw(transactions)

    print(f"parse {len(transactions)} messages")
    print(f"{json.dumps(transactions, indent=2, default=datetime_serializer)}")

    # TODO stats


if __name__ == "__main__":
    mbox_filepath = sys.argv[1]
    eml_to_stats(mbox_filepath)
