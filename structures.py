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
    price: list[int]
    selected: list[int]
    team: list[TEAM]
    _xp: T.Optional[float] = None

    @property
    def xP(self) -> float:
        if self._xp is None:
            self._xp = statistics.mean(self.points)
        return self._xp
