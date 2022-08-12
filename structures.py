import dataclasses
import datetime
import statistics
import typing as T

import helpers


@dataclasses.dataclass(frozen=True)
class Fixture:
    at_home: bool
    away: str
    difficulty: int
    home: str
    kickoff_time: datetime.datetime


@dataclasses.dataclass(eq=True, unsafe_hash=True)
class Player:
    coefficients: tuple[float, ...] = dataclasses.field(compare=False, init=False)
    fixutres: list[Fixture] = dataclasses.field(compare=False, repr=False)
    minutes: list[int] = dataclasses.field(compare=False, repr=False)
    name: str = dataclasses.field(compare=True)
    news: str = dataclasses.field(compare=False)
    points: list[int] = dataclasses.field(compare=False, repr=False)
    position: T.Literal["GKP", "DEF", "MID", "FWD"] = dataclasses.field(compare=False)
    price: int = dataclasses.field(compare=True)
    selected: list[int] = dataclasses.field(compare=False, repr=False)
    team: str = dataclasses.field(compare=True)
    webname: str = dataclasses.field(compare=False)
    xP: float = dataclasses.field(compare=False, init=False)

    def __post_init__(self):
        backtrace = 3
        lookahead = 3
        # Missing historical data for: {full_name}, setting xP=0,"
        if len(self.points) > backtrace:
            self.coefficients, self.xP = helpers.xP(
                past_points=self.points,
                backtrace=backtrace,
            )
            self.xP /= self.upcoming_difficulty(lookahead)
        elif 0 < len(self.points) <= backtrace:
            self.coefficients = tuple()
            self.xP = statistics.median(self.points) / backtrace
            self.xP /= self.upcoming_difficulty(lookahead)
        else:
            self.coefficients = tuple()
            self.xP = 0

    @property
    def tp(self) -> int:
        return sum(self.points)

    @property
    def tm(self) -> int:
        return sum(self.minutes)

    def upcoming_difficulty(self, n: int = 3) -> float:
        return sum(f.difficulty for f in self.fixutres[:n]) / (3 * n)
