import json
import sys

from parse.mail import parse_mbox_file
from parse.receipt import parse_html_body


def eml_to_stats(mbox_filepath):
    transactions = parse_mbox_file(mbox_filepath)
    parse_html_body(transactions)

    # TODO write some unit tests
    #  - just isolate one email or something
    #  - and write tests for every step of the way

    # TODO parse date
    # TODO parse receipt paper -> itemized

    print(f"parse {len(transactions)} messages")
    print(f"{json.dumps(transactions, indent=2)}")

    # TODO stats


if __name__ == "__main__":
    mbox_filepath = sys.argv[1]
    eml_to_stats(mbox_filepath)
