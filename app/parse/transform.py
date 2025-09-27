def transform_receipt_parsed(transactions):
    """
    Given a list of items from a receipt (transaction date, item name, item price, item category, etc),
    convert this into some kind of data table to be used with a library
    """
    for trans in transactions:
        if "receipt_raw" in trans:
            _transform_receipt_parsed(trans)


def _transform_receipt_parsed(trans):
    # TODO do it
    pass
