from hotbot.player import Player, RandomPlayer, LearningAgent
from hotbot.table import Table

P0 = LearningAgent(0)
P1 = RandomPlayer(1)
P2 = RandomPlayer(2)
P3 = RandomPlayer(3)

for _i in range(1000):
    try:
        self = Table(debug=False)

        self.add_player(P0)
        self.add_player(P1)
        self.add_player(P2)
        self.add_player(P3)

        self.start_table()
        self.start_tournament()

        # n_states = len(P0.q_table)
        # print(f"Learning agent number of states: {n_states}")

        win_pct = round(P0.wins / P0.games * 100)
        print(f"win rate {win_pct}")

    except:
        pass


P0.wins = 0
P0.games = 0

for _i in range(1000):
    try:
        self = Table(debug=False)

        self.add_player(P0)
        self.add_player(P1)
        self.add_player(P2)
        self.add_player(P3)

        self.start_table()
        self.start_tournament()

        # n_states = len(P0.q_table)
        # print(f"Learning agent number of states: {n_states}")

        win_pct = round(P0.wins / P0.games * 100)
        print(f"win rate {win_pct}")

    except Exception as e:
        print(e)
        pass


[self.players[_p].stack for _p in self.players]
[self.players[_p].rebuys for _p in self.players]