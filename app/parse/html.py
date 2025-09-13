from html.parser import HTMLParser

DEBUG = False


def parse_body_html(transactions):
    """
    Parses the html body from the email, … and produces something

    transactions: each email is one transaction
            body_html: html body of the email
            @see mail.py

    return: transactions
    """
    for trans in transactions:
        if "body_html" in trans:
            if DEBUG:
                print(f"parsing {trans['id']}")
            __parse_body_html(trans)
    return transactions


def __parse_body_html(trans):
    """
    Do the actual work.
    """
    parser = MyHTMLParser()
    parser.init()
    parser.feed(trans.pop("body_html"))
    receipt_raw = parser.data

    if len(receipt_raw) < 10:
        trans.setdefault("warning", []).append("Receipt seems kinda short?")

    all_line_lengths = set([len(line) for line in receipt_raw])
    if len(all_line_lengths) != 1:
        trans.setdefault("warning", []).append(
            f"Receipt lines are not all the same length: {all_line_lengths}"
        )

    trans["receipt_raw"] = receipt_raw


class MyHTMLParser(HTMLParser):
    # XXX using __init__ will break HTMLParser
    def init(self):
        # HACK it's a little naïve to assume this is what we want
        #  - but also, I am only parsing a very specific email type, sooo
        self.tagToCollect = "pre"
        self.insideTag = False
        self.data = []

    def handle_starttag(self, tag, attrs):
        if tag == self.tagToCollect:
            self.insideTag = True

        if self.insideTag:
            if DEBUG:
                print(f"Start tag: {tag}, Attributes: {attrs}")

    def handle_endtag(self, tag):
        if self.insideTag:
            if DEBUG:
                print(f"End tag: {tag}")

        if tag == self.tagToCollect:
            self.insideTag = False

    def handle_data(self, data):
        if self.insideTag:
            self.data.append(data)
            if DEBUG:
                print(f"Data: {data}")
