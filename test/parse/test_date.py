import datetime
import json
import unittest

from app.parse.date import datetime_serializer, parse_date_raw
from app.parse.mail import parse_mbox_file


class TestParseReceipt(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        transactions = parse_mbox_file("raw/dumps/Purchase-Groceries.mbox")
        parse_date_raw(transactions)

        self.transactions = transactions
        self.one = transactions[39]

    def test_all_keys(self):
        for trans in self.transactions:
            self.assertEqual(
                sorted(trans.keys()),
                ["body_html", "date", "date_raw", "id", "idx"],
                f"bad keys for transaction {trans['id']}",
            )

    def test_one(self):
        trans = self.one
        self.assertEqual(
            sorted(trans.keys()), ["body_html", "date", "date_raw", "id", "idx"]
        )

        date = trans["date"]
        self.assertEqual(
            date,
            datetime.datetime(2025, 4, 26, 15, 23, 14, tzinfo=datetime.timezone.utc),
        )

        trans_cp = trans.copy()
        trans_cp.pop("body_html")
        self.assertEqual(
            json.dumps(trans_cp, default=datetime_serializer),
            '{"idx": 39, "date_raw": "Sat, 26 Apr 2025 15:23:14 +0000", "id": "39@Sat, 26 Apr 2025 15:23:14 +0000", "date": "2025-04-26T15:23:14+00:00"}',
        )
