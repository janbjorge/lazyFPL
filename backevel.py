import statistics
import sys

import numpy as np
import torch

import fetch
import ml_model

if __name__ == "__main__":
    pool = sorted(fetch.players(), key=lambda x: (x.team, x.name, x.webname))
    if sys.argv[1:]:
        pool = [p for p in pool if p.webname in sys.argv[1:] or p.team in sys.argv[1:]]

    lookahead = 1
    backtrace = 3
    backstep = 3
    err = list[float]()

    with torch.no_grad():
        for p in pool:
            try:
                net = ml_model.load(p)
            except ValueError:
                continue
            net.eval()
            print(f"{p.name}({p.webname}) - {p.position} - {p.team}")
            for n in range(backstep):
                fixutres = [f for f in p.fixutres if not f.upcoming][
                    -(backtrace + lookahead + n) : -(lookahead + n)
                ]
                inference = [ml_model.features(f) for f in fixutres]
                next_fixture = p.fixutres[p.fixutres.index(fixutres[-1]) + 1]
                inf = np.expand_dims(
                    np.stack(
                        [np.array(x, dtype=np.float32) for x in inference],
                        axis=0,
                    ).astype(np.float32),
                    axis=0,
                )
                xP = net(torch.from_numpy(inf)).detach().numpy()[0]
                e = next_fixture.points - xP
                print(
                    f"  xP: {xP:<6.2f} TP: {next_fixture.points:<6.2f} Err: {e:<6.2f}"
                )
                err.append(e**2)
            print()

    print(f"RMS: {statistics.mean(err)**0.5:.3f}")
