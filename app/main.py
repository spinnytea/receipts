import json
import sys

from parse.mail import parse_mbox_file


def eml_to_stats(mbox_filepath):
    transactions = parse_mbox_file(mbox_filepath)

    # TODO parse date
    # TODO parse html -> receipt paper
    # TODO parse receipt paper -> itemized

    print(f"parse {len(transactions)} messages")
    print(f"{json.dumps(transactions, indent=2)}")

    # TODO stats


if __name__ == "__main__":
    mbox_filepath = sys.argv[1]
    eml_to_stats(mbox_filepath)
