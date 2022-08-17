import itertools
import os
import typing as T

import requests


import database
import helpers
import structures


def bootstrap() -> dict:
    return requests.get(
        "https://fantasy.premierleague.com/api/bootstrap-static/"
    ).json()


def player_name(pid: int) -> str:
    for element in bootstrap()["elements"]:
        if element["id"] == pid:
            return f'{element["first_name"]} {element["second_name"]}'
    raise ValueError(f"No player named: {pid}")


def players() -> list[structures.Player]:

    pool = list[structures.Player]()

    for (name, webname), _games in itertools.groupby(
        sorted(database.games(), key=lambda x: (x.player, x.webname)),
        lambda x: (x.player, x.webname),
    ):
        games = list(sorted(_games, key=lambda x: x.kickoff))
        fixtures = [
            structures.Fixture(
                at_home=game.is_home,
                kickoff_time=game.kickoff,
                minutes=game.minutes,
                opponent=game.opponent,
                player=name,
                points=game.points,
                session=game.session,
                team=game.team,
                upcoming=game.upcoming,
                webname=webname,
                team_strength_attack_home=game.team_strength_attack_home,
                team_strength_attack_away=game.team_strength_attack_away,
                team_strength_defence_home=game.team_strength_defence_home,
                team_strength_defence_away=game.team_strength_defence_away,
                team_strength_overall_home=game.team_strength_overall_home,
                team_strength_overall_away=game.team_strength_overall_away,
                opponent_strength_attack_home=game.opponent_strength_attack_home,
                opponent_strength_attack_away=game.opponent_strength_attack_away,
                opponent_strength_defence_home=game.opponent_strength_defence_home,
                opponent_strength_defence_away=game.opponent_strength_defence_away,
                opponent_strength_overall_home=game.opponent_strength_overall_home,
                opponent_trength_overall_away=game.opponent_trength_overall_away,
            )
            for game in games
        ]

        try:
            team = [g for g in games if g.upcoming][-1].team
        except IndexError:
            continue

        pool.append(
            structures.Player(
                fixutres=fixtures,
                name=name,
                news="",
                position=games[-1].position,
                price=database.price(games[-1].player_id),
                team=team,
                webname=database.webname(games[-1].player_id),
            )
        )
    return pool


def my_team(
    team_id: str = os.environ.get("FPL_TEAMID", ""),
    pl_profile: str = os.environ.get("FPL_COOKIE", ""),
) -> T.Sequence[structures.Player]:
    if not team_id:
        raise ValueError("Missing `FPL_TEAMID`.")
    if not pl_profile:
        raise ValueError("Missing `FPL_COOKIE`.")
    team = requests.get(
        f"https://fantasy.premierleague.com/api/my-team/{team_id}/",
        cookies={"pl_profile": pl_profile},
    ).json()
    names = set(player_name(pick["element"]) for pick in team["picks"])
    return [p for p in players() if p.name in names]


if __name__ == "__main__":
    helpers.lprint(players())
