import unittest
from decimal import Decimal

from app.parse.html import parse_body_html
from app.parse.mail import parse_mbox_file
from app.parse.receipt import _parse_receipt_raw, parse_receipt_raw


class TestParseReceipt(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.transactions = parse_mbox_file("raw/dumps/Purchase-Groceries.mbox")
        parse_body_html(self.transactions)
        parse_receipt_raw(self.transactions)

        with open("raw/receipt_raw_sample.txt", "r", encoding="utf-8") as file:
            self.receipt_raw_sample = file.read()
        self.receipt_raw_sample = [
            line.strip('"') for line in self.receipt_raw_sample.splitlines()
        ]

    def test_all_keys(self):
        for trans in self.transactions:
            keys = sorted(trans.keys())
            if "warning" in keys:
                keys.remove("warning")
            self.assertEqual(
                keys,
                ["date_raw", "id", "idx", "receipt_data"],
                f"bad keys for transaction {trans['id']}",
            )

    def test_loaded_sample(self):
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
            sorted(trans["receipt_data"].keys()), ["items", "skipped", "store_number"]
        )

        self.assertEqual(trans["receipt_data"]["store_number"], 55)
        items = trans["receipt_data"]["items"].copy()
        items.reverse()
        self.assertEqual(len(items), 15)
        # DAIRY
        self.assertEqual(
            items.pop(),
            {
                "name": "PHIL CRM CHEES8Z",
                "price": Decimal("3.00"),
                "category": "DAIRY",
                "taxable": False,
                "adjustments": [
                    {
                        "name": "PHIL CRM CHEES8Z",
                        "amount": Decimal("3.99"),
                        "code": " F",
                    },
                    {
                        "name": "BONUS BUY SAVINGS",
                        "amount": Decimal("0.99"),
                        "code": "-F",
                    },
                ],
            },
        )
        self.assertEqual(
            items.pop(),
            {
                "name": "BLACKCHRY 0% 4PK",
                "price": Decimal("5.99"),
                "category": "DAIRY",
                "taxable": False,
                "adjustments": [
                    {
                        "name": "BLACKCHRY 0% 4PK",
                        "amount": Decimal("5.99"),
                        "code": " F",
                    },
                ],
            },
        )
        for item in items:
            if "DAIRY" == item["category"]:
                del item["adjustments"]
        self.assertEqual(
            items.pop(),
            {
                "name": "PLRS ORG CVN16Z",
                "price": Decimal("4.99"),
                "category": "DAIRY",
                "taxable": False,
            },
        )
        self.assertEqual(
            items.pop(),
            {
                "name": "SIGGI STRW 5.3Z",
                "price": Decimal("2.19"),
                "category": "DAIRY",
                "taxable": False,
            },
        )
        self.assertEqual(
            items.pop(),
            {
                "name": "YPL OUI DF VNL5Z",
                "price": Decimal("2.39"),
                "category": "DAIRY",
                "taxable": False,
            },
        )
        self.assertEqual(
            items.pop(),
            {
                "name": "SB EGGS LRG",
                "price": Decimal("4.19"),
                "category": "DAIRY",
                "taxable": False,
            },
        )
        # GENERAL MERCHANDISE
        self.assertEqual(
            items.pop(),
            {
                "name": "SL GARLIC PRESS",
                "price": Decimal("7.73"),
                "category": "GENERAL MERCHANDISE",
                "taxable": True,
                "adjustments": [
                    {
                        "name": "SL GARLIC PRESS",
                        "amount": Decimal("8.59"),
                        "code": " T",
                    },
                    {
                        "name": "BONUS BUY SAVINGS",
                        "amount": Decimal("0.86"),
                        "code": "-T",
                    },
                ],
            },
        )
        # GROCERY
        self.assertEqual(
            items.pop(),
            {
                "name": "SB CDER VINEGAR",
                "price": Decimal("1.99"),
                "category": "GROCERY",
                "taxable": False,
                "adjustments": [
                    {
                        "name": "SB CDER VINEGAR",
                        "amount": Decimal("1.99"),
                        "code": " F",
                    },
                ],
            },
        )
        for item in items:
            if "GROCERY" == item["category"]:
                del item["category"]
                del item["taxable"]
                del item["adjustments"]
        self.assertEqual(
            items.pop(),
            {
                "name": "BRLLCKPEAPN8.8Z",
                "price": Decimal("3.59"),
            },
        )
        self.assertEqual(
            items.pop(),
            {
                "name": "SB MARSH CRM 7Z",
                "price": Decimal("1.59"),
            },
        )
        self.assertEqual(
            items.pop(),
            {
                "name": "BONE NAM STW PRE",
                "price": Decimal("6.99"),
            },
        )
        self.assertEqual(
            items.pop(),
            {
                "name": "SB WALNUTS H&P",
                "price": Decimal("6.39"),
            },
        )
        # MEAT
        self.assertEqual(
            items.pop(),
            {
                "name": "BP HD MT FRANKS",
                "price": Decimal("2.50"),
                "category": "MEAT",
                "taxable": False,
                "adjustments": [
                    {
                        "name": "BP HD MT FRANKS",
                        "amount": Decimal("4.49"),
                        "code": " F",
                    },
                    {
                        "name": "BONUS BUY SAVINGS",
                        "amount": Decimal("1.99"),
                        "code": "-F",
                    },
                ],
            },
        )
        for item in items:
            if "MEAT" == item["category"]:
                del item["category"]
                del item["taxable"]
                del item["adjustments"]
        self.assertEqual(
            items.pop(),
            {
                "name": "BP HD MT FRANKS",
                "price": Decimal("2.50"),
            },
        )
        self.assertEqual(
            items.pop(),
            {
                "name": "PRE BEEF RE STK",
                "price": Decimal("11.99"),
            },
        )

        # we should have verified them all
        self.assertEqual(len(items), 0)

        # FIXME finish
        # self.assertEqual(trans["warning"], [])
        # import json
        # print(f"{json.dumps(trans['receipt_data'].get('skipped'), indent=2)}")
        # self.assertEqual(trans["receipt_data"].get("skipped"), [])
