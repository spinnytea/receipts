import unittest

from app.parse.mail import parse_eml_file, parse_mbox_file


class TestParseEmail(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.transactions = parse_eml_file("data/test_data/test_simple.eml")

    def test_count(self):
        self.assertEqual(len(self.transactions), 1)

    def test_all_keys(self):
        for trans in self.transactions:
            self.assertEqual(
                sorted(trans.keys()),
                ["body_html", "date_raw", "filename", "id", "idx"],
                f"bad keys for transaction {trans['id']}",
            )

    def test_one(self):
        trans = self.transactions[0]
        self.assertEqual(
            sorted(trans.keys()), ["body_html", "date_raw", "filename", "id", "idx"]
        )
        self.assertEqual(
            trans["id"],
            "Wed, 08 Oct 2025 00:23:10 +0000 @ data/test_data/test_simple.eml",
        )
        self.assertEqual(trans["idx"], 0)
        self.assertEqual(trans["date_raw"], "Wed, 08 Oct 2025 00:23:10 +0000")


class TestParseMailbox(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.transactions = parse_mbox_file("data/test_data/test_simple.mbox")

    def test_count(self):
        self.assertEqual(len(self.transactions), 1)

    def test_all_keys(self):
        for trans in self.transactions:
            self.assertEqual(
                sorted(trans.keys()),
                ["body_html", "date_raw", "filename", "id", "idx"],
                f"bad keys for transaction {trans['id']}",
            )

    def test_one(self):
        trans = self.transactions[0]
        self.assertEqual(
            sorted(trans.keys()), ["body_html", "date_raw", "filename", "id", "idx"]
        )
        self.assertEqual(
            trans["id"],
            "Sat, 26 Apr 2025 15:23:14 +0000 @ data/test_data/test_simple.mbox",
        )
        self.assertEqual(trans["idx"], 0)
        self.assertEqual(trans["date_raw"], "Sat, 26 Apr 2025 15:23:14 +0000")
