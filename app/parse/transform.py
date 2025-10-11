from decimal import Decimal
from enum import Enum

from app.parse.receipt import CATEGORIES


class TransformFormat(Enum):
    List = 1
    Table = 2


# @warnings.deprecated("only needed if we use/learn an external tool")
def transform_receipt_parsed(transactions, *, format: TransformFormat):
    """
    Given a list of items from a receipt (transaction date, item name, item price, item category, etc),
    convert this into some kind of data table to be used with a library
    """
    data_dump = []
    for trans in transactions:
        if "receipt_data" in trans:
            if format == TransformFormat.List:
                data_dump.extend(_transform_receipt_parsed_to_list(trans))
            elif format == TransformFormat.Table:
                data_dump.append(_transform_receipt_parsed_to_table(trans))
    return data_dump


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
