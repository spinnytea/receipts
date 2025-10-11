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
