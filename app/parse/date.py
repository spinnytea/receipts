import datetime

date_string = "Sat, 26 Apr 2025 15:23:14 +0000"
format_string = "%a, %d %b %Y %H:%M:%S %z"


def parse_date_raw(transactions):
    for trans in transactions:
        if "date_raw" not in trans:
            trans.setdefault("warning", []).append("missing date")
        else:
            try:
                trans["date"] = datetime.datetime.strptime(
                    trans["date_raw"], format_string
                )
            except ValueError as e:
                trans.setdefault("warning", []).append(f"Error parsing date: {e}")


def datetime_serializer(obj):
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()  # Converts to ISO string
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")
