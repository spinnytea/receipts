import re
from decimal import ROUND_UP, Decimal
from typing import List

# XXX should categories be automatic?
CATEGORIES = [
    "Age Restricted: \d+",
    "BAKE SHOP",
    "BAKERY - COMMERCIAL",
    "CHEESE SHOP",
    "CONVENIENCE ITEMS",
    "DAIRY",
    "DELI",
    "FROZEN FOOD",
    "GENERAL MERCHANDISE",
    "GROCERY",
    "HEALTH AND BEAUTY CARE",
    "MEAT",
    "PHARMACY",
    "PREPARED FOODS",
    "PRODUCE",
]
CATEGORY_LINE = re.compile(r"(" + "|".join(CATEGORIES) + r")\s+")

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
#  Q: Qualified health care item for HSA (healthcare spending account) (triple tax-free)
#  B: (various) SNAP-eligible and taxed
TAXABLE_CODES = [" T", "-T", "TF", " X", "-X", " B", "-B"]
TAX_CODE_GROUP = r"( T|-T| F|-F| X| Q|- |  | B|-B)"
ITEMIZED_LINE = re.compile(
    r"^(WT|MR|  )\s{6}(.{20})\s+(\d+\.\d\d)" + TAX_CODE_GROUP + r"$"
)
CREDIT_LINE = re.compile(r"^(SC)\s{6}(.{20})\s*(\d+\.\d\d)( F|-F)")

WEIGHT_LINE = re.compile(r"^ (\d*\.\d+ lb @ \d+\.\d\d /lb)( = (\d+\.\d\d))?\s+$")
QUANTITY_LINE = re.compile(r"^ (\d+ @ \d+\.\d\d)\s+$")

SKIP_TAX_CHECK = False


# XXX never ever ever hard code the tax rate, set it as an env var or something
def APPLY_TAX_RATE(amount):
    return (amount * Decimal("0.06")).quantize(Decimal("0.01"), rounding=ROUND_UP)


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

    if not parser.skip_rest:
        if "tax" in receipt_data and receipt_data["tax"] > Decimal("0"):
            sum = Decimal(0)
            for item in receipt_data["items"]:
                if item.get("taxable", False):
                    sum += item["price"]
            if not sum or sum == Decimal(0):
                trans.setdefault("warning", []).append("tax but no taxable items?")
            if not SKIP_TAX_CHECK and receipt_data["tax"] != APPLY_TAX_RATE(sum):
                trans.setdefault("warning", []).append(
                    f"what is this tax amount? (tax) {receipt_data['tax']} != (sum) {sum} * (rate) {Decimal('0.06')} == (calc) {APPLY_TAX_RATE(sum)}"
                )

        if "balance" in receipt_data:
            sum = Decimal(0)
            for item in receipt_data["items"]:
                sum += item["price"]
            if "tax" in receipt_data:
                sum += receipt_data["tax"]
            if sum != receipt_data["balance"]:
                trans.setdefault("warning", []).append(
                    f"balance mismatch? (listed) {receipt_data['balance']} != (sum) {sum}"
                )
        else:
            trans.setdefault("warning", []).append("receipt has no balance")

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
        self.current_quantity = None

        for line in receipt_raw:
            if line.isspace():
                # skip lines that are all spaces
                continue

            if "store_number" not in self.data:
                # throw out all the lines before the store number
                # (the next line starts the produce)
                # TODO parse date on reciept (store day time, day time 111 222 33 000000)
                x = re.match("^Store #(\d+)", line)
                if x:
                    self.data["store_number"] = int(x.group(1))
                    self.parsing_groceries = True
                continue

            if set(line) == {"*"}:
                # if line all stars, then we are done
                self.current_item = None
                self.current_category = None
                self.parsing_groceries = False

            match_tax = re.match(r"^\s+TAX\s+(\d+\.\d\d)  $", line)
            if match_tax:
                self.current_item = None
                self.current_category = None
                self.parsing_groceries = False
                [tax] = match_tax.groups()
                if "tax" in self.data:
                    self.warning.append(
                        f"duplicate tax? old: {self.data['tax']}, new: {tax}"
                    )
                self.data["tax"] = Decimal(tax)
                continue

            match_balance = re.match(r"^\s+\**\s+BALANCE\s+(\d+\.\d\d)  $", line)
            if match_balance:
                self.current_item = None
                self.current_category = None
                self.parsing_groceries = False
                [balance] = match_balance.groups()
                if "balance" in self.data:
                    self.warning.append(
                        f"duplicate balance? old: {self.data['balance']}, new: {balance}"
                    )
                self.data["balance"] = Decimal(balance)
                continue

            if not self.parsing_groceries:
                # skip everything else
                continue

            if self.skip_rest:
                # if we hit a snag, just skip the rest (easier to recover/debug state)
                self.data.setdefault("skipped", []).append(line)
                continue

            if (
                not line.startswith(" ")
                and not line.startswith("WT ")
                and not line.startswith("MR ")
                and not line.startswith("SC ")
            ):
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
                match_savings = re.match(
                    r"\s+((BONUS BUY )?SAVINGS)\s+(\d+\.\d\d)" + TAX_CODE_GROUP + r"$",
                    line,
                )
                if match_savings:
                    [name, _, cost, code] = match_savings.groups()
                    self._add_adjustment([name, cost, code], line)

                    if self.current_quantity:
                        self._add_quantity_readout()

                    continue

                match_itemized = ITEMIZED_LINE.match(line)
                if match_itemized:
                    [wt, name, cost, code] = match_itemized.groups()
                    self.current_item = {
                        "name": name.strip(),
                        "price": Decimal(0),
                        "category": self.current_category,
                        "taxable": code in TAXABLE_CODES,
                        "adjustments": [],
                        "lines": [],
                    }
                    self._add_adjustment([name, cost, code], line)
                    self.data["items"].append(self.current_item)

                    if self.current_weight and line.startswith("WT"):
                        self._add_weight_readout(shouldHaveCost=False)
                    if self.current_quantity:
                        self._add_quantity_readout()

                    continue

                match_credit = CREDIT_LINE.match(line)
                if match_credit:
                    [sc, name, cost, code] = match_credit.groups()
                    self._add_adjustment([name, cost, code], line)
                    continue

                match_verify = re.match(
                    r"\s+(PRICE YOU PAY)\s+(\d+\.\d\d|FREE)\s+", line
                )
                if match_verify:
                    [text, cost] = match_verify.groups()
                    if cost == "FREE":
                        cost = "0"
                    price = Decimal(cost)
                    self.current_item["adjustments"].append(
                        {
                            "name": text,
                            "price": price,
                            "type": "verify",
                        }
                    )
                    self.current_item["lines"].append(line)

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

                match_verify = re.match(
                    r"\s+(PRICE YOU PAY FOR)\s+(\d)\s+(\d+\.\d\d)\s+", line
                )
                if match_verify:
                    [text, quantity, cost] = match_verify.groups()
                    price = Decimal(cost)
                    self.current_item["adjustments"].append(
                        {
                            "name": text,
                            "price": price,
                            "quantity": int(quantity),
                            "type": "verify",
                        }
                    )
                    self.current_item["lines"].append(line)

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
                    self.current_weight = {"line": line, "match": match_weight.groups()}
                    continue

                match_quantity = QUANTITY_LINE.match(line)
                if match_quantity:
                    self.current_quantity = {
                        "line": line,
                        "match": match_quantity.groups(),
                    }
                    continue

            self.data.setdefault("skipped", []).append(line)
            self.skip_rest = True
            self.warning.append(f"skipped first, skip rest -- {line}")

        self.current_item = None

    def _add_adjustment(self, match, line):
        if self.current_item is None:
            self.warning.append("not currently parsing anything")
        if not match or len(match) != 3:
            self.warning.append("invalid match argument")

        [name, cost, code] = match
        taxable = code in TAXABLE_CODES
        scale = -1 if code[0] == "-" else 1

        # XXX should it be "tax_code !== self.current_item["tax_code"]"
        if taxable != self.current_item["taxable"]:
            self.warning.append(f"mismatch taxable: {match} -- {self.current_item}")

        amount = Decimal(cost)
        self.current_item["price"] += amount * scale
        self.current_item["adjustments"].append(
            {
                "name": name.strip(),
                "amount": amount,
                "code": code,
                "type": "sum",
            }
        )

        self.current_item["lines"].append(line)

    def _add_weight_readout(self, shouldHaveCost=False):
        [weight_readout, _, cost] = self.current_weight["match"]
        self.current_item["lines"].insert(
            -2 if shouldHaveCost else -1, self.current_weight["line"]
        )
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

    def _add_quantity_readout(self):
        [quantity_readout] = self.current_quantity["match"]
        self.current_item["lines"].insert(-1, self.current_quantity["line"])
        self.current_quantity = None
        last_adjustment = self.current_item["adjustments"][-1]
        last_adjustment["quantity_readout"] = quantity_readout

        match_breakdown = re.match(r"^(\d+) @ (\d+\.\d\d)", quantity_readout)
        if not match_breakdown:
            self.warning.append(
                f"could not break down quantity_readout {quantity_readout} -- {self.current_item}"
            )
        else:
            [count, cost] = match_breakdown.groups()
            amount = int(count) * Decimal(cost)
            if amount != last_adjustment["amount"]:
                self.warning.append(
                    f"quantity_readout does not match actual amount? {quantity_readout} {last_adjustment} -- {self.current_item}"
                )
