import re
from typing import List


def parse_receipt_raw(transactions):
    for trans in transactions:
        if "receipt_raw" in trans:
            _parse_receipt_raw(trans)


def _parse_receipt_raw(trans):
    parser = ReceiptParser()
    parser.feed(trans.pop("receipt_raw"))
    receipt_data = parser.data

    if "store_number" not in receipt_data:
        trans.setdefault("warning", []).append(
            "Missing store number (never started parsing)"
        )

    if receipt_data.get("skipped"):
        trans.setdefault("warning", []).append(
            "Some of the receipt lines have not been accouned for (skipped)"
        )

    trans["receipt_data"] = receipt_data


class ReceiptParser:
    def __init__(self):
        self.data = None
        self.store_number = None
        self.current_category = None

    def feed(self, receipt_raw: List[str]):
        self.data = {}
        self.current_category = None

        for line in receipt_raw:
            if line.isspace():
                # skip lines that are all spaces
                continue

            if "store_number" not in self.data:
                # throw out all the lines before the store number
                # (the next line starts the produce)
                x = re.search("^Store #(\d+)", line)
                if x:
                    self.data["store_number"] = int(x.group(1))
                continue

            self.data.setdefault("skipped", []).append(line)

        # FIXME finish
        pass
