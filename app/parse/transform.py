from decimal import Decimal
from enum import Enum

from app.parse.receipt import CATEGORIES


class TransformFormat(Enum):
    List = 1
    Table = 2


def transform_receipt_parsed(transactions, *, format: TransformFormat):
    """
    Given a list of items from a receipt (transaction date, item name, item price, item category, etc),
    convert this into some kind of data table to be used with a library
    """
    results = []
    for trans in transactions:
        if "receipt_data" in trans:
            result = None
            if format == TransformFormat.List:
                result = _transform_receipt_parsed_to_list(trans)
            elif format == TransformFormat.Table:
                result = _transform_receipt_parsed_to_table(trans)

            if isinstance(result, list):
                results.extend(result)
            else:
                results.append(result)
    return results


def _transform_receipt_parsed_to_list(trans):
    items = []
    for item in trans["receipt_data"]["items"]:
        items.append(
            {
                "date": trans["date"],
                "category": item["category"],
                "price": item["price"],
            }
        )
    return items


def _transform_receipt_parsed_to_table(trans):
    agg = {"date": trans["date"], **{category: Decimal("0") for category in CATEGORIES}}
    for item in trans["receipt_data"]["items"]:
        category = item["category"]
        agg[category] = agg.get(category, Decimal("0")) + item["price"]
    return agg
