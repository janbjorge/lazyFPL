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


@dataclasses.dataclass
class Player:
    fixutres: tuple[Fixture, ...]
    minutes: list[int]
    name: str
    points: list[int]
    position: T.Literal["GK", "DEF", "MID", "FWD"]
    price: int
    selected: list[int]
    team: str
    _xp: T.Optional[float] = None

    def xP(self) -> float:
        if self._xp is None:
            self._xp = round(
                statistics.mean(self.points) / self.upcoming_difficulty(),
                2,
            )
        return self._xp

    @property
    def tp(self) -> int:
        return sum(self.points)

    @property
    def tm(self) -> int:
        return sum(self.minutes)

    def upcoming_difficulty(self, n: int = 3) -> int:
        return sum(f.difficulty for f in self.fixutres[:n])
