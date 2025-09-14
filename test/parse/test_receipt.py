import json
import unittest
from decimal import Decimal

from app.parse.date import datetime_serializer
from app.parse.html import parse_body_html
from app.parse.mail import parse_mbox_file
from app.parse.receipt import ReceiptParser, _parse_receipt_raw, parse_receipt_raw


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

    def test_item_simple(self):
        parser = ReceiptParser()
        parser.feed(
            [
                "Store #00                             ",
                "DAIRY                                 ",
                "        BLACKCHRY 0% 4PK        5.99 F",
            ]
        )
        items = parser.data["items"]
        self.assertEqual(len(items), 1)
        item = items[0]
        self.assertEqual(
            item,
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
                        "type": "sum",
                    },
                ],
                "lines": ["        BLACKCHRY 0% 4PK        5.99 F"],
            },
            json.dumps(item, default=datetime_serializer, indent=2),
        )

    def test_item_savings(self):
        parser = ReceiptParser()
        parser.feed(
            [
                "Store #00                             ",
                "DAIRY                                 ",
                "        PHIL CRM CHEES8Z        3.99 F",
                "        BONUS BUY SAVINGS       0.99-F",
                "   PRICE YOU PAY           3.00       ",
            ]
        )
        items = parser.data["items"]
        self.assertEqual(len(items), 1)
        item = items[0]
        self.assertEqual(
            item,
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
                        "type": "sum",
                    },
                    {
                        "name": "BONUS BUY SAVINGS",
                        "amount": Decimal("0.99"),
                        "code": "-F",
                        "type": "sum",
                    },
                    {
                        "name": "PRICE YOU PAY",
                        "price": Decimal("3.00"),
                        "type": "verify",
                    },
                ],
                "lines": [
                    "        PHIL CRM CHEES8Z        3.99 F",
                    "        BONUS BUY SAVINGS       0.99-F",
                    "   PRICE YOU PAY           3.00       ",
                ],
            },
            json.dumps(item, default=datetime_serializer, indent=2),
        )

    def test_item_bogo(self):
        parser = ReceiptParser()
        parser.feed(
            [
                "Store #00                             ",
                "BAKERY - COMMERCIAL                   ",
                "        THMS EM ORIG 13Z        5.29 F",
                "        BONUS BUY SAVINGS       5.29-F",
                "   PRICE YOU PAY           FREE       ",
                "        THOM EMFN 6CT12Z        5.29 F",
            ]
        )
        items = parser.data["items"]
        self.assertEqual(len(items), 2)
        item = items[0]
        self.assertEqual(
            item,
            {
                "name": "THMS EM ORIG 13Z",
                "price": Decimal("0.00"),
                "category": "BAKERY - COMMERCIAL",
                "taxable": False,
                "adjustments": [
                    {
                        "name": "THMS EM ORIG 13Z",
                        "amount": Decimal("5.29"),
                        "code": " F",
                        "type": "sum",
                    },
                    {
                        "name": "BONUS BUY SAVINGS",
                        "amount": Decimal("5.29"),
                        "code": "-F",
                        "type": "sum",
                    },
                    {
                        "name": "PRICE YOU PAY",
                        "price": Decimal("0.00"),
                        "type": "verify",
                    },
                ],
                "lines": [
                    "        THMS EM ORIG 13Z        5.29 F",
                    "        BONUS BUY SAVINGS       5.29-F",
                    "   PRICE YOU PAY           FREE       ",
                ],
            },
            json.dumps(item, default=datetime_serializer, indent=2),
        )
        item = items[1]
        self.assertEqual(
            item,
            {
                "name": "THOM EMFN 6CT12Z",
                "price": Decimal("5.29"),
                "category": "BAKERY - COMMERCIAL",
                "taxable": False,
                "adjustments": [
                    {
                        "name": "THOM EMFN 6CT12Z",
                        "amount": Decimal("5.29"),
                        "code": " F",
                        "type": "sum",
                    },
                ],
                "lines": [
                    "        THOM EMFN 6CT12Z        5.29 F",
                ],
            },
            json.dumps(item, default=datetime_serializer, indent=2),
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

        def simplify_one_item(item):
            del item["category"]
            del item["taxable"]
            del item["adjustments"]
            del item["lines"]
            return item

        def simplify_matching_items(items, category):
            for item in items:
                if category == item["category"]:
                    simplify_one_item(item)

        self.assertEqual(sorted(trans.keys()), ["id", "receipt_data"])
        self.assertEqual(
            sorted(trans["receipt_data"].keys()),
            ["balance", "items", "store_number", "tax"],
        )

        self.assertEqual(trans["receipt_data"]["store_number"], 55)
        self.assertEqual(trans["receipt_data"]["tax"], Decimal("0.47"))
        self.assertEqual(trans["receipt_data"]["balance"], Decimal("111.41"))
        items = trans["receipt_data"]["items"].copy()
        items.reverse()
        self.assertEqual(len(items), 31)
        # DAIRY
        item = items.pop()
        self.assertEqual(
            item,
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
                        "type": "sum",
                    },
                    {
                        "name": "BONUS BUY SAVINGS",
                        "amount": Decimal("0.99"),
                        "code": "-F",
                        "type": "sum",
                    },
                    {
                        "name": "PRICE YOU PAY",
                        "price": Decimal("3.00"),
                        "type": "verify",
                    },
                ],
                "lines": [
                    "        PHIL CRM CHEES8Z        3.99 F",
                    "        BONUS BUY SAVINGS       0.99-F",
                    "   PRICE YOU PAY           3.00       ",
                ],
            },
            json.dumps(item, default=datetime_serializer, indent=2),
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
                        "type": "sum",
                    },
                ],
                "lines": ["        BLACKCHRY 0% 4PK        5.99 F"],
            },
        )
        simplify_matching_items(items, "DAIRY")
        self.assertEqual(
            items.pop(),
            {
                "name": "PLRS ORG CVN16Z",
                "price": Decimal("4.99"),
            },
        )
        self.assertEqual(
            items.pop(),
            {
                "name": "SIGGI STRW 5.3Z",
                "price": Decimal("2.19"),
            },
        )
        self.assertEqual(
            items.pop(),
            {
                "name": "YPL OUI DF VNL5Z",
                "price": Decimal("2.39"),
            },
        )
        self.assertEqual(
            items.pop(),
            {
                "name": "SB EGGS LRG",
                "price": Decimal("4.19"),
            },
        )
        # GENERAL MERCHANDISE
        item = items.pop()
        self.assertEqual(
            item,
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
                        "type": "sum",
                    },
                    {
                        "name": "BONUS BUY SAVINGS",
                        "amount": Decimal("0.86"),
                        "code": "-T",
                        "type": "sum",
                    },
                    {
                        "name": "PRICE YOU PAY",
                        "price": Decimal("7.73"),
                        "type": "verify",
                    },
                ],
                "lines": [
                    "        SL GARLIC PRESS         8.59 T",
                    "        BONUS BUY SAVINGS       0.86-T",
                    "   PRICE YOU PAY           7.73       ",
                ],
            },
            json.dumps(item, default=datetime_serializer, indent=2),
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
                        "type": "sum",
                    },
                ],
                "lines": ["        SB CDER VINEGAR         1.99 F"],
            },
        )
        simplify_matching_items(items, "GROCERY")
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
        item = items.pop()
        self.assertEqual(
            item,
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
                        "type": "sum",
                    },
                    {
                        "name": "BONUS BUY SAVINGS",
                        "amount": Decimal("1.99"),
                        "code": "-F",
                        "type": "sum",
                    },
                    {
                        "name": "PRICE YOU PAY",
                        "price": Decimal("2.50"),
                        "type": "verify",
                    },
                ],
                "lines": [
                    "        BP HD MT FRANKS         4.49 F",
                    "        BONUS BUY SAVINGS       1.99-F",
                    "   PRICE YOU PAY           2.50       ",
                ],
            },
            json.dumps(item, default=datetime_serializer, indent=2),
        )
        simplify_matching_items(items, "MEAT")
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
        # PRODUCE
        self.assertEqual(
            items.pop(),
            {
                "name": "CARROTS 2LB",
                "price": Decimal("1.99"),
                "category": "PRODUCE",
                "taxable": False,
                "adjustments": [
                    {
                        "name": "CARROTS 2LB",
                        "amount": Decimal("1.99"),
                        "code": " F",
                        "type": "sum",
                    },
                ],
                "lines": ["        CARROTS 2LB             1.99 F"],
            },
        )
        self.assertEqual(
            simplify_one_item(items.pop()),
            {
                "name": "LTLPT BMR GLD",
                "price": Decimal("3.99"),
            },
        )
        self.assertEqual(
            simplify_one_item(items.pop()),
            {
                "name": "SW GARLIC 9.5Z",
                "price": Decimal("3.99"),
            },
        )
        self.assertEqual(
            simplify_one_item(items.pop()),
            {
                "name": "SW SQ GINGER 10Z",
                "price": Decimal("4.49"),
            },
        )
        self.assertEqual(
            simplify_one_item(items.pop()),
            {
                "name": "AUR GRANOLA 13Z",
                "price": Decimal("5.99"),
            },
        )
        item = items.pop()
        self.assertEqual(
            item,
            {
                "name": "1LB STRAWBERRY",
                "price": Decimal("3.79"),
                "category": "PRODUCE",
                "taxable": False,
                "adjustments": [
                    {
                        "name": "1LB STRAWBERRY",
                        "amount": Decimal("4.99"),
                        "code": " F",
                        "type": "sum",
                    },
                    {
                        "name": "BONUS BUY SAVINGS",
                        "amount": Decimal("1.20"),
                        "code": "-F",
                        "type": "sum",
                    },
                    {
                        "name": "PRICE YOU PAY",
                        "price": Decimal("3.79"),
                        "type": "verify",
                    },
                ],
                "lines": [
                    "        1LB STRAWBERRY          4.99 F",
                    "        BONUS BUY SAVINGS       1.20-F",
                    "   PRICE YOU PAY           3.79       ",
                ],
            },
            json.dumps(item, default=datetime_serializer, indent=2),
        )
        self.assertEqual(
            items.pop(),
            {
                "name": "RED SEEDLESS GRA",
                "price": Decimal("6.10"),
                "category": "PRODUCE",
                "taxable": False,
                "adjustments": [
                    {
                        "name": "RED SEEDLESS GRA",
                        "amount": Decimal("6.10"),
                        "code": " F",
                        "type": "sum",
                        "weight_readout": "1.53 lb @ 3.99 /lb",
                    },
                ],
                "lines": [
                    " 1.53 lb @ 3.99 /lb                   ",
                    "WT      RED SEEDLESS GRA        6.10 F",
                ],
            },
        )
        item = items.pop()
        self.assertEqual(
            item,
            {
                "name": "ASPARAGUS",
                "price": Decimal("3.35"),
                "category": "PRODUCE",
                "taxable": False,
                "adjustments": [
                    {
                        "name": "ASPARAGUS",
                        "amount": Decimal("4.24"),
                        "code": " F",
                        "type": "sum",
                        "weight_readout": "1.12 lb @ 3.79 /lb",
                    },
                    {
                        "name": "BONUS BUY SAVINGS",
                        "amount": Decimal("0.89"),
                        "code": "-F",
                        "type": "sum",
                    },
                    {
                        "name": "PRICE YOU PAY",
                        "price": Decimal("3.35"),
                        "type": "verify",
                        "weight_readout": "1.12 lb @ 2.99 /lb",
                        "weight_price": Decimal("3.35"),
                    },
                ],
                "lines": [
                    " 1.12 lb @ 3.79 /lb                   ",
                    "WT      ASPARAGUS               4.24 F",
                    " 1.12 lb @ 2.99 /lb = 3.35            ",
                    "        BONUS BUY SAVINGS       0.89-F",
                    "   PRICE YOU PAY           3.35       ",
                ],
            },
            json.dumps(item, default=datetime_serializer, indent=2),
        )
        item = items.pop()
        self.assertEqual(
            item,
            {
                "name": "+LEMONS",
                "price": Decimal("0.67"),
                "category": "PRODUCE",
                "taxable": False,
                "adjustments": [
                    {
                        "name": "+LEMONS",
                        "amount": Decimal("0.67"),
                        "code": " F",
                        "type": "sum",
                    },
                ],
                "lines": [
                    "        +LEMONS                 0.67 F",
                ],
            },
            json.dumps(item, default=datetime_serializer, indent=2),
        )
        item = items.pop()
        self.assertEqual(
            item,
            {
                "name": "KIWI",
                "price": Decimal("2.00"),
                "category": "PRODUCE",
                "taxable": False,
                "adjustments": [
                    {
                        "name": "KIWI",
                        "amount": Decimal("3.16"),
                        "code": " F",
                        "type": "sum",
                        "quantity_readout": "4 @ 0.79",
                    },
                    {
                        "name": "BONUS BUY SAVINGS",
                        "amount": Decimal("1.16"),
                        "code": "-F",
                        "type": "sum",
                        "quantity_readout": "4 @ 0.29",
                    },
                    {
                        "name": "PRICE YOU PAY FOR",
                        "price": Decimal("2.00"),
                        "quantity": 4,
                        "type": "verify",
                    },
                ],
                "lines": [
                    " 4 @ 0.79                             ",
                    "        KIWI                    3.16 F",
                    " 4 @ 0.29                             ",
                    "        BONUS BUY SAVINGS       1.16-F",
                    "   PRICE YOU PAY FOR   4   2.00       ",
                ],
            },
            json.dumps(item, default=datetime_serializer, indent=2),
        )
        item = items.pop()
        self.assertEqual(
            item,
            {
                "name": "SUMMER SQUASH",
                "price": Decimal("1.41"),
                "category": "PRODUCE",
                "taxable": False,
                "adjustments": [
                    {
                        "name": "SUMMER SQUASH",
                        "amount": Decimal("1.77"),
                        "code": " F",
                        "type": "sum",
                        "weight_readout": "0.71 lb @ 2.49 /lb",
                    },
                    {
                        "name": "BONUS BUY SAVINGS",
                        "amount": Decimal("0.36"),
                        "code": "-F",
                        "type": "sum",
                    },
                    {
                        "name": "PRICE YOU PAY",
                        "price": Decimal("1.41"),
                        "type": "verify",
                        "weight_readout": "0.71 lb @ 1.99 /lb",
                        "weight_price": Decimal("1.41"),
                    },
                ],
                "lines": [
                    " 0.71 lb @ 2.49 /lb                   ",
                    "WT      SUMMER SQUASH           1.77 F",
                    " 0.71 lb @ 1.99 /lb = 1.41            ",
                    "        BONUS BUY SAVINGS       0.36-F",
                    "   PRICE YOU PAY           1.41       ",
                ],
            },
            json.dumps(item, default=datetime_serializer, indent=2),
        )
        self.assertEqual(
            simplify_one_item(items.pop()),
            {
                "name": "GARLIC",
                "price": Decimal("0.69"),
            },
        )
        self.assertEqual(
            simplify_one_item(items.pop()),
            {
                "name": "LOOSE SHALLOTS",
                "price": Decimal("0.52"),
            },
        )
        self.assertEqual(
            simplify_one_item(items.pop()),
            {
                "name": "IMPRTD RED PPPRS",
                "price": Decimal("1.00"),
            },
        )
        self.assertEqual(
            simplify_one_item(items.pop()),
            {
                "name": "BROCCOLI CROWNS",
                "price": Decimal("1.49"),
            },
        )
        self.assertEqual(
            simplify_one_item(items.pop()),
            {
                "name": "FRESH BANANAS",
                "price": Decimal("1.45"),
            },
        )

        # we should have verified them all
        self.assertEqual(len(items), 0)

        if trans.get("warning", []) and "(skipped)" in ".".join(trans.get("warning")):
            print(f"{json.dumps(trans['receipt_data'].get('skipped'), indent=2)}")
        self.assertEqual(trans.get("warning", []), [])
        self.assertEqual(trans["receipt_data"].get("skipped", []), [])
