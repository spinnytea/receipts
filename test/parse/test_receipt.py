import unittest
from decimal import Decimal

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
            sorted(trans["receipt_data"].keys()), ["items", "skipped", "store_number"]
        )

        self.assertEqual(trans["receipt_data"]["store_number"], 55)
        items = trans["receipt_data"]["items"].copy()
        items.reverse()
        self.assertEqual(len(items), 6)
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

        # we should have verified them all
        self.assertEqual(len(items), 0)

        # FIXME finish
        # print(f"{json.dumps(trans['receipt_data'].get('skipped'), indent=2)}")
        # self.assertEqual(trans["receipt_data"].get("skipped"), [])
