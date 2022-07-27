import fetch

if __name__ == "__main__":
    print("xP       Price  TP   UD   Team            Position  Player")
    for p in fetch.players():
        print(
            f"{p.xP():<8.3f} {p.price:<6.1f} {p.tp:<4} "
            f"{p.upcoming_difficulty():<4.1f} {p.team:<15} "
            f"{p.position:<8}  {p.name}"
        )
