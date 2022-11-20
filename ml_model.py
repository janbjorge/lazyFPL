import torch

torch.set_printoptions(threshold=10_000)
from torch.utils.data import Dataset as TorchDataset, DataLoader as TorchDataLoader
import cache
import structures


class Net(torch.nn.Module):
    def __init__(self, sensors: int, lstm_hidden: int = 4) -> None:
        super().__init__()
        self.num_layers = 1
        self.lstm_hidden = lstm_hidden
        self.lstm = torch.nn.LSTM(
            input_size=sensors,
            hidden_size=lstm_hidden,
            batch_first=True,
            num_layers=self.num_layers,
        )
        self.linear = torch.nn.Linear(
            in_features=lstm_hidden,
            out_features=1,
        )

    def forward(self, x):
        batch_size = x.shape[0]
        h0 = torch.zeros(self.num_layers, batch_size, self.lstm_hidden).requires_grad_()
        c0 = torch.zeros(self.num_layers, batch_size, self.lstm_hidden).requires_grad_()

        _, (hn, _) = self.lstm(x, (h0, c0))

        out = self.linear(hn[0]).flatten()
        return out


class SequenceDataset(TorchDataset):
    def __init__(
        self,
        fixtures: list["structures.Fixture"],
        backtrace: int = 3,
    ) -> None:
        x, y = samples(fixtures, backtrace)
        self.x, self.y = torch.Tensor(x), torch.Tensor(y)

    def __len__(self):
        return self.x.shape[0]

    def __getitem__(self, idx: int):
        return self.x[idx], self.y[idx]


def samples(
    fixtures: list["structures.Fixture"],
    backtrace: int = 3,
) -> tuple[list[tuple[float, ...]], list[float]]:

    fixtures = sorted(fixtures, key=lambda x: x.kickoff_time)
    # time --->
    back = (backtrace + 2) ** 2
    train = [f for f in fixtures if not f.upcoming][-back:]

    assert len(train) >= backtrace
    targets = list[float]()
    coefficients = list[tuple[float, ...]]()

    while len(train) > backtrace:
        target = train.pop(-1)
        bt1, bt2, bt3 = train[-backtrace:]

        assert target.points is not None
        assert bt1.points is not None
        assert bt2.points is not None
        assert bt3.points is not None

        targets.append(target.points)
        coefficients.append(
            (
                bt1.at_home,
                bt2.at_home,
                bt3.at_home,
                bt1.points,
                bt2.points,
                bt3.points,
                bt1.team_strength_attack_home,
                bt1.team_strength_attack_away,
                bt1.team_strength_defence_home,
                bt1.team_strength_defence_away,
                bt1.team_strength_overall_home,
                bt1.team_strength_overall_away,
                bt1.opponent_strength_attack_home,
                bt1.opponent_strength_attack_away,
                bt1.opponent_strength_defence_home,
                bt1.opponent_strength_defence_away,
                bt1.opponent_strength_overall_home,
                bt1.opponent_strength_overall_away,
                bt2.team_strength_attack_home,
                bt2.team_strength_attack_away,
                bt2.team_strength_defence_home,
                bt2.team_strength_defence_away,
                bt2.team_strength_overall_home,
                bt2.team_strength_overall_away,
                bt2.opponent_strength_attack_home,
                bt2.opponent_strength_attack_away,
                bt2.opponent_strength_defence_home,
                bt2.opponent_strength_defence_away,
                bt2.opponent_strength_overall_home,
                bt2.opponent_strength_overall_away,
                bt3.team_strength_attack_home,
                bt3.team_strength_attack_away,
                bt3.team_strength_defence_home,
                bt3.team_strength_defence_away,
                bt3.team_strength_overall_home,
                bt3.team_strength_overall_away,
                bt3.opponent_strength_attack_home,
                bt3.opponent_strength_attack_away,
                bt3.opponent_strength_defence_home,
                bt3.opponent_strength_defence_away,
                bt3.opponent_strength_overall_home,
                bt3.opponent_strength_overall_away,
            )
        )

    return coefficients, targets


@cache.fcache
def train(player: "structures.Player"):
    # players = fetch.players()
    # player = [p for p in players if p.webname == "Salah"][0]
    # player = [p for p in players if p.webname == "Robertson"][0]
    # player = [p for p in players if p.webname == "Kane"][0]
    # player = [p for p in players if p.webname == "Haaland"][0]
    # print(player)
    ds = SequenceDataset(player.fixutres)
    loader = TorchDataLoader(
        ds,
        batch_size=4,
    )

    loss_function = torch.nn.MSELoss()
    net = Net(ds[0][0].shape[0])
    lr = 1e-2
    optimizer = torch.optim.Adam(net.parameters(), lr=lr)
    epchs = 500
    for epch in range(500):
        train_loss = 0
        bucket = 0
        out = 0
        for x, y in loader:
            x = x[None, :]
            x = x.permute(1, 0, 2)
            output = net(x)
            out += output.sum().detach().numpy()
            assert output.shape == y.shape
            loss = loss_function(output, y)
            optimizer.zero_grad()
            loss.backward()

            optimizer.step()
            train_loss += loss.detach().numpy()
            bucket += x.shape[0]

        # print(epch, round(epch / epchs * 100), train_loss, out / bucket)
    print(train_loss, out / bucket)
    # for name, pars in net.named_parameters():
    #     print(name, pars.shape)
    print("--- DONE ---")
    return net


if __name__ == "__main__":

    import fetch
    for player in fetch.players():
        print(player)
        try: 
            train(player)
        except Exception as e:
            print(e)
    # players = fetch.players()
    # for p in pla
    # player = [p for p in players if p.webname == "Salah"][0]
    # player = [p for p in players if p.webname == "Robertson"][0]
    # player = [p for p in players if p.webname == "Kane"][0]
    # player = [p for p in players if p.webname == "Haaland"][0]
    # print(player)
    # train(player)
