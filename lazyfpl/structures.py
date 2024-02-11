from __future__ import annotations

import dataclasses
import datetime
import statistics
from typing import Generator, Sequence

import pydantic

from lazyfpl import conf, database, helpers


@dataclasses.dataclass
class Fixture:
    at_home: bool
    kickoff_time: datetime.datetime
    minutes: int | None
    opponent: str
    opponent_short: str
    opponent_strength: int
    player: str
    points: int | None
    session: database.SESSIONS
    team: str
    team_short: str
    team_strength: int
    upcoming: bool
    webname: str


@dataclasses.dataclass(eq=True, unsafe_hash=True)
class Player:
    fixutres: list[Fixture] = dataclasses.field(compare=False, repr=False)
    name: str = dataclasses.field(compare=True)
    news: str = dataclasses.field(compare=True)
    position: database.POSITIONS = dataclasses.field(compare=False)
    price: int = dataclasses.field(compare=False)
    selected: int | None = dataclasses.field(compare=False)
    team: str = dataclasses.field(compare=False)
    team_short: str = dataclasses.field(compare=False)
    webname: str = dataclasses.field(compare=True)
    xP: float | None

    def tp(self, session: database.SESSIONS = database.CURRENT_SESSION) -> int:
        return sum(f.points or 0 for f in self.fixutres if f.session == session)

    def mtm(self, last: int = conf.backtrace) -> float:
        # fixutre.minutes is None if the gameweek is not started
        # need to filter out fixutres with minutes as none.
        try:
            return statistics.mean(
                (
                    f.minutes or 0
                    for f in sorted(
                        (f for f in self.fixutres if not f.upcoming),
                        key=lambda x: x.kickoff_time,
                    )[-last:]
                )
            )
        except statistics.StatisticsError:
            return 0.0

    def upcoming_difficulty(self) -> int:
        upcoming = [f for f in self.fixutres if f.upcoming][: conf.lookahead]
        return sum(f.team_strength - f.opponent_strength for f in upcoming)

    def upcoming_opponents(self) -> list[str]:
        return [
            x.opponent_short
            for x in sorted(
                (f for f in self.fixutres if f.upcoming),
                key=lambda f: f.kickoff_time,
            )
        ]

    def str_upcoming_opponents(self) -> str:
        return " - ".join(self.upcoming_opponents()[: conf.lookahead])

    def __str__(self) -> str:
        raise NotImplementedError

    def display(self) -> dict[str, float | str | None]:
        return {
            "xP": self.xP,
            "Price": self.price,
            "TP": self.tp(),
            "UD": self.upcoming_difficulty(),
            "Selected": self.selected,
            "Webname": self.webname,
            "Team": self.team,
            "Position": self.position,
            "Upcoming opponents": self.str_upcoming_opponents(),
            "News": self.news,
        }


class Squad:
    def __init__(self, players: Sequence[Player]):
        self.players = players

    def price(self) -> int:
        return helpers.squad_price(self.players)

    def best_lineup(self) -> list[Player]:
        return helpers.best_lineup(self.players)

    def SxP(self) -> float:
        # Squad xP
        return helpers.squad_xP(self.players)

    def LxP(self) -> float:
        # Lineup xP
        return helpers.squad_xP(self.best_lineup())

    def CxP(self) -> float:
        # Combined xP
        return (self.SxP() ** 2 + self.LxP() ** 2) ** 0.5

    def tscore(self) -> int:
        return helpers.tcnt(self.players)

    def sscore(self, n: int = conf.lookahead) -> int:
        # "sscore -> "schedule score"
        return helpers.sscore(self.players, n=n)

    def tsscore(self, n: int = conf.lookahead) -> float:
        return helpers.tsscore(self.players)

    def __iter__(self) -> Generator[Player, None, None]:
        yield from self.players

    def __len__(self) -> int:
        return len(self.players)

    def __str(self) -> Generator[str, None, None]:
        yield f"Price: {self.price()/10} Size: {len(self.players)}"
        yield f"LxP: {self.LxP():.1f} SxP: {self.SxP():.1f} CxP: {self.CxP():.1f}"
        yield (
            f"Schedule score: {self.sscore()} Team score: {self.tscore()} "
            f"TSscore: {self.tsscore():.2f}"
        )
        bis = helpers.best_lineup(self.players)
        yield helpers.tabulater(
            [
                dict({"BIS": "X" if p in bis else ""} | p.display())
                for p in sorted(
                    self.players,
                    key=lambda x: (-helpers.position_order(x.position), -(x.xP or 0)),
                )
            ],
        )

    def __str__(self) -> str:
        return "\n".join(self.__str())


class HistoricGame(pydantic.BaseModel):
    assists: int
    bonus: int
    bps: int
    clean_sheets: int
    creativity: float
    element: int
    fixture: float
    goals_conceded: float
    goals_scored: float
    GW: int
    ict_index: float
    influence: float
    kickoff_time: datetime.datetime
    minutes: int
    name: str
    opponent_team: int
    own_goals: int
    penalties_missed: int
    penalties_saved: int
    position: database.POSITIONS
    red_cards: int
    round: int
    saves: int
    selected: int
    team_a_score: int
    team_h_score: int
    team: str
    threat: float
    total_points: int
    transfers_balance: int
    transfers_in: int
    transfers_out: int
    value: int
    was_home: bool
    xP: float
    yellow_cards: int

    @pydantic.field_validator("position", mode="before")
    def gk_to_gkp(cls, value: str) -> str:
        return "GKP" if value == "GK" else value


class UpcommingGame(pydantic.BaseModel):
    code: int
    difficulty: int
    event_name: str | None = pydantic.Field(default=None)
    event: int | None = pydantic.Field(default=None)
    finished: bool
    id: int
    is_home: bool
    kickoff_time: datetime.datetime | None = pydantic.Field(default=None)
    minutes: int
    provisional_start_time: bool
    team_a_score: int | None = pydantic.Field(default=None)
    team_a: int
    team_h_score: int | None = pydantic.Field(default=None)
    team_h: int


class Team(pydantic.BaseModel):
    code: int
    draw: int
    id: int
    loss: int
    name: str
    played: int
    points: int
    position: int
    pulse_id: int
    short_name: str
    strength: int
    unavailable: bool
    win: int
