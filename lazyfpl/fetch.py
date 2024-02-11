from __future__ import annotations

import dataclasses
import datetime
import functools
import itertools
import traceback

import dateutil.parser
import requests

from lazyfpl import conf, database, ml_model, structures


@dataclasses.dataclass
class Persona:
    """
    Represents a Persona with first name, second name, and webname.
    """

    first: str
    second: str
    webname: str

    @property
    def combined(self) -> str:
        """
        Returns a combined string of the first and second name.
        """
        return " ".join((self.first, self.second))


@functools.cache
def bootstrap() -> dict:
    """
    Fetches and returns data from the Fantasy Premier League API's
    bootstrap-static endpoint.
    """
    return requests.get(
        "https://fantasy.premierleague.com/api/bootstrap-static/"
    ).json()


def bootstrap_events() -> list[dict]:
    """
    Extracts and returns event-related data from the bootstrap data.
    """
    return bootstrap()["events"]


@functools.cache
def next_gw() -> int:
    """
    Determines and returns the next game week's ID.
    """
    for e in bootstrap_events():
        if e["is_next"]:
            return int(e["id"])
    raise ValueError


@functools.cache
def current_gw() -> int:
    """
    Determines and returns the current game week's ID.
    """
    for e in bootstrap_events():
        if e["is_current"]:
            return int(e["id"])
    raise ValueError


@functools.cache
def next_deadline() -> datetime.timedelta:
    for e in bootstrap_events():
        if e["is_next"]:
            deadline = dateutil.parser.parse(e["deadline_time"])
            now = datetime.datetime.now(tz=datetime.timezone.utc)
            return deadline - now
    raise ValueError


@functools.cache
def person(pid: int) -> Persona:
    """
    Retrieves and returns a Persona object for a given player ID.
    """
    for element in bootstrap()["elements"]:
        if element["id"] == pid:
            return Persona(
                first=element["first_name"],
                second=element["second_name"],
                webname=element["web_name"],
            )
    raise ValueError(f"No player: {pid}")


@functools.cache
def players() -> list[structures.Player]:
    """
    Creates and returns a list of Player objects, each representing a football player.
    """
    pool = list[structures.Player]()

    for (name, webname), _games in itertools.groupby(
        sorted(
            database.games(),
            key=lambda x: (x.player, x.webname),
        ),
        lambda x: (x.player, x.webname),
    ):
        games = sorted(_games, key=lambda x: x.kickoff)
        fixtures = [
            structures.Fixture(
                at_home=game.is_home,
                kickoff_time=game.kickoff,
                minutes=game.minutes,
                opponent=game.opponent,
                opponent_short=game.opponent_short,
                player=name,
                points=game.points,
                session=game.session,
                team=game.team,
                team_short=game.team_short,
                upcoming=game.upcoming,
                webname=webname,
                team_strength=game.team_strength,
                opponent_strength=game.opponent_strength,
            )
            for game in games
        ]

        try:
            next_upcoming = [g for g in games if g.upcoming][0]
            last_game = [g for g in games if not g.upcoming][-1]
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
                team=next_upcoming.team,
                team_short=next_upcoming.team_short,
                webname=database.webname(games[-1].player_id),
                xP=None,
                selected=last_game.selected,
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
def picks() -> list[Persona]:
    """
    Fetches and returns the current team picks from the Fantasy Premier League API.
    """
    if not conf.teamid or not conf.profile:
        raise RuntimeError(
            "Env. FPL-teamid and FPL-cookie/profile must be set. FPL-team id "
            "from URL and cookie 'pl_profile' from 'application' in chrome."
        )

    response = requests.get(
        f"https://fantasy.premierleague.com/api/my-team/{conf.teamid}/",
        cookies={"pl_profile": conf.profile},
    )
    if not response:
        raise RuntimeError("Non 2xx status code.")

    return [person(p["element"]) for p in response.json()["picks"]]


def my_team() -> structures.Squad:
    """
    Constructs and returns a Squad object representing the user's current team.
    """

    def fuzzyed_equal(player: structures.Player, persona: Persona) -> bool:
        personawebname = persona.webname.casefold()
        playerwebname = player.webname.casefold()

        personaname = persona.combined.casefold()
        playername = player.name.casefold()
        return (
            personawebname == playerwebname
            and all(name in personaname for name in playername.split())
            and all(name in playername for name in personaname.split())
        )

    return structures.Squad(
        [p for p in players() if any(fuzzyed_equal(p, pck) for pck in picks())]
    )
