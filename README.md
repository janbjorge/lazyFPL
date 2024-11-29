<p align="center">
  <a href="https://pypi.python.org/pypi/lazyfpl"><img src="https://github.com/janbjorge/lazyFPL/blob/main/logo.png?raw=true" alt="lazyFPL"></a>
</p>

<p align="center">
    <em>Fantasy Premier League Team Optimizer - Win at FPL with Laziness</em>
</p>

<p align="center">
<a href="https://github.com/astral-sh/ruff" target="_blank">
    <img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json" alt="Package version">
</a>
<a href="https://pypi.python.org/pypi/lazyfpl" target="_blank">
    <img src="https://img.shields.io/pypi/v/lazyfpl.svg" alt="Package version">
</a>
<a href="https://pypi.python.org/pypi/lazyfpl" target="_blank">
    <img src="https://img.shields.io/pypi/pyversions/lazyfpl.svg" alt="Package version">
</a>
<a href="https://pypi.python.org/pypi/lazyfpl" target="_blank">
    <img src="https://img.shields.io/pypi/l/lazyfpl.svg" alt="Supported Python versions">
</a>
</p>

#
The _Fantasy Premier League Team Optimizer_ employs data-driven methods for analyzing and optimizing Fantasy Premier League (FPL) team selections. It is an essential tool for FPL players who wish to leverage statistical models and optimization algorithms for a competitive advantage.

## Why Model Training is Essential
In this application, training a machine learning model is critical as it allows for nuanced understanding and prediction of FPL player performances. By analyzing historical data, the model identifies patterns and trends, offering forecasts about future player performances. These predictions are invaluable for strategic team selection and transfer decisions, providing users with a significant edge in the game.

# Modules Overview
Each module in this application contributes a specific functionality to the overall performance of the Fantasy Premier League Team Optimizer, ensuring a comprehensive and efficient experience for users.

## `backevel`
The `backevel` module is designed to validate the accuracy of the model's predictions against real-world player performances. It serves as a critical tool for assessing the model's effectiveness, enabling users to understand and improve the predictive capability of the system. This module is especially useful for refining the model's algorithms to enhance its future forecasting accuracy.

## `conf`
The `conf` module is where users can customize the application's settings and parameters. This flexibility allows for personalization according to individual strategies and preferences. It's crucial for users who want to adapt the application's functionality to their unique play style or specific requirements in the FPL.

## `ml_model`
The `ml_model` module is at the core of the application. It uses machine learning algorithms to analyze historical data and predict future player performances. This predictive capability is what makes the application so powerful for FPL players, offering insights that can inform strategic decisions for team selections and transfers.

## `optimizer`
The `optimizer` module combines the insights from the `ml_model` with the constraints defined by the user to suggest the best possible team setups. It is a sophisticated tool that leverages both data-driven predictions and user-defined strategies to maximize the performance of an FPL team.

## `populator`
The `populator` module is responsible for filling the database with data from external sources. This module ensures that the database has comprehensive and up-to-date information, which is crucial for the accuracy of the model's predictions and the effectiveness of the optimizer.

## `transfer`
In the `transfer` module, users receive guidance on managing player transfers, influenced by the model's predictions and optimization algorithms. This module helps users make informed decisions about player transfers, combining data-driven insights with strategic planning for improved team performance.

## `differentials`
The `differentials` module is a specialized tool designed for the Fantasy Premier League Team Optimizer. It offers analytics to identify potential differential picks in your fantasy football team. Differential picks are players who are not widely selected by other managers but have the potential to score high points, thereby giving you an edge in the competition.

## Command Line Interface (CLI) Usage
The application features a CLI implemented via `typer`, allowing for a more intuitive and flexible interaction. Below are command examples for key operations:

```bash
# Populate the database with team data.
fpl

# Train the ML model on the populated data with default training parameters.
fpl train

# Train the ML model with custom parameters.
fpl train --epochs 10 --lr 0.005 --min-mtm 70 --upsample 20 --batch-size 32

# Show the player database.
fpl show --top 5 --no-news

# Pick transfer options based on specified constraints.
fpl transfer 2 --add Salah Haaland --exclude Alexander-Arnold --min-mtm 65 --min-xp 7.0

# Optimize the best possible lineup based on given constraints.
fpl lineup --budget-lower 950 --include Haaland --max-players-per-team 2 --min-xp 6.5

# Show differentials based on specified criteria.
fpl differential --min-mtm 70 --min-selected 500 --min-xp 6.5 --top 3

# Validate the accuracy of the model's predictions.
fpl backeval

# Show the current team.
fpl team
```

Obs! Ensure to run the `populate` and `train` commands each gameweek to update the data and train the model on the latest statistics.

## optimizer
### Summary of `fpl lineup` Command Output
The `fpl lineup` command allows users to optimize their Fantasy Premier League lineup based on specified criteria. The output provides several optimized team combinations, considering key parameters such as budget, selected players, and expected points.

Key features:
- **Player Selection**: Specific players like Salah, Haaland, or Alexander-Arnold can be explicitly included or excluded based on the user's preferences.
- **Team Metrics**: The output contains analytics on each player, including expected points (xP), price, upcoming matches, and additional news like injuries or suspensions.
- **Optimization Scores**: Metrics like Likely points (LxP), Scheduled points (SxP), Combined points (CxP), and Schedule score indicate the potential performance of the chosen lineup.

This summary captures the key metrics and potential lineups, showcasing the power of the optimizer in assessing player performances and building optimal team configurations.

## Acknowledgments
Special thanks to the maintainers of the [Fantasy-Premier-League](https://github.com/vaastav/Fantasy-Premier-League) library. This invaluable resource has been instrumental in providing comprehensive and up-to-date FPL player statistics, game-week specific data, and historical performance records. Their dedication to maintaining and updating this library plays a crucial role in enhancing the capabilities of our "Fantasy Premier League Team Optimizer" and the FPL community at large. Your efforts are greatly appreciated!

