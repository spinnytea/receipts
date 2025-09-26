import unittest

from app.parse.mail import parse_mbox_file


class TestParseMail(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.transactions = parse_mbox_file("raw/test_data/test_simple.mbox")

    def test_count(self):
        self.assertEqual(len(self.transactions), 1)

    def test_all_keys(self):
        for trans in self.transactions:
            self.assertEqual(
                sorted(trans.keys()),
                ["body_html", "date_raw", "id", "idx"],
                f"bad keys for transaction {trans['id']}",
            )

    def test_one(self):
        trans = self.transactions[0]
        self.assertEqual(sorted(trans.keys()), ["body_html", "date_raw", "id", "idx"])
        self.assertEqual(trans["id"], "0@Sat, 26 Apr 2025 15:23:14 +0000")
        self.assertEqual(trans["idx"], 0)
        self.assertEqual(trans["date_raw"], "Sat, 26 Apr 2025 15:23:14 +0000")
