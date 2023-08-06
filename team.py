import fetch
import helpers

if __name__ == "__main__":
    helpers.lprint(
        (mt := fetch.my_team()).players,
        best=[p.name for p in helpers.best_lineup(mt.players)],
    )
