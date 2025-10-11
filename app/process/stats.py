import math
from decimal import Decimal

from app.parse.receipt import CATEGORIES

GRAPH_BLOCK = "█"
GRAPH_BLOCK_HALF = "▐"
GRAPH_BLOCK_NONE = " "


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


def stats_graph_agg(agg, half=False, log_base=2):
    """
    TODO this needs a better name, and argument name
    TODO arg for scale (e.g. log2, log10, linear, etc)
    TODO arg for sort (name vs sum)
    """
    cats = []
    max_sizes = {
        "graph": 0,
        "sum": 0,
    }
    for category, sum in agg.get("cats", {}).items():
        f = float(sum)
        if f > 0:
            graph_size = math.ceil(math.log(f, log_base))
            sum_size = len(str(sum))
            max_sizes["graph"] = max(max_sizes["graph"], graph_size)
            max_sizes["sum"] = max(max_sizes["sum"], sum_size)

            # the last block in the graph is special, to add more granularity
            # (why not just adjust log_base? screensize, i guess)
            delta = graph_size - math.log(f, log_base)
            graph_cap = GRAPH_BLOCK
            if half and 0.85 < delta:
                # if it's way too close to the threshold, then subtract one from the size
                graph_cap = GRAPH_BLOCK_NONE
            elif half and 0.4 < delta:
                # if it's closer to the half way mark, show a half block
                graph_cap = GRAPH_BLOCK_HALF

            cats.append(
                {
                    "category": category,
                    "sum": sum,
                    "float": f,
                    "graph_size": graph_size,
                    "graph_cap": graph_cap,
                }
            )
    graph = "\n"
    for cat in cats:
        # XXX is there a more terse way to unpack this?
        # TODO better graph character
        category = cat["category"]
        sum = cat["sum"]
        g = (
            cat["graph_cap"]
            .ljust(cat["graph_size"], GRAPH_BLOCK)
            .rjust(max_sizes["graph"], GRAPH_BLOCK_NONE)
        )
        s = str(cat["sum"]).rjust(max_sizes["sum"])
        graph += f" {g}  {s} · {category}\n"
    return graph
