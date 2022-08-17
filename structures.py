import dataclasses
import datetime
import typing as T

import helpers


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
    opponent_trength_overall_away: int

    @property
    def ratio(self) -> float:
        if self.at_home:
            ad = self.team_strength_attack_home / self.opponent_strength_defence_away
            da = self.team_strength_defence_home / self.opponent_strength_attack_away
            oa = self.team_strength_overall_home / self.opponent_trength_overall_away
            return ad * da * oa
        else:
            ad = self.team_strength_attack_away / self.opponent_strength_defence_home
            da = self.team_strength_defence_away / self.opponent_strength_attack_home
            oa = self.team_strength_overall_away / self.opponent_strength_overall_home
            return ad * da * oa

    @property
    def adjusted_points(self) -> float:
        return self.points / self.ratio if self.points else 0.0


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
        backtrace = 3

        # Missing historical data for: {full_name}, setting xP=0,"
        if sum(not f.upcoming for f in self.fixutres) > backtrace:
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
        return sum(f.ratio for f in nfixutres)
