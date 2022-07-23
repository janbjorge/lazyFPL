import argparse
import csv
import sys


def show(columns: tuple[str], delimiter: str):
    for row in csv.DictReader(sys.stdin, delimiter=delimiter):
        print(f"{delimiter}".join(row[column] for column in columns), flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("columns", nargs="+", default=tuple())
    parser.add_argument("--delimiter", default=",")
    parsed = parser.parse_args()
    show(parsed.columns, parsed.delimiter)


if __name__ == "__main__":
    main()
