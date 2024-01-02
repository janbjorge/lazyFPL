from __future__ import annotations

import pytest

from lazyfpl import constraints, structures

# Sample Player instances for testing
player1 = structures.Player(
    fixutres=[],
    name="Player1",
    news="",
    position="GKP",
    price=100,
    selected=11,
    team="TeamA",
    team_short="TA",
    webname="Player1",
    xP=None,
)
player2 = structures.Player(
    fixutres=[],
    name="Player2",
    news="",
    position="DEF",
    price=100,
    selected=22,
    team="TeamA",
    team_short="TA",
    webname="Player2",
    xP=None,
)
player3 = structures.Player(
    fixutres=[],
    name="Player3",
    news="",
    position="MID",
    price=100,
    selected=33,
    team="TeamB",
    team_short="TB",
    webname="Player3",
    xP=None,
)
player4 = structures.Player(
    fixutres=[],
    name="Player4",
    news="",
    position="FWD",
    price=100,
    selected=44,
    team="TeamC",
    team_short="TC",
    webname="Player4",
    xP=None,
)


@pytest.mark.parametrize(
    "lineup, n, expected",
    [
        ([player1, player2, player3], 2, True),
        ([player1, player1, player3], 1, False),
    ],
)
def test_team_constraint(
    lineup: list[structures.Player],
    n: int,
    expected: bool,
) -> None:
    assert constraints.team_constraint(lineup, n) == expected


@pytest.mark.parametrize(
    "lineup, expected",
    [
        (
            [player1, player2, player3],
            True,
        ),
        (
            [player1, player3, player4],
            False,
        ),
    ],
)
def test_gkp_def_same_team(
    lineup: list[structures.Player],
    expected: bool,
) -> None:
    assert constraints.gkp_def_same_team(lineup) == expected
