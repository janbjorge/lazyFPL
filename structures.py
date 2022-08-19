import dataclasses
import datetime
import statistics
import typing as T

import helpers


@dataclasses.dataclass(frozen=True)
class Difficulty:
    attack: float
    defence: float
    overall: float


@dataclasses.dataclass(frozen=True)
class Fixture:
    at_home: bool
    kickoff_time: datetime.datetime
    minutes: T.Optional[int]
    opponent: str
    player: str
    points: T.Optional[int]
    session: T.Literal["2021-22", "2022-23"]
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
                self.team_strength_attack_home / self.opponent_strength_defence_away
            )
            defence = (
                self.team_strength_defence_home / self.opponent_strength_attack_away
            )
            overall = (
                self.team_strength_overall_home / self.opponent_strength_overall_away
            )
        else:
            attack = (
                self.team_strength_attack_away / self.opponent_strength_defence_home
            )
            defence = (
                self.team_strength_defence_away / self.opponent_strength_attack_home
            )
            overall = (
                self.team_strength_overall_away / self.opponent_strength_overall_home
            )
        return Difficulty(
            attack=attack,
            defence=defence,
            overall=overall,
        )


@dataclasses.dataclass(eq=True, unsafe_hash=True)
class Player:
    coefficients: tuple[float, ...] = dataclasses.field(compare=False, init=False)
    fixutres: list[Fixture] = dataclasses.field(compare=False, repr=False)
    name: str = dataclasses.field(compare=True)
    news: str = dataclasses.field(compare=False)
    position: T.Literal["GKP", "DEF", "MID", "FWD"] = dataclasses.field(compare=False)
    price: int = dataclasses.field(compare=False)
    team: str = dataclasses.field(compare=False)
    webname: str = dataclasses.field(compare=True)
    xP: float = dataclasses.field(compare=False, init=False)

    def __post_init__(self):
        backtrace = 2

        # Missing historical data for: {full_name}, setting xP=0,"
        enough_observations = sum(not f.upcoming for f in self.fixutres) > backtrace
        if enough_observations:
            self.coefficients, self.xP = helpers.xP(
                fixtures=self.fixutres,
                backtrace=backtrace,
            )
        else:
            self.coefficients = tuple()
            self.xP = 0

    @property
    def tp(self) -> int:
        return sum(
            f.points for f in self.fixutres if f.points and f.session == "2022-23"
        )

    @property
    def tm(self) -> int:
        return sum(
            f.minutes for f in self.fixutres if f.minutes and f.session == "2022-23"
        )

    def upcoming_difficulty(self, n: int = 3) -> float:
        nfixutres = [f for f in self.fixutres if f.upcoming][:n]
        return statistics.mean(
            (f.relative.attack + f.relative.defence + f.relative.overall) / 3
            for f in nfixutres
        )
