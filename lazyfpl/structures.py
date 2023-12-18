import dataclasses
import datetime
import itertools
import statistics
import typing as T

import pydantic

from lazyfpl import conf, database, helpers


@dataclasses.dataclass(frozen=True)
class Difficulty:
    attack: float
    defence: float
    overall: float

    @property
    def mean(self):
        return statistics.mean((self.attack, self.defence, self.overall))


@dataclasses.dataclass(frozen=True)
class Fixture:
    at_home: bool
    kickoff_time: datetime.datetime
    minutes: T.Optional[int]
    opponent: str
    player: str
    points: T.Optional[int]
    session: database.SESSIONS
    team: str
    upcoming: bool
    webname: str
    team_strength_attack_home: int
    team_strength_attack_away: int
    team_strength_defence_home: int
    team_strength_defence_away: int
    team_strength_overall_home: int
    team_strength_overall_away: int
    opponent_strength_attack_home: int
    opponent_strength_attack_away: int
    opponent_strength_defence_home: int
    opponent_strength_defence_away: int
    opponent_strength_overall_home: int
    opponent_strength_overall_away: int

    @property
    def relative(self) -> Difficulty:
        if self.at_home:
            attack = (
                self.team_strength_attack_home - self.opponent_strength_defence_away
            ) / (self.team_strength_attack_home + self.opponent_strength_defence_away)
            defence = (
                self.team_strength_defence_home - self.opponent_strength_attack_away
            ) / (self.team_strength_defence_home + self.opponent_strength_attack_away)
            overall = (
                self.team_strength_overall_home - self.opponent_strength_overall_away
            ) / (self.team_strength_overall_home + self.opponent_strength_overall_away)
        else:
            attack = (
                self.team_strength_attack_away - self.opponent_strength_defence_home
            ) / (self.team_strength_attack_away + self.opponent_strength_defence_home)
            defence = (
                self.team_strength_defence_away - self.opponent_strength_attack_home
            ) / (self.team_strength_defence_away + self.opponent_strength_attack_home)
            overall = (
                self.team_strength_overall_away - self.opponent_strength_overall_home
            ) / (self.team_strength_overall_away + self.opponent_strength_overall_home)

        return Difficulty(
            attack=attack,
            defence=defence,
            overall=overall,
        )


@dataclasses.dataclass(eq=True, unsafe_hash=True)
class Player:
    fixutres: list[Fixture] = dataclasses.field(compare=False, repr=False)
    name: str = dataclasses.field(compare=True)
    news: str = dataclasses.field(compare=True)
    position: database.POSITIONS = dataclasses.field(compare=False)
    price: int = dataclasses.field(compare=False)
    team: str = dataclasses.field(compare=False)
    webname: str = dataclasses.field(compare=True)
    xP: T.Optional[float]

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
                        (f for f in self.fixutres if f.minutes is not None),
                        key=lambda x: x.kickoff_time,
                    )[-last:]
                )
            )
        except statistics.StatisticsError:
            return 0.0

    def upcoming_difficulty(self) -> float:
        upcoming = [f for f in self.fixutres if f.upcoming][: conf.lookahead]
        return statistics.mean(f.relative.mean for f in upcoming)

    @property
    def next_opponent(self) -> str:
        return min(
            (f for f in self.fixutres if f.upcoming),
            key=lambda f: f.kickoff_time,
        ).opponent

    def upcoming_opponents(self) -> list[str]:
        return [
            x.opponent
            for x in sorted(
                (f for f in self.fixutres if f.upcoming),
                key=lambda f: f.kickoff_time,
            )
        ]

    def __str__(self):
        return (
            f"{(self.xP or 0):<6.1f} {self.price:<6.1f} {self.tp():<4} "
            f"{self.upcoming_difficulty()*10:<8.1f} {self.team:<15} "
            f"{self.position:<9} {self.webname:<20} "
            f"{' - '.join(self.upcoming_opponents()[:conf.lookahead])} "
            f"{self.news}"
        )


class Squad:
    def __init__(self, players: T.Sequence[Player]):
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

    def __iter__(self):
        yield from self.players

    def __len__(self) -> int:
        return len(self.players)

    def __str(self):
        pospri = {"GKP": 0, "DEF": 1, "MID": 2, "FWD": 3}
        yield f"Price: {self.price()/10} Size: {len(self.players)}"
        yield f"LxP: {self.LxP():.1f} SxP: {self.SxP():.1f} CxP: {self.CxP():.1f}"
        yield (
            f"Schedule score: {self.sscore()} Team score: {self.tscore()} "
            f"TSscore: {self.tsscore():.2f}"
        )
        yield (
            "BIS  xP     Price  TP   UD       Team            Position  Player"
            + " " * 15
            + "Upcoming"
            + " " * 30
            + "News"
        )
        for _, players in itertools.groupby(
            sorted(
                self.players,
                key=lambda x: (pospri.get(x.position), x.xP or 0),
                reverse=True,
            ),
            key=lambda x: x.position,
        ):
            for player in players:
                yield ("X    " if player in self.best_lineup() else "     ") + str(
                    player
                )

    def __str__(self) -> str:
        return "\n".join(self.__str())


class HistoricGame(pydantic.BaseModel):
    name: str
    position: database.POSITIONS
    team: str
    xP: float
    assists: int
    bonus: int
    bps: int
    clean_sheets: int
    creativity: float
    element: int
    fixture: float
    goals_conceded: float
    goals_scored: float
    ict_index: float
    influence: float
    kickoff_time: datetime.datetime
    minutes: int
    opponent_team: int
    own_goals: int
    penalties_missed: int
    penalties_saved: int
    red_cards: int
    round: int
    saves: int
    selected: int
    team_a_score: int
    team_h_score: int
    threat: float
    total_points: int
    transfers_balance: int
    transfers_in: int
    transfers_out: int
    value: int
    was_home: bool
    yellow_cards: int
    GW: int

    @pydantic.validator("position", pre=True)
    def gk_to_gkp(cls, value: str) -> str:
        return "GKP" if value == "GK" else value


class UpcommingGame(pydantic.BaseModel):
    code: int
    difficulty: int
    event_name: str | None
    event: int | None
    finished: bool
    id: int
    is_home: bool
    kickoff_time: datetime.datetime | None
    minutes: int
    provisional_start_time: bool
    team_a_score: int | None
    team_a: int
    team_h_score: int | None
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
    strength_attack_away: int
    strength_attack_home: int
    strength_defence_away: int
    strength_defence_home: int
    strength_overall_away: int
    strength_overall_home: int
    unavailable: bool
    win: int
