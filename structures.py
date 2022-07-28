import statistics
import dataclasses
import typing as T
import datetime


@dataclasses.dataclass(frozen=True)
class Fixture:
    at_home: bool
    away: str
    difficulty: int
    home: str
    kickoff_time: datetime.datetime


@dataclasses.dataclass(eq=True)
class Player:
    fixutres: tuple[Fixture, ...] = dataclasses.field(compare=False)
    minutes: list[int] = dataclasses.field(compare=False)
    name: str = dataclasses.field(compare=True)
    points: list[int] = dataclasses.field(compare=False)
    position: T.Literal["GK", "DEF", "MID", "FWD"] = dataclasses.field(compare=True)
    price: int = dataclasses.field(compare=True)
    selected: list[int] = dataclasses.field(compare=False)
    team: str = dataclasses.field(compare=True)
    _xp: T.Optional[float] = dataclasses.field(default=None, compare=False)

    def xP(self) -> float:
        if self._xp is None:
            self._xp = statistics.mean(self.points) / self.upcoming_difficulty()
        return self._xp

    @property
    def tp(self) -> int:
        return sum(self.points)

    @property
    def tm(self) -> int:
        return sum(self.minutes)

    def upcoming_difficulty(self, n: int = 3) -> float:
        return sum(f.difficulty for f in self.fixutres[:n]) / (3 * n)
