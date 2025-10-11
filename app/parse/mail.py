import mailbox
import os
from email import policy
from email.parser import BytesParser


def parse_eml_file(eml_file_path):
    """
    Parses an Eml file, converts the email in some kind of data object

    eml_file_path: filepath of eml file
    return list of dicts
        id: some arbitrary value to tell them apart, within a given file
        date_raw: date from email
        body_html: html content of email
        body_text: text content of email
    """
    transactions = []

    try:
        with open(eml_file_path, "rb") as fp:
            message = BytesParser(policy=policy.default).parse(fp)
        transactions.append(get_transaction_from_message(message, eml_file_path, 0))
    except FileNotFoundError:
        print(f"Error: Mbox file not found at {eml_file_path}")
    except Exception as e:
        print(f"An error occurred: {e}")

    return transactions


def parse_mbox_file(mbox_file_path):
    """
    Parses an Mbox file, converts each email in some kind of data object

    mbox_file_path: filepath of mbox file
    return list of dicts
        id: some arbitrary value to tell them apart
        date_raw: date from email
        body_html: html content of email
        body_text: text content of email
    """
    transactions = []

    try:
        # Open the Mbox file
        with MboxReader(mbox_file_path) as mbox:
            # Iterate through each message in the Mbox file
            for i, message in enumerate(mbox):
                transactions.append(
                    get_transaction_from_message(message, mbox_file_path, i)
                )
    except FileNotFoundError:
        print(f"Error: Mbox file not found at {mbox_file_path}")
    except Exception as e:
        print(f"An error occurred: {e}")

    return transactions


def get_transaction_from_message(message, filename, idx):
    trans = {}
    trans["filename"] = filename
    trans["idx"] = idx

    # Extract header information
    # data["from"] = message["from"]
    # data["to"] = message["to"]
    # data["subject"] = message["subject"]
    trans["date_raw"] = message["date"]

    # XXX consider using date instead of idx
    trans["id"] = f"{trans['date_raw']} @ {trans['filename']}"

    # Extract and print the email body (plain text part)
    if message.is_multipart():
        for part in message.walk():
            ctype = part.get_content_type()
            cdispo = str(part.get("Content-Disposition"))

            # trans.setdefault("warning", []).append(
            #     f"Message: {trans['date_raw']}, Content-Type: {ctype}, Content-Disposition: {cdispo}"
            # )

            # Only consider text parts, not attachments
            if (ctype == "text/html") and "attachment" not in cdispo:
                if "body_html" in trans:
                    trans.setdefault("warning", []).append(
                        "Multiple html bodies in message"
                    )
                try:
                    trans["body_html"] = part.get_payload(decode=True).decode()
                except UnicodeDecodeError:
                    trans.setdefault("warning", []).append(
                        f"Body could not be decoded (multipart, {ctype})"
                    )
                break  # Stop after finding the first plain text part
    else:
        try:
            trans["body_text"] = message.get_payload(decode=True).decode()
        except UnicodeDecodeError:
            trans.setdefault("warning", []).append("Body could not be decoded")

    return trans


class MboxReader:
    def __init__(self, resource_name):
        self.resource_name = resource_name
        self.resource = None

    def __enter__(self):
        self.resource = mailbox.mbox(self.resource_name)
        return self.resource  # This value will be assigned to the 'as' variable

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.resource is not None:
            self.resource.close()
        self.resource = None
        # if exc_type:
        #     print(f"An exception occurred: {exc_val}")
        return False


def traverse_files_recursive(directory_path):
    """
    Recursively parse eml/mbox all files within a given directory and its subdirectories.

    De-dup by date (full timestamp), in case exported the same email.

    directory_path (str): The path to the directory to start the search from.
    return list of transactions
    """
    unique_transactions = {}
    for root, _, files in os.walk(directory_path):
        for file in files:
            full_path = os.path.join(root, file)
            ts = []
            if file.lower().endswith(".eml"):
                ts.extend(parse_eml_file(full_path))
            elif file.lower().endswith(".mbox"):
                ts.extend(parse_mbox_file(full_path))
            for trans in ts:
                date_raw = trans["date_raw"]
                if date_raw in unique_transactions:
                    uniq = unique_transactions[date_raw]
                    print(
                        f"Duplicate email at {date_raw}\n  {trans['id']}\n  {uniq['id']}"
                    )
                    uniq.setdefault("duplicates", [uniq["id"]]).append(trans["id"])
                else:
                    unique_transactions[date_raw] = trans
    return list(unique_transactions.values())
