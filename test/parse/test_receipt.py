import unittest

from app.parse.mail import parse_mbox_file
from app.parse.receipt import parse_html_body


class TestParseReceipt(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        transactions = parse_mbox_file("raw/dumps/Purchase-Groceries.mbox")
        parse_html_body(transactions)
        self.one = transactions[39]

    def test_one(self):
        trans = self.one
        self.assertEqual(sorted(trans.keys()), ["date_raw", "idx", "receipt_raw"])
        self.assertEqual(trans["idx"], 39)
        self.assertEqual(trans["date_raw"], "Sat, 26 Apr 2025 15:23:14 +0000")

        receipt_raw = trans["receipt_raw"]
        self.assertEqual(len(receipt_raw), 53)
