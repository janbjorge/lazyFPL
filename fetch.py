import functools
import itertools
import os
import traceback

import requests

import conf
import database
import helpers
import ml_model
import structures


@functools.cache
def bootstrap() -> dict:
    return requests.get(
        "https://fantasy.premierleague.com/api/bootstrap-static/"
    ).json()


@functools.cache
def player_name(pid: int) -> str:
    for element in bootstrap()["elements"]:
        if element["id"] == pid:
            return f'{element["first_name"]} {element["second_name"]}'
    raise ValueError(f"No player named: {pid}")


@functools.cache
def players() -> list["structures.Player"]:
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
                opponent_strength_overall_away=game.opponent_trength_overall_away,
            )
            for game in games
        ]

        try:
            team = [g for g in games if g.upcoming][-1].team
        except IndexError as e:
            if conf.env.debug:
                print(e)
            continue

        pool.append(
            structures.Player(
                fixutres=fixtures,
                name=name,
                news=games[-1].news,
                position=games[-1].position,
                price=database.price(games[-1].player_id),
                team=team,
                webname=database.webname(games[-1].player_id),
            )
        )

    remove = set[structures.Player]()
    for p in pool:
        try:
            p.xP = ml_model.xP(p)
        except ValueError as e:
            if conf.env.debug:
                traceback.print_exc()
            remove.add(p)

    for r in remove:
        while r in pool:
            pool.remove(r)

    return pool


@functools.cache
def picks(team_id: str) -> dict:
    gmw = 1
    prev = None
    while req := requests.get(
        f"https://fantasy.premierleague.com/api/entry/{team_id}/event/{gmw}/picks/",
        timeout=10,
    ):
        gmw += 1
        prev = req
    assert prev is not None
    return prev.json()["picks"]


@functools.cache
def my_team(
    team_id: str = os.environ.get("FPL_TEAMID", ""),
) -> structures.Squad:
    assert team_id
    names = set(player_name(pick["element"]) for pick in picks(team_id))
    return structures.Squad([p for p in players() if p.name in names])


if __name__ == "__main__":
    print(structures.Squad(players()))
