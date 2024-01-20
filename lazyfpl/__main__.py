def help_message() -> None:
    print(
        """
    LazyFPL - Fantasy Premier League Team Optimizer - Win at FPL with Laziness

    - Constraints Module
        Contains functions to check various constraints like team composition
        and budget limits.

    - Database Module
        Manages interactions with the database, including queries and data storage.

    - Fetch Module
        Retrieves various types of data related to players, teams, and games.

    - Helpers Module
        Provides utility functions for calculations and data manipulations.

    - Populator Module
        Responsible for populating the database with current and historical FPL data.

    - Structures Module
        Defines data structures and models for representing players, teams, and games.

    - Transfer Modulee
        Assists in making transfer decisions based on various strategies
        and constraints.

    - Differentials Module
        Offers analytics to identify potential differential picks in
        your fantasy football team.

    Usage:
        Each module is designed to be used as a standalone tool or in conjunction
    with others to enhance your Fantasy Premier League strategy. Use the respective
    module's functions to fetch data, analyze team compositions, make
    transfers, and more.

    For more detailed information on each module, refer to their individual
    documentation or use help(module_name).
    """
    )


if __name__ == "__main__":
    help_message()
