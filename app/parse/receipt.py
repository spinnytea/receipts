import re
from decimal import Decimal
from typing import List

CATEGORY_LINE = re.compile(r"(DAIRY|GENERAL MERCHANDISE|GROCERY|MEAT|PRODUCE)\s+")

# Common receipt codes
#  T: Taxable item.
# -T: Taxable item sale (how much less it costs)
#  F: Food item. This often indicates a non-taxable item in states where groceries are not taxed. In some stores, it may also indicate that the item is eligible for food stamps (EBT).
# -F: Food item sale (how much less it costs)
# TF: Taxable Food. This combination is used for food items that are subject to sales tax, such as candy, sodas, and prepared foods.
# NF: Non-taxable Food.
#  E: Exempt from sales tax.
#  X: Taxable item, used by some retailers instead of "T".
#  N: Non-taxable item, used by some retailers instead of a code like "F" or "E".
TAXABLE_CODES = [" T", "-T", "TF", " X"]
ITEMIZED_LINE = re.compile(r"^W?T?\s+(.{16})\s*(\d+\.\d\d)( T|-T| F|-F)$")

WEIGHT_LINE = re.compile(r"^ (\d+\.\d\d lb @ \d+\.\d\d /lb)( = (\d+\.\d\d))?\s+$")


def parse_receipt_raw(transactions):
    for trans in transactions:
        if "receipt_raw" in trans:
            _parse_receipt_raw(trans)


def _parse_receipt_raw(trans):
    parser = ReceiptParser()
    parser.feed(trans.pop("receipt_raw"))
    receipt_data = parser.data

    if parser.warning:
        trans.setdefault("warning", []).extend(parser.warning)
    if "store_number" not in receipt_data:
        trans.setdefault("warning", []).append(
            "Missing store number (never started parsing)"
        )
    if parser.parsing_groceries:
        trans.setdefault("warning", []).append("Never finished parsing groceries")
    if receipt_data.get("skipped"):
        trans.setdefault("warning", []).append(
            "Some of the receipt lines have not been accouned for (skipped)"
        )

    trans["receipt_data"] = receipt_data


class ReceiptParser:
    def __init__(self):
        self.data = {"items": []}

    def feed(self, receipt_raw: List[str]):
        self.warning = []
        self.current_category = None
        self.parsing_groceries = False
        self.current_item = None
        self.skip_rest = False
        self.current_weight = None

        for line in receipt_raw:
            if line.isspace():
                # skip lines that are all spaces
                continue

            if "store_number" not in self.data:
                # throw out all the lines before the store number
                # (the next line starts the produce)
                x = re.match("^Store #(\d+)", line)
                if x:
                    self.data["store_number"] = int(x.group(1))
                    self.parsing_groceries = True
                continue

            if set(line) == {"*"}:
                # if line all stars, then we are done
                self.parsing_groceries = False

            if not self.parsing_groceries:
                # TODO do not skip everything else?
                continue

            if self.skip_rest:
                # if we hit a snag, just skip the rest (easier to recover/debug state)
                self.data.setdefault("skipped", []).append(line)
                continue

            if not line.startswith(" ") and not line.startswith("WT "):
                match_category = CATEGORY_LINE.match(line)
                if match_category:
                    self.current_category = match_category.group(1)
                    continue
                self.current_category = None
            elif not self.current_category:
                self.warning.append(
                    f"receipt should have a category by this point -- {line}"
                )
            else:
                match_itemized = ITEMIZED_LINE.match(line)
                if match_itemized:
                    [name, cost, code] = match_itemized.groups()
                    self.current_item = {
                        "name": name.strip(),
                        "price": Decimal(0),
                        "category": self.current_category,
                        "taxable": code in TAXABLE_CODES,
                        "adjustments": [],
                    }
                    self._add_adjustment([name, cost, code])
                    self.data["items"].append(self.current_item)

                    if self.current_weight and line.startswith("WT"):
                        self._add_weight_readout(shouldHaveCost=False)

                    continue

                match_savings = re.match(
                    r"\s+(BONUS BUY SAVINGS)\s+(\d+\.\d\d)(-T|-F)", line
                )
                if match_savings:
                    # FIXME use weight readout
                    self._add_adjustment(match_savings.groups())
                    continue

                match_verify = re.match(r"\s+(PRICE YOU PAY)\s+(\d+\.\d\d)\s+", line)
                if match_verify:
                    [text, cost] = match_verify.groups()
                    price = Decimal(cost)
                    self.current_item["adjustments"].append(
                        {
                            "name": text,
                            "price": Decimal(cost),
                            "type": "verify",
                        }
                    )

                    if self.current_weight:
                        self._add_weight_readout(shouldHaveCost=True)

                    if price == self.current_item["price"]:
                        self.current_item = None
                        continue
                    else:
                        self.skip_rest = True
                        self.warning.append(
                            f"invalid price? {line} -- {self.current_item}"
                        )

                match_weight = WEIGHT_LINE.match(line)
                if match_weight:
                    self.current_weight = match_weight.groups()
                    continue

            # FIXME finish other lines

            self.data.setdefault("skipped", []).append(line)
            self.skip_rest = True

        self.current_item = None

    def _add_adjustment(self, match):
        if self.current_item is None:
            self.warning.append("not currently parsing anything")
        if not match or len(match) != 3:
            self.warning.append("invalid match argument")

        [name, cost, code] = match
        taxable = code in TAXABLE_CODES
        scale = -1 if code[0] == "-" else 1

        if taxable != self.current_item["taxable"]:
            self.warning.append(f"mismatch taxable: {match} -- {self.current_item}")

        self.current_item["price"] += Decimal(cost) * scale
        self.current_item["adjustments"].append(
            {
                "name": name.strip(),
                "amount": Decimal(cost),
                "code": code,
                "type": "sum",
            }
        )

    def _add_weight_readout(self, shouldHaveCost=False):
        [weight_readout, _, cost] = self.current_weight
        self.current_weight = None
        last_adjustment = self.current_item["adjustments"][-1]
        last_adjustment["weight_readout"] = weight_readout
        if shouldHaveCost:
            if cost:
                price = Decimal(cost)
                last_adjustment["weight_price"] = price
                if last_adjustment["price"] != price:
                    self.warning.push(
                        f"verify price does not match weight cost: {weight_readout}, {cost} -- {self.current_item}"
                    )
                if last_adjustment["price"] != price:
                    self.warning.push(
                        f"verify price ({last_adjustment['name']}) does not match weight cost: {weight_readout}, {cost} -- {self.current_item}"
                    )
                if self.current_item["price"] != price:
                    self.warning.push(
                        f"item price ({self.current_item['name']}) does not match weight cost: {weight_readout}, {cost} -- {self.current_item}"
                    )
            else:
                self.warning.push(
                    f"should be verifying price, but has none? {weight_readout}, {cost} -- {self.current_item}"
                )
        else:  # not shouldHaveCost:
            if cost:
                self.warning.push(
                    f"verify weight price on original item? {weight_readout}, {cost} -- {self.current_item}"
                )
            else:
                # valid
                pass

        # XXX not sure if it should be a separate adjustment?
        # self.current_item["adjustments"].append(
        #     {
        #         "readout": weight_readout,
        #         "type": "weight_readout",
        #     }
        # )
