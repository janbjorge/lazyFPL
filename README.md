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

## Modules Overview

### `backevel`
The `backevel` module is designed to validate the accuracy of the model's predictions against real-world player performances. It serves as a critical tool for assessing the model's effectiveness, enabling users to understand and improve the predictive capability of the system. This module is especially useful for refining the model's algorithms to enhance its future forecasting accuracy.

### `conf`
The `conf` module is where users can customize the application's settings and parameters. This flexibility allows for personalization according to individual strategies and preferences. It's crucial for users who want to adapt the application's functionality to their unique play style or specific requirements in the FPL.

### `ml_model`
The `ml_model` module is at the core of the application. It uses machine learning algorithms to analyze historical data and predict future player performances. This predictive capability is what makes the application so powerful for FPL players, offering insights that can inform strategic decisions for team selections and transfers.

### `optimizer`
The `optimizer` module combines the insights from the `ml_model` with the constraints defined by the user to suggest the best possible team setups. It is a sophisticated tool that leverages both data-driven predictions and user-defined strategies to maximize the performance of an FPL team.

### `populator`
The `populator` module is responsible for filling the database with data from external sources. This module ensures that the database has comprehensive and up-to-date information, which is crucial for the accuracy of the model's predictions and the effectiveness of the optimizer.

### `transfer`
In the `transfer` module, users receive guidance on managing player transfers, influenced by the model's predictions and optimization algorithms. This module helps users make informed decisions about player transfers, combining data-driven insights with strategic planning for improved team performance.

## `differentials`
The differentials module is a specialized tool designed for the Fantasy Premier League Team Optimizer. It offers analytics to identify potential differential picks in your fantasy football team. Differential picks are players who are not widely selected by other managers but have the potential to score high points, thereby giving you an edge in the competition.

## Command Line Interface (CLI) Usage
This application features a CLI, implemented via `argparse`, for straightforward interaction and execution. Below are command examples for key operations:

```bash
# Builds local player database.
python3 -m lazyfpl.populator

# Train ml-model (used to estimate expected points per player).
python3 -m lazyfpl.ml_model

# Backeval the model (optional).
python3 -m lazyfpl.backevel

# Optimize team selection based on various criteria.
python3 -m lazyfpl.optimizer --no-news --min-mtm 60
```

Obs! Step 1 and 2 must be run every gameweek to optain any new data.


## optimizer
Summary of lazyfpl.optimizer Command Output

The lazyfpl.optimizer command, with the parameters --no-news --min-mtm 60 --include Salah Haaland Alexander-Arnold, generated several team combinations for the Fantasy Premier League, focusing on optimizing the team with specific constraints and player inclusions.

- Key Players Included: The optimization specifically included Mohamed Salah, Erling Haaland, and Trent Alexander-Arnold, key players known for their high impact in FPL.
- Player Analysis: The output provided detailed analytics on various players, including expected points (xP), price, total points (TP), and upcoming matches. Notably, Erling Haaland was mentioned with a foot injury and a 50% chance of playing.
- Team Statistics: The command calculated different metrics like 'Price', 'Size', 'LxP' (Likely points), 'SxP' (Scheduled points), and 'CxP' (Combined points), providing a comprehensive overview of the team's potential performance.
- Optimization Results: The optimizer assessed numerous combinations of goalkeepers, defenders, midfielders, and forwards, totaling an astronomical number of potential team setups (in the range of 4.4e+15).
- Team Performance Scores: The summary includes schedule scores, team scores, and total scores (TSscore), indicating the balance between the team's schedule, individual player performance, and overall team synergy.

This summary provides a snapshot of the optimizer's output, showcasing its capabilities in assessing player performances, predicting future outputs, and suggesting optimal team configurations based on the given parameters

```python
Price: 99.4 Size: 15
LxP: 215.2 SxP: 277.7 CxP: 351.3
Schedule score: 15 Team score: 14 TSscore: 20.52
BIS  xP     Price  TP   UD       Team            Position  Player               Upcoming                              News
X    20.9   57.0   65   -0.2     Wolves          FWD       Cunha                Chelsea - Brentford - Everton 
X    19.7   76.0   58   0.6      Newcastle       FWD       Isak                 Luton - Nott'm Forest - Liverpool 
X    17.5   139.0  112  0.9      Man City        FWD       Haaland              Everton - Sheffield Utd - Newcastle Foot injury - 50% chance of playing
X    18.4   49.0   36   -0.2     Fulham          MID       Cairney              Burnley - Bournemouth - Arsenal 
X    16.9   76.0   71   0.9      Man City        MID       Foden                Everton - Sheffield Utd - Newcastle 
     16.1   132.0  127  0.1      Liverpool       MID       Salah                Arsenal - Burnley - Newcastle 
     15.8   57.0   50   -0.5     Nott'm Forest   MID       Gibbs-White          Bournemouth - Newcastle - Man Utd 
     14.7   50.0   42   -0.2     Fulham          MID       J.Palhinha           Burnley - Bournemouth - Arsenal 
X    31.1   43.0   22   -0.2     Fulham          DEF       Tosin                Burnley - Bournemouth - Arsenal 
X    20.6   44.0   45   -0.1     Bournemouth     DEF       Senesi               Nott'm Forest - Fulham - Spurs 
X    18.2   82.0   75   0.1      Liverpool       DEF       Alexander-Arnold     Arsenal - Burnley - Newcastle 
X    17.9   44.0   38   -0.5     Nott'm Forest   DEF       Toffolo              Bournemouth - Newcastle - Man Utd 
X    17.9   44.0   23   0.2      Aston Villa     DEF       Diego Carlos         Sheffield Utd - Man Utd - Burnley 
X    16.1   46.0   57   -0.1     Bournemouth     GKP       Neto                 Nott'm Forest - Fulham - Spurs 
     15.9   55.0   46   0.9      Man City        GKP       Ederson M.           Everton - Sheffield Utd - Newcastle 

Price: 99.7 Size: 15
LxP: 215.2 SxP: 278.0 CxP: 351.6
Schedule score: 15 Team score: 14 TSscore: 20.52
BIS  xP     Price  TP   UD       Team            Position  Player               Upcoming                              News
X    20.9   57.0   65   -0.2     Wolves          FWD       Cunha                Chelsea - Brentford - Everton 
X    19.7   76.0   58   0.6      Newcastle       FWD       Isak                 Luton - Nott'm Forest - Liverpool 
X    17.5   139.0  112  0.9      Man City        FWD       Haaland              Everton - Sheffield Utd - Newcastle Foot injury - 50% chance of playing
X    18.4   49.0   36   -0.2     Fulham          MID       Cairney              Burnley - Bournemouth - Arsenal 
X    16.9   76.0   71   0.9      Man City        MID       Foden                Everton - Sheffield Utd - Newcastle 
     16.1   132.0  127  0.1      Liverpool       MID       Salah                Arsenal - Burnley - Newcastle 
     15.8   57.0   50   -0.5     Nott'm Forest   MID       Gibbs-White          Bournemouth - Newcastle - Man Utd 
     15.0   53.0   59   -0.2     Fulham          MID       Andreas              Burnley - Bournemouth - Arsenal 
X    31.1   43.0   22   -0.2     Fulham          DEF       Tosin                Burnley - Bournemouth - Arsenal 
X    20.6   44.0   45   -0.1     Bournemouth     DEF       Senesi               Nott'm Forest - Fulham - Spurs 
X    18.2   82.0   75   0.1      Liverpool       DEF       Alexander-Arnold     Arsenal - Burnley - Newcastle 
X    17.9   44.0   38   -0.5     Nott'm Forest   DEF       Toffolo              Bournemouth - Newcastle - Man Utd 
X    17.9   44.0   23   0.2      Aston Villa     DEF       Diego Carlos         Sheffield Utd - Man Utd - Burnley 
X    16.1   46.0   57   -0.1     Bournemouth     GKP       Neto                 Nott'm Forest - Fulham - Spurs 
     15.9   55.0   46   0.9      Man City        GKP       Ederson M.           Everton - Sheffield Utd - Newcastle 
```

## Acknowledgments

Special thanks to the maintainers of the [Fantasy-Premier-League](https://github.com/vaastav/Fantasy-Premier-League) library. This invaluable resource has been instrumental in providing comprehensive and up-to-date FPL player statistics, game-week specific data, and historical performance records. Their dedication to maintaining and updating this library plays a crucial role in enhancing the capabilities of our "Fantasy Premier League Team Optimizer" and the FPL community at large. Your efforts are greatly appreciated!