import mailbox
import email


def parse_mbox_file(mbox_file_path):
    """
    Parses an Mbox file and prints information from each email.
    """
    contents = []
    try:
        # Open the Mbox file
        mbox = mailbox.mbox(mbox_file_path)

        # Iterate through each message in the Mbox file
        for i, message in enumerate(mbox):
            # Extract header information
            # print(f"From: {message['from']}")
            # print(f"To: {message['to']}")
            # print(f"Subject: {message['subject']}")
            # print(f"Date: {message['date']}")

            # Extract and print the email body (plain text part)
            if message.is_multipart():
                for part in message.walk():
                    ctype = part.get_content_type()
                    cdispo = str(part.get("Content-Disposition"))

                    # print(f"Content-Type: {ctype}, Content-Disposition: {cdispo}")

                    # Only consider text parts, not attachments
                    if (
                        ctype == "text/plain" or ctype == "text/html"
                    ) and "attachment" not in cdispo:
                        try:
                            body = part.get_payload(decode=True).decode()
                            contents.append(body)
                        except UnicodeDecodeError:
                            print("[Body could not be decoded]")
                        break  # Stop after finding the first plain text part
            else:
                try:
                    body = message.get_payload(decode=True).decode()
                    raise Exception("haven't seen this before")
                except UnicodeDecodeError:
                    print("[Body could not be decoded]")

    except FileNotFoundError:
        print(f"[Error: Mbox file not found at {mbox_file_path}]")
    except Exception as e:
        print(f"[An error occurred: {e}]")

    return contents
