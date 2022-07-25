import difflib
import sys

import fetch


def fuzzy_match(a: str, b: str) -> bool:
    if a in b or b in a:
        return True
    if difflib.SequenceMatcher(None, a, b).ratio() > 0.75:
        return True
    for suba in a.split():
        for subb in b.split():
            if difflib.SequenceMatcher(None, suba, subb).ratio() > 0.75:
                return True
    return False


def main():
    for player in fetch.players():
        if fuzzy_match(player.name.lower(), " ".join(sys.argv[1:]).lower()):
            print(player)


if __name__ == "__main__":
    main()
