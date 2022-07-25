import statistics
import dataclasses
import typing as T

TEAM = T.Literal[
    "Arsenal",
    "Aston Villa",
    "Brentford",
    "Brighton",
    "Burnley",
    "Chelsea",
    "Crystal Palace",
    "Everton",
    "Fulham",
    "Leeds",
    "Leicester",
    "Liverpool",
    "Man City",
    "Man Utd",
    "Newcastle",
    "Norwich",
    "Sheffield Utd",
    "Southampton",
    "Spurs",
    "Watford",
    "West Brom",
    "West Ham",
    "Wolves",
]


@dataclasses.dataclass
class Player:
    minutes: list[int]
    name: str
    opponent: list[str]
    points: list[int]
    position: T.Literal["GK", "DEF", "MID", "FWD"]
    price: int
    selected: list[int]
    team: TEAM
    _xp: T.Optional[float] = None

    def xP(self, last_n: int = 0) -> float:
        if self._xp is None:
            self._xp = round(statistics.mean(self.points[-last_n:]), 1)
        return self._xp

    @property
    def tp(self) -> int:
        return sum(self.points)

    @property
    def tm(self) -> int:
        return sum(self.minutes)
