import datetime
import json
import unittest
from decimal import Decimal

import dateutil.parser

from app.parse.date import datetime_serializer
from app.process.stats import stats_graph_agg, stats_sum_receipt_parsed


class TestSumTransactions(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        with open(
            "data/test_data/receipt_parsed_sample.json", "r", encoding="utf-8"
        ) as file:
            self.receipt_parsed_sample = json.loads(file.read())
            # XXX move to a generic "load this type of data" instead of just json.loads
            for trans in self.receipt_parsed_sample:
                trans["date"] = dateutil.parser.isoparse(trans["date"])
                for item in trans["receipt_data"]["items"]:
                    item["price"] = Decimal(item["price"])
        self.agg = {
            "date_min": datetime.datetime(
                2025, 5, 24, 19, 12, 21, tzinfo=datetime.timezone.utc
            ),
            "date_max": datetime.datetime(
                2025, 6, 16, 22, 54, 31, tzinfo=datetime.timezone.utc
            ),
            "cats": {
                "Age Restricted: 18": Decimal("0"),
                "BAKE SHOP": Decimal("0"),
                "BAKERY - COMMERCIAL": Decimal("4.49"),
                "CHEESE SHOP": Decimal("0"),
                "CONVENIENCE ITEMS": Decimal("0"),
                "DAIRY": Decimal("33.13"),
                "DELI": Decimal("0"),
                "FROZEN FOOD": Decimal("0"),
                "GENERAL MERCHANDISE": Decimal("7.73"),
                "GROCERY": Decimal("34.54"),
                "HEALTH AND BEAUTY CARE": Decimal("0"),
                "MEAT": Decimal("16.99"),
                "PHARMACY": Decimal("0"),
                "PREPARED FOODS": Decimal("0"),
                "PRODUCE": Decimal("42.92"),
            },
        }

    def test_loaded_sample(self):
        self.assertEqual(len(self.receipt_parsed_sample), 2)

        trans = self.receipt_parsed_sample[0]
        self.assertEqual(
            sorted(trans.keys()),
            ["date", "date_raw", "id", "idx", "receipt_data"],
            f"bad keys for transaction {trans['id']}",
        )
        self.assertEqual(
            trans["date"],
            datetime.datetime(2025, 6, 16, 22, 54, 31, tzinfo=datetime.timezone.utc),
        )
        item = trans["receipt_data"]["items"][0]
        self.assertEqual(
            sorted(item.keys()),
            ["adjustments", "category", "lines", "name", "price", "taxable"],
            f"bad keys for transaction {trans['id']} item #0",
        )
        self.assertEqual(item["name"], "PF WG 15 GRAIN")
        self.assertEqual(item["price"], Decimal("4.49"))
        self.assertEqual(item["category"], "BAKERY - COMMERCIAL")

    def test_sum_cats_all(self):
        agg = stats_sum_receipt_parsed(self.receipt_parsed_sample)
        self.assertIsInstance(agg["date_min"], datetime.datetime)
        self.assertIsInstance(agg["date_max"], datetime.datetime)
        self.assertEqual(
            agg,
            self.agg,
            json.dumps(agg, default=datetime_serializer, indent=2),
        )

    @unittest.skip("not implemented yet")
    def test_sum_cats_with_date_range(self):
        pass

    def test_graph_it(self):
        self.assertEqual(
            stats_graph_agg(self.agg),
            """
    ■■■   4.49 · BAKERY - COMMERCIAL
 ■■■■■■  33.13 · DAIRY
    ■■■   7.73 · GENERAL MERCHANDISE
 ■■■■■■  34.54 · GROCERY
  ■■■■■  16.99 · MEAT
 ■■■■■■  42.92 · PRODUCE
""",
        )
