import fetch
import helpers


if __name__ == "__main__":
    helpers.lprint(
        fetch.my_team(),
        best=[p.name for p in helpers.best_lineup(fetch.my_team())],
    )
