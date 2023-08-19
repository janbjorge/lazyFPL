import datetime
import functools
import itertools
import traceback

import dateutil.parser
import requests

import conf
import database
import ml_model
import structures


@functools.cache
def bootstrap() -> dict:
    return requests.get(
        "https://fantasy.premierleague.com/api/bootstrap-static/"
    ).json()


def bootstrap_events() -> list[dict]:
    return bootstrap()["events"]


def next_gw() -> int:
    for e in bootstrap_events():
        if e["is_next"]:
            return int(e["id"])
    raise ValueError


def current_gw() -> int:
    for e in bootstrap_events():
        if e["is_current"]:
            return int(e["id"])
    raise ValueError


def next_deadline() -> datetime.timedelta:
    for e in bootstrap_events():
        if e["is_next"]:
            deadline = dateutil.parser.parse(e["deadline_time"])
            now = datetime.datetime.now(tz=datetime.timezone.utc)
            return deadline - now
    raise ValueError


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
            if conf.debug:
                traceback.print_exception(e)
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
                xP=None,
            )
        )

    for p in pool:
        try:
            p.xP = ml_model.xP(p)
        except ValueError as e:
            if conf.debug:
                traceback.print_exception(e)

    return pool


@functools.cache
def picks(team_id: str) -> dict:
    return requests.get(
        f"https://fantasy.premierleague.com/api/entry/{team_id}/event/{current_gw()}/picks/",
        timeout=10,
    ).json()["picks"]


@functools.cache
def my_team(
    team_id: str = conf.teamid,
) -> structures.Squad:
    assert team_id
    names = set(player_name(pick["element"]) for pick in picks(team_id))
    return structures.Squad([p for p in players() if p.name in names])


if __name__ == "__main__":
    import sys

    to_show = sys.argv[1:]
    for p in sorted(players(), key=lambda x: (x.team, x.webname)):
        if p.webname in to_show or p.team in to_show:
            print(f"{p.webname} ({p.team})")
            for f in sorted(
                (f for f in p.fixutres if f.points is not None),
                key=lambda x: x.kickoff_time,
                reverse=True,
            )[: conf.backtrace]:
                vs = (
                    f"{f.opponent} vs. {p.team}"
                    if f.at_home
                    else f"{p.team} vs. {f.opponent}"
                )
                print(
                    f"  {vs:<30} Points: {f.points} Minutes: {f.minutes} Diff: {f.relative.mean:.1f}"
                )
