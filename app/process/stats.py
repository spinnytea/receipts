import math
from decimal import Decimal

from app.parse.receipt import CATEGORIES


def stats_sum_receipt_parsed(transactions):
    """
    Given a list of items from a receipt (transaction date, item name, item price, item category, etc),
    sum all of the item categories
    """
    cats = {category: Decimal("0") for category in CATEGORIES}
    agg = {
        "date_min": None,
        "date_max": None,
        "cats": cats,
    }

    for trans in transactions:
        if "receipt_data" in trans:
            if agg["date_min"] is None:
                agg["date_min"] = trans["date"]
                agg["date_max"] = trans["date"]
            elif trans["date"] < agg["date_min"]:
                agg["date_min"] = trans["date"]
            elif trans["date"] > agg["date_max"]:
                agg["date_max"] = trans["date"]

            for item in trans["receipt_data"]["items"]:
                category = item["category"]
                cats[category] = cats.get(category, Decimal("0")) + item["price"]
    return agg


def stats_graph_agg(agg):
    """
    TODO this needs a better name, and argument name
    TODO arg for scale (e.g. log2, log10, linear, etc)
    TODO arg for sort (name vs sum)
    """
    cats = []
    max_size = 0
    for category, sum in agg.get("cats", {}).items():
        f = float(sum)
        if f > 0:
            size = math.ceil(math.log2(f))
            max_size = max(max_size, size)
            cats.append(
                {
                    "category": category,
                    "Decimal": sum,
                    "float": f,
                    "size": size,
                }
            )
    graph = "\n"
    for cat in cats:
        # XXX is there a more terse way to unpack this?
        # TODO better graph character
        category = cat["category"]
        sum = cat["Decimal"]
        size = cat["size"]
        graph += f"{''.rjust(size, '■').rjust(max_size)} - {category} ({sum})\n"
    return graph
