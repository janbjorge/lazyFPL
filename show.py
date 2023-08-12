import fetch
import structures

if __name__ == "__main__":
    print(structures.Squad([p for p in fetch.players() if p.xP is not None]))
