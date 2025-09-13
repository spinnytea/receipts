import unittest

from app.parse.html import parse_body_html
from app.parse.mail import parse_mbox_file


class TestParseHtml(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        transactions = parse_mbox_file("raw/dumps/Purchase-Groceries.mbox")
        parse_body_html(transactions)

        self.transactions = transactions
        self.one = transactions[39]

    def test_all_keys(self):
        for trans in self.transactions:
            self.assertEqual(
                sorted(trans.keys()),
                ["date_raw", "id", "idx", "receipt_raw"],
                f"bad keys for transaction {trans['id']}",
            )

    def test_all_lens(self):
        """
        this is over testing
        not sure this really matters
        """
        for trans in self.transactions:
            for line in trans["receipt_raw"]:
                self.assertEqual(len(line), 38)

    def test_one(self):
        trans = self.one
        self.assertEqual(sorted(trans.keys()), ["date_raw", "id", "idx", "receipt_raw"])

        receipt_raw = trans["receipt_raw"]
        self.assertEqual(len(receipt_raw), 53)
        self.assertEqual(len(receipt_raw[0]), 38)

        all_lens = set([len(line) for line in receipt_raw])
        self.assertEqual(all_lens, {38})
