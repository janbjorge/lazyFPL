import fetch

if __name__ == "__main__":
    print(
        "xP     Price  TP   UD       Team            Position  Player"
        + " " * 15
        + "News"
    )
    for p in sorted(fetch.players(), key=lambda x: x.xP):
        print(
            f"{p.xP:<6.2f} {p.price:<6.1f} {p.tp():<4} "
            f"{p.upcoming_difficulty():<8.2f} {p.team:<15} "
            f"{p.position:<9} {p.webname:<20} "
            f"{p.news}"
        )
