import mailbox


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
        # TODO class MboxReader / with MboxReader(mboxfilename) as mbox:
        mbox = mailbox.mbox(mbox_file_path)

        # Iterate through each message in the Mbox file
        for i, message in enumerate(mbox):
            trans = {}
            trans["idx"] = i

            # Extract header information
            # data["from"] = message["from"]
            # data["to"] = message["to"]
            # data["subject"] = message["subject"]
            trans["date_raw"] = message["date"]

            trans["id"] = f"{i}@{trans['date_raw']}"

            # Extract and print the email body (plain text part)
            if message.is_multipart():
                for part in message.walk():
                    ctype = part.get_content_type()
                    cdispo = str(part.get("Content-Disposition"))

                    # trans.setdefault("warning", []).append(
                    #     f"Message: {trans['id']}, Content-Type: {ctype}, Content-Disposition: {cdispo}"
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

            transactions.append(trans)

        mbox.close()

    except FileNotFoundError:
        print(f"Error: Mbox file not found at {mbox_file_path}")
        mbox.close()
    except Exception as e:
        print(f"An error occurred: {e}")
        mbox.close()

    return transactions
