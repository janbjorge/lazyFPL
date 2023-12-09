
# Fantasy Premier League Team Optimizer - Win at FPL with lazines
This Python project is designed to analyze and optimize Fantasy Premier League (FPL) team selections using data-driven techniques.

## Modules Overview

- `backevel.py`: Back evaluation of player performance.
- `conf.py`: Configuration settings.
- `constraints.py`: Team selection constraints.
- `database.py`: Database interactions.
- `fetch.py`: Data fetching from FPL API.
- `ml_model.py`: Machine learning model for player performance prediction.
- `optimizer.py`: Team selection optimization.
- `populator.py`: Data population from external sources.
- `structures.py`: Data structures definition.
- `transfer.py`: Management of player transfers.

## Basic Usage Examples

```bash
# Builds local player database.
python3 populator.py

# Train ml-model (used to estiate expected points per player).
python3 ml_model.p

# Backeval the model (optional).
python3 backevel.py

# Based on upcoming fixture thufness, team synergy and expected points (from ML-model)
# show optimal team comparisons.
# This will exclude player with news and below mean-minutes played 60
python3 optimizer.py --no-news --min-mtm 60
```
