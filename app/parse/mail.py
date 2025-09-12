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
        mbox = mailbox.mbox(mbox_file_path)

        # Iterate through each message in the Mbox file
        for i, message in enumerate(mbox):
            data = {}
            data["id"] = message["date"]

            # Extract header information
            # data["from"] = message["from"]
            # data["to"] = message["to"]
            # data["subject"] = message["subject"]
            data["date_raw"] = message["date"]

            # Extract and print the email body (plain text part)
            if message.is_multipart():
                for part in message.walk():
                    ctype = part.get_content_type()
                    cdispo = str(part.get("Content-Disposition"))

                    # print(f"Message: {data['id']}, Content-Type: {ctype}, Content-Disposition: {cdispo}")

                    # Only consider text parts, not attachments
                    if (ctype == "text/html") and "attachment" not in cdispo:
                        if "body_html" in data:
                            print(f"[Multiple html bodies in message {i}]")
                        try:
                            data["body_html"] = part.get_payload(decode=True).decode()
                        except UnicodeDecodeError:
                            print("[Body could not be decoded]")
                        break  # Stop after finding the first plain text part
            else:
                try:
                    data["body_text"] = message.get_payload(decode=True).decode()
                except UnicodeDecodeError:
                    print("[Body could not be decoded]")

            # validate data
            if sorted(data.keys()) != ["body_html", "date_raw", "id"]:
                print(f"[Unexpected data keys: {sorted(data.keys())}]")

            transactions.append(data)

    except FileNotFoundError:
        print(f"[Error: Mbox file not found at {mbox_file_path}]")
    except Exception as e:
        print(f"[An error occurred: {e}]")

    return transactions
