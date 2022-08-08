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


@dataclasses.dataclass(eq=True, unsafe_hash=True)
class Player:
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
    _xp: T.Optional[float] = dataclasses.field(default=None, compare=False)

    def xP(self, n: int = 3) -> float:
        if not self.points:
            return 0
        if self._xp is None:
            self._xp = statistics.mean(self.points) / self.upcoming_difficulty(n=n)
        return self._xp

    @property
    def tp(self) -> int:
        return sum(self.points)

    @property
    def tm(self) -> int:
        return sum(self.minutes)

    def upcoming_difficulty(self, n: int = 3) -> float:
        return sum(f.difficulty for f in self.fixutres[:n]) / (3 * n)
