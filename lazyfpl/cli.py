import typer

app = typer.Typer(
    help="Tool for managing LazyFPL.",
    no_args_is_help=True,
)


@app.command()
def populate() -> None:
    """Populate the database with team data."""
    from lazyfpl import populator

    populator.main()


@app.command()
def train(
    epochs: int = typer.Option(
        5,
        help="Number of training epochs.",
    ),
    lr: float = typer.Option(
        0.01,
        help="Learning rate for the optimizer.",
    ),
    min_mtm: int = typer.Option(
        0,
        help="Minimum mean time metric for filtering players.",
    ),
    upsample: int = typer.Option(
        16,
        help="Factor for upsampling the training data.",
    ),
    batch_size: int = typer.Option(
        16,
        help="Batch size for training.",
    ),
    no_news: bool = typer.Option(
        False,
        help="Exclude players with news attached to them.",
    ),
) -> None:
    """Train the ML model on the populated data."""
    from lazyfpl import ml_model

    ml_model.main(
        epochs=epochs,
        lr=lr,
        min_mtm=min_mtm,
        upsample=upsample,
        batch_size=batch_size,
        no_news=no_news,
    )


@app.command()
def show(
    top: int = typer.Option(
        None,
        help="Top N players per position.",
    ),
    no_news: bool = typer.Option(
        False,
        help="Drop players with news attached to them.",
    ),
) -> None:
    """Show player database"""
    from lazyfpl import show

    show.main(top, no_news)


@app.command()
def transfer(
    add: list[str] = typer.Option(
        [],
        help="Players to add.",
    ),
    exclude: list[str] = typer.Option(
        [],
        help="Players to exclude.",
    ),
    max_transfers: int = typer.Option(
        ...,
        help="Maximum number of transfers allowed.",
    ),
    min_mtm: float = typer.Option(
        0.0,
        help="Minimum mean time metric.",
    ),
    min_xp: float = typer.Option(
        0.0,
        help="Minimum expected points.",
    ),
    no_news: bool = typer.Option(
        False,
        help="Exclude players with news attached to them.",
    ),
    remove: list[str] = typer.Option(
        [],
        help="Players to remove.",
    ),
) -> None:
    """Pick transfer options based on specified constraints."""
    from lazyfpl import transfer

    transfer.main(
        add,
        exclude,
        max_transfers,
        min_mtm,
        min_xp,
        no_news,
        remove,
    )


@app.command(name="lineup")
def lineup_optimizer(
    budget_lower: int = typer.Option(
        900,
        help="Lower budget limit.",
    ),
    budget_upper: int = typer.Option(
        1000,
        help="Upper budget limit.",
    ),
    gkp_def_not_same_team: bool = typer.Option(
        False,
        help="Goalkeeper and defenders should not be from the same team.",
    ),
    include: list[str] = typer.Option(
        [],
        help="Players to include in the lineup.",
    ),
    keep_squad: int = typer.Option(
        1000,
        help="Number of lineups to keep.",
    ),
    max_def_per_team: int = typer.Option(
        3,
        help="Maximum number of defenders per team.",
    ),
    max_players_per_team: int = typer.Option(
        3,
        help="Maximum number of players per team.",
    ),
    min_mtm: float = typer.Option(
        0.0,
        help="Minimum mean time metric.",
    ),
    min_xp: float = typer.Option(
        0.0,
        help="Minimum expected points.",
    ),
    no_news: bool = typer.Option(
        False,
        help="Exclude players with news attached to them.",
    ),
    remove: list[str] = typer.Option(
        [],
        help="Players to remove from consideration.",
    ),
    top_position_price: int = typer.Option(
        0,
        help="Top players per position by price.",
    ),
) -> None:
    """Optimize the best possible lineup within given constraints."""
    from lazyfpl import optimizer

    optimizer.main(
        budget_lower,
        budget_upper,
        gkp_def_not_same_team,
        include,
        keep_squad,
        max_def_per_team,
        max_players_per_team,
        min_mtm,
        min_xp,
        no_news,
        remove,
        top_position_price,
    )


@app.command()
def differential(
    min_mtm: float = typer.Option(
        0.0,
        help="Minimum mean time metric.",
    ),
    min_selected: int = typer.Option(
        1000,
        "-mc",
        help="Player must be selected by at least this amount of managers.",
    ),
    min_xp: float = typer.Option(
        0.0,
        help="Minimum expected points.",
    ),
    no_news: bool = typer.Option(
        False,
        help="Exclude players with news attached to them.",
    ),
    top: int = typer.Option(
        None,
        "-t",
        help="Top N players per position.",
    ),
) -> None:
    """Show differentials based on specified criteria."""
    from lazyfpl import differentials

    differentials.main(
        min_mtm,
        min_selected,
        min_xp,
        no_news,
        top,
    )


if __name__ == "__main__":
    app()
