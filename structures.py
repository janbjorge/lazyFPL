import dataclasses
import datetime
import statistics
import typing as T

import pydantic

import helpers


@dataclasses.dataclass(frozen=True)
class Difficulty:
    attack: float
    defence: float
    overall: float

    @property
    def combined(self):
        return (self.attack**2 + self.defence**2 + self.overall**2) ** (1 / 2)


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
    fixutres: list[Fixture] = dataclasses.field(compare=False)
    name: str = dataclasses.field(compare=True)
    news: str = dataclasses.field(compare=True)
    position: T.Literal["GKP", "DEF", "MID", "FWD"] = dataclasses.field(compare=False)
    price: int = dataclasses.field(compare=False)
    team: str = dataclasses.field(compare=False)
    webname: str = dataclasses.field(compare=True)
    xP: float = 0.0

    @property
    def tp(self) -> int:
        return sum(
            f.points for f in self.fixutres if f.points and f.session == "2022-23"
        )

    @property
    def mtm(self) -> float:
        try:
            return statistics.mean(
                f.minutes for f in self.fixutres if f.session == "2022-23" and f.minutes
            )
        except statistics.StatisticsError:
            return 0.0

    def upcoming_difficulty(self) -> float:
        upcoming = [f for f in self.fixutres if f.upcoming][: helpers.lookahead()]
        return sum(f.relative.combined for f in upcoming)

    @property
    def next_opponent(self) -> str:
        return min(
            [f for f in self.fixutres if f.upcoming], key=lambda f: f.kickoff_time
        ).opponent

    def __str__(self):
        return (
            f"{self.xP:<6.2f} {self.price:<6.1f} {self.tp:<4} "
            f"{self.upcoming_difficulty():<8.2f} {self.team:<15} "
            f"{self.position:<9} {self.webname:<20} "
            f"{self.news}"
        )


class HistoricGame(pydantic.BaseModel):
    name: str
    position: T.Literal["GK", "DEF", "MID", "FWD", "GKP"]
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
