
# Fantasy Premier League Team Optimizer - Win at FPL with lazines
This Python project is designed to analyze and optimize Fantasy Premier League (FPL) team selections using data-driven techniques.

## Modules Overview

- `lazyfpl/backevel.py`: Back evaluation of player performance.
- `lazyfpl/conf.py`: Configuration settings.
- `lazyfpl/constraints.py`: Team selection constraints.
- `lazyfpl/database.py`: Database interactions.
- `lazyfpl/fetch.py`: Data fetching from FPL API.
- `lazyfpl/ml_model.py`: Machine learning model for player performance prediction.
- `lazyfpl/optimizer.py`: Team selection optimization.
- `lazyfpl/populator.py`: Data population from external sources.
- `lazyfpl/structures.py`: Data structures definition.
- `lazyfpl/transfer.py`: Management of player transfers.

## Basic Usage Examples

```bash
# Builds local player database.
python3 -m lazyfpl.populator

# Train ml-model (used to estiate expected points per player).
python3 -m lazyfpl.ml_model

# Backeval the model (optional).
python3 -m lazyfpl.backevel

# Based on upcoming fixture thufness, team synergy and expected points (from ML-model)
# show optimal team comparisons.
# This will exclude player with news and below mean-minutes played 60
python3 -m lazyfpl.optimizer --no-news --min-mtm 60
```
