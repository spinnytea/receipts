import sys
from parse import parse_mbox_file

if __name__ == "__main__":
    mbox_file = sys.argv[1]
    contents = parse_mbox_file(mbox_file)
    print(f"parse {len(contents)} messages")
