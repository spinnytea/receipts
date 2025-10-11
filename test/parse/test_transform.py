import json
import unittest
from decimal import Decimal

from app.parse.date import datetime_serializer
from app.parse.transform import (
    TransformFormat,
    _transform_receipt_parsed_to_list,
    _transform_receipt_parsed_to_table,
    transform_receipt_parsed,
)


class TestParseTransform(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        with open(
            "data/test_data/receipt_parsed_sample.json", "r", encoding="utf-8"
        ) as file:
            self.receipt_parsed_sample = json.loads(file.read())
            # XXX move to a generic "load this type of data" instead of just json.loads
            for trans in self.receipt_parsed_sample:
                for item in trans["receipt_data"]["items"]:
                    item["price"] = Decimal(item["price"])

    def test_loaded_sample(self):
        self.assertEqual(len(self.receipt_parsed_sample), 2)

        trans = self.receipt_parsed_sample[0]
        self.assertEqual(
            sorted(trans.keys()),
            ["date", "date_raw", "filename", "id", "idx", "receipt_data"],
            f"bad keys for transaction {trans['id']}",
        )
        self.assertEqual(trans["date"], "2025-06-16T22:54:31+00:00")
        item = trans["receipt_data"]["items"][0]
        self.assertEqual(
            sorted(item.keys()),
            ["adjustments", "category", "lines", "name", "price", "taxable"],
            f"bad keys for transaction {trans['id']} item #0",
        )
        self.assertEqual(item["name"], "PF WG 15 GRAIN")
        self.assertEqual(item["price"], Decimal("4.49"))
        self.assertEqual(item["category"], "BAKERY - COMMERCIAL")

    def test_one_list(self):
        trans = self.receipt_parsed_sample[0]
        results = _transform_receipt_parsed_to_list(trans)
        self.assertEqual(len(results), 4)
        self.assertEqual(
            results,
            [
                {
                    "date": "2025-06-16T22:54:31+00:00",
                    "category": "BAKERY - COMMERCIAL",
                    "price": Decimal("4.49"),
                },
                {
                    "date": "2025-06-16T22:54:31+00:00",
                    "category": "DAIRY",
                    "price": Decimal("5.19"),
                },
                {
                    "date": "2025-06-16T22:54:31+00:00",
                    "category": "DAIRY",
                    "price": Decimal("5.19"),
                },
                {
                    "date": "2025-06-16T22:54:31+00:00",
                    "category": "GROCERY",
                    "price": Decimal("13.99"),
                },
            ],
        )

    def test_one_table(self):
        trans = self.receipt_parsed_sample[0]
        result = _transform_receipt_parsed_to_table(trans)
        self.assertEqual(
            result,
            {
                "date": "2025-06-16T22:54:31+00:00",
                "Age Restricted: 18": Decimal("0"),
                "BAKE SHOP": Decimal("0"),
                "BAKERY - COMMERCIAL": Decimal("4.49"),
                "CHEESE SHOP": Decimal("0"),
                "CONVENIENCE ITEMS": Decimal("0"),
                "DAIRY": Decimal("10.38"),
                "DELI": Decimal("0"),
                "FROZEN FOOD": Decimal("0"),
                "GENERAL MERCHANDISE": Decimal("0"),
                "GROCERY": Decimal("13.99"),
                "HEALTH AND BEAUTY CARE": Decimal("0"),
                "MEAT": Decimal("0"),
                "PHARMACY": Decimal("0"),
                "PREPARED FOODS": Decimal("0"),
                "PRODUCE": Decimal("0"),
            },
            json.dumps(result, default=datetime_serializer, indent=2),
        )

    def test_all_list(self):
        results = transform_receipt_parsed(
            self.receipt_parsed_sample, format=TransformFormat.List
        )
        self.assertEqual(len(results), 35)
        self.assertEqual(
            results[0],
            {
                "date": "2025-06-16T22:54:31+00:00",
                "category": "BAKERY - COMMERCIAL",
                "price": Decimal("4.49"),
            },
        )
        self.assertEqual(
            results[3],
            {
                "date": "2025-06-16T22:54:31+00:00",
                "category": "GROCERY",
                "price": Decimal("13.99"),
            },
        )
        self.assertEqual(
            results[4],
            {
                "date": "2025-05-24T19:12:21+00:00",
                "category": "DAIRY",
                "price": Decimal("3.00"),
            },
        )
        self.assertEqual(
            results[34],
            {
                "date": "2025-05-24T19:12:21+00:00",
                "category": "PRODUCE",
                "price": Decimal("1.45"),
            },
        )

    def test_all_table(self):
        results = transform_receipt_parsed(
            self.receipt_parsed_sample, format=TransformFormat.Table
        )
        self.assertEqual(
            results,
            [
                {
                    "date": "2025-06-16T22:54:31+00:00",
                    "Age Restricted: 18": Decimal("0"),
                    "BAKE SHOP": Decimal("0"),
                    "BAKERY - COMMERCIAL": Decimal("4.49"),
                    "CHEESE SHOP": Decimal("0"),
                    "CONVENIENCE ITEMS": Decimal("0"),
                    "DAIRY": Decimal("10.38"),
                    "DELI": Decimal("0"),
                    "FROZEN FOOD": Decimal("0"),
                    "GENERAL MERCHANDISE": Decimal("0"),
                    "GROCERY": Decimal("13.99"),
                    "HEALTH AND BEAUTY CARE": Decimal("0"),
                    "MEAT": Decimal("0"),
                    "PHARMACY": Decimal("0"),
                    "PREPARED FOODS": Decimal("0"),
                    "PRODUCE": Decimal("0"),
                },
                {
                    "date": "2025-05-24T19:12:21+00:00",
                    "Age Restricted: 18": Decimal("0"),
                    "BAKE SHOP": Decimal("0"),
                    "BAKERY - COMMERCIAL": Decimal("0"),
                    "CHEESE SHOP": Decimal("0"),
                    "CONVENIENCE ITEMS": Decimal("0"),
                    "DAIRY": Decimal("22.75"),
                    "DELI": Decimal("0"),
                    "FROZEN FOOD": Decimal("0"),
                    "GENERAL MERCHANDISE": Decimal("7.73"),
                    "GROCERY": Decimal("20.55"),
                    "HEALTH AND BEAUTY CARE": Decimal("0"),
                    "MEAT": Decimal("16.99"),
                    "PHARMACY": Decimal("0"),
                    "PREPARED FOODS": Decimal("0"),
                    "PRODUCE": Decimal("42.92"),
                },
            ],
            json.dumps(results, default=datetime_serializer, indent=2),
        )
