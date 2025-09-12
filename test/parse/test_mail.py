import unittest

from app.parse.mail import parse_mbox_file


class TestParseMail(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.transactions = parse_mbox_file("raw/dumps/Purchase-Groceries.mbox")

    def test_count(self):
        self.assertEqual(len(self.transactions), 42)

    def test_one(self):
        trans = self.transactions[39]
        self.assertEqual(sorted(trans.keys()), ["body_html", "date_raw", "idx"])
        self.assertEqual(trans["idx"], 39)
        self.assertEqual(trans["date_raw"], "Sat, 26 Apr 2025 15:23:14 +0000")
