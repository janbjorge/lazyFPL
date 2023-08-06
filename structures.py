import collections
import dataclasses
import datetime
import itertools
import statistics
import typing as T

import pydantic

import conf
import database


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
    position: database.POSITIONS = dataclasses.field(compare=False)
    price: int = dataclasses.field(compare=False)
    team: str = dataclasses.field(compare=False)
    webname: str = dataclasses.field(compare=True)
    xP: float = 0.0

    def tp(self, session: database.SESSIONS = database.CURRENT_SESSION) -> int:
        return sum(f.points or 0 for f in self.fixutres if f.session == session)

    def mtm(self, last: int = 5) -> float:
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
        upcoming = [f for f in self.fixutres if f.upcoming][: conf.env.lookahead]
        return sum(f.relative.combined for f in upcoming)

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
            f"{self.xP:<6.2f} {self.price:<6.1f} {self.tp():<4} "
            f"{self.upcoming_difficulty():<8.2f} {self.team:<15} "
            f"{self.position:<9} {self.webname:<20} "
            f"{self.news}"
        )


class Squad:
    def __init__(self, players: T.Sequence[Player]):
        self.players = players
        # self.bis = bis or helpers.best_lineup(self.players)
        # self.oxP = oxP or helpers.overall_xP(self.players)
        # self.sscore = sscore or helpers.sscore(self.players)

    def price(self) -> int:
        return sum(p.price for p in self.players)

    def valid_squad(
        self, gkps: int = 2, defs: int = 5, mids: int = 5, fwds: int = 3
    ) -> bool:
        cnt = collections.Counter(p.position for p in self.players)
        return (
            cnt["GKP"] == gkps
            and cnt["DEF"] == defs
            and cnt["MID"] == mids
            and cnt["FWD"] == fwds
        )

    def best_lineup(
        self,
        min_gkp: int = 1,
        min_def: int = 3,
        min_mid: int = 2,
        min_fwd: int = 1,
        size: int = 11,
    ) -> list[Player]:
        team = sorted(self.players, key=lambda x: x.xP, reverse=True)
        gkps = [p for p in team if p.position == "GKP"]
        defs = [p for p in team if p.position == "DEF"]
        mids = [p for p in team if p.position == "MID"]
        fwds = [p for p in team if p.position == "FWD"]
        best = gkps[:min_gkp] + defs[:min_def] + mids[:min_mid] + fwds[:min_fwd]
        remainder = sorted(
            defs[min_def:] + mids[min_mid:] + fwds[min_fwd:],
            key=lambda x: x.xP,
            reverse=True,
        )
        return best + remainder[: (size - len(best))]

    def SxP(self) -> float:
        # Squad xP
        return sum(p.xP for p in self.players)

    def LxP(self) -> float:
        # Lineup xP
        return sum(p.xP for p in self.best_lineup())

    def CxP(self) -> float:
        # Combined xP
        return (self.SxP() ** 2 + self.LxP() ** 2) ** 0.5

    def sscore(self, n: int = conf.env.lookahead) -> int:
        # "sscore -> "schedule score"
        # counts players in the lineup who plays in same match.
        # Ex. l'pool vs. man. city, and you team has Haaland and Salah as the only
        # players from the l'pool and city, the sscore is 2 since both play
        # the same match (assuming they start/play ofc.)

        per_gw = collections.defaultdict(list)
        for player in self.players:
            for i, nextopp in enumerate(player.upcoming_opponents()[:n]):
                per_gw[i].append((player.team, nextopp))

        score = 0
        for vs in per_gw.values():
            score += sum(vs.count(x[::-1]) for x in set(vs))
        return score

    def __iter__(self):
        yield from self.players

    def __len__(self) -> int:
        return len(self.players)

    def __str(self):
        pospri = {"GKP": 0, "DEF": 1, "MID": 2, "FWD": 3}
        yield f"Price: {self.price()/10} Size: {len(self.players)}"
        yield f"LxP: {self.LxP():.2f} SxP: {self.SxP():.2f} CxP: {self.CxP():.2f}"
        yield f"Schedule score: {self.sscore()}"
        for pos, players in itertools.groupby(
            sorted(
                self.players,
                key=lambda x: (pospri.get(x.position), x.xP),
                reverse=True,
            ),
            key=lambda x: x.position,
        ):
            yield f"\n{pos.upper()}"
            yield (
                "BIS  xP     Price  TP   UD       Team            Position  Player"
                + " " * 15
                + "News"
            )
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
