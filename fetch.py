import csv
import datetime
import io
import itertools
import typing as T

import requests
from dateutil.parser import parse as dt_parser


import cache
import structures


def merged_team_list(
    url="https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/master_team_list.csv",
) -> T.Generator[dict[str, str], None, None]:
    yield from csv.DictReader(io.StringIO(requests.get(url).text))


@cache.fcache(ttl=datetime.timedelta(days=1))
def players(
    url="https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/2021-22/gws/merged_gw.csv",
    last_n: int = 10,
) -> tuple[structures.Player, ...]:
    team_name_lookup = {row["team"]: row["team_name"] for row in merged_team_list()}

    players: list[structures.Player] = []

    for name, matches in itertools.groupby(
        sorted(
            csv.DictReader(io.StringIO(requests.get(url).text), delimiter=","),
            key=lambda r: r["name"],
        ),
        key=lambda r: r["name"],
    ):
        last_n_list = sorted(matches, key=lambda r: dt_parser(r["kickoff_time"]))[
            -last_n:
        ]
        players.append(
            structures.Player(
                minutes=[int(r["minutes"]) for r in last_n_list],
                name=name,
                opponent=[team_name_lookup[r["opponent_team"]] for r in last_n_list],
                points=[int(r["total_points"]) for r in last_n_list],
                position=last_n_list[-1]["position"],
                price=[int(r["value"]) for r in last_n_list],
                selected=[int(r["selected"]) for r in last_n_list],
                team=[r["team"] for r in last_n_list],
            )
        )

    return sorted(players, key=lambda x: x.name)


if __name__ == "__main__":
    for player in players():
        print(player)
