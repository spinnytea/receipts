from enum import Enum


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
