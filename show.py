import sys

import conf
import fetch
import structures

if __name__ == "__main__":
    if toshow := sys.argv[1:]:
        for show in toshow:
            for player in fetch.players():
                if (
                    player.webname.casefold() == show.casefold()
                    or player.team.casefold() == show.casefold()
                ):
                    points = [str(f.points) for f in player.fixutres if not f.upcoming][
                        -conf.backtrace :
                    ] + [str(player.xP)]

                    print(f"{player}{' -> '.join(points)}")
    else:
        print(
            structures.Squad(
                [p for p in fetch.players() if p.xP is not None and not p.news]
            )
        )
