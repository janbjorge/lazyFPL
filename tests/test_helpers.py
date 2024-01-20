import pytest

from lazyfpl import helpers, structures

# Sample Player instances for testing with necessary attributes
player1 = structures.Player(
    fixutres=[],
    name="Player1",
    news="",
    position="GKP",
    price=25,
    selected=11,
    team="TeamA",
    team_short="TA",
    webname="Player1",
    xP=1.0,
)
player2 = structures.Player(
    fixutres=[],
    name="Player2",
    news="",
    position="DEF",
    price=50,
    selected=22,
    team="TeamA",
    team_short="TA",
    webname="Player2",
    xP=2.0,
)
player3 = structures.Player(
    fixutres=[],
    name="Player3",
    news="",
    position="MID",
    price=75,
    selected=33,
    team="TeamB",
    team_short="TB",
    webname="Player3",
    xP=3.0,
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
    xP=4.0,
)
lineup = [player1, player2, player3, player4]


@pytest.mark.parametrize(
    "lineup, expected_price",
    [
        (lineup, 250),
        ([], 0),
    ],
)
def test_squad_price(
    lineup: list[structures.Player],
    expected_price: int,
) -> None:
    assert helpers.squad_price(lineup) == expected_price


@pytest.mark.parametrize(
    "lineup, expected_xp",
    [
        (lineup, 10.0),
        ([], 0.0),
    ],
)
def test_squad_xP(
    lineup: list[structures.Player],
    expected_xp: float,
) -> None:
    assert helpers.squad_xP(lineup) == expected_xp


@pytest.mark.parametrize(
    "lineup, expected_overall_xp",
    [
        (lineup, pytest.approx(14.1421, 0.0001)),
        ([], 0.0),
    ],
)
def test_overall_xP(
    lineup: list[structures.Player],
    expected_overall_xp: float,
) -> None:
    assert pytest.approx(helpers.overall_xP(lineup)) == expected_overall_xp
