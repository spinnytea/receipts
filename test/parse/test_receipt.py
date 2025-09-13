import unittest

from app.parse.mail import parse_mbox_file
from app.parse.receipt import _parse_receipt_raw


class TestParseReceipt(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.transactions = parse_mbox_file("raw/dumps/Purchase-Groceries.mbox")
        with open("raw/receipt_raw_sample.txt", "r", encoding="utf-8") as file:
            self.receipt_raw_sample = file.read()
        self.receipt_raw_sample = [
            line.strip('"') for line in self.receipt_raw_sample.splitlines()
        ]

        # FIXME parse_receipt_raw(self.transactions)

    def test_loaded_data(self):
        self.assertEqual(len(self.receipt_raw_sample), 127)

        all_lens = set()
        for line in self.receipt_raw_sample:
            all_lens.add(len(line))
        self.assertEqual(all_lens, {38})

    def test_receipt_raw_sample(self):
        trans = {"id": "receipt_raw_sample", "receipt_raw": self.receipt_raw_sample}
        _parse_receipt_raw(trans)

        self.assertEqual(sorted(trans.keys()), ["id", "receipt_data", "warning"])
        self.assertEqual(
            sorted(trans["receipt_data"].keys()), ["skipped", "store_number"]
        )

        data_cp = trans["receipt_data"].copy()
        data_cp.pop("skipped")
        self.assertEqual(data_cp, {"store_number": 55})

        # self.assertEqual(trans["receipt_data"].get("skipped"), [])
        # FIXME finish
