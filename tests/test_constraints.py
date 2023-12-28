import pytest

from lazyfpl import constraints, structures

# def test_team_constraint(lineup: list[structures.Player], valid: bool):
#     ...


@pytest.mark.parametrize(
    "lineup, valid",
    (
        ([...], True),
        ([...], True),
        ([...], True),
    ),
)
def test_gkp_def_same_team(lineup: list[structures.Player], valid: bool):
    ...
    # assert constraints.gkp_def_same_team(lineup) == valid
