import random
from pprint import pprint

from hotbot.player import Player

from treys import Deck, Evaluator, Card

class Table:
    def __init__(self, smallblind=50, debug=False):
        self.players = {}
        self.smallblind = smallblind
        self.pots = []
        self.debug = debug
        self.rounds = 0
        self.table_finished = False
    
    def log(self, message, is_pprint=False):
        if self.debug:
            if not is_pprint:
                print(message)
            else:
                pprint(message)
    
    def add_player(self, player):
        self.players[player.id] = player
    
    def start_table(self):
        self.dealer_button = random.randint(0, 3)
        for _player in self.players:
            self.players[_player].reset_stacks()
    
    def get_next_player_pos_alive(self, start_pos):
        for _pos in range(4):
            cur_pos = (start_pos + _pos + 1) % 4
            if self.players[cur_pos].is_alive:
                return cur_pos
    
    def move_dealer_button(self):
        self.dealer_button = self.get_next_player_pos_alive(self.dealer_button)
        self.log(f"Dealer button position: {self.dealer_button}")

    def add_to_pots(self, player, amount):
        player.stack -= amount
        if len(self.pots) == 0:
            self.pots.append({
                "amount": amount,
                "players": {player: amount},
            })
        else:
            for _pot in self.pots:
                if player not in _pot["players"]:
                    _pot["players"][player] = min(amount, _pot["amount"])
                    amount -= min(amount, _pot["amount"])
                else:
                    if _pot["players"][player] < _pot["amount"]:
                        to_add = _pot["amount"] - _pot["players"][player]
                        _pot["players"][player] += min(to_add, amount)
                        amount -= min(to_add, amount)
                if amount == 0:
                    break
            
            if amount > 0:
                self.pots.append({
                    "amount": amount,
                    "players": {player: amount},
            })

    def pay_blinds(self):
        self.id_smallblind = self.get_next_player_pos_alive(self.dealer_button)
        self.id_bigblind = self.get_next_player_pos_alive(self.id_smallblind)

        self.can_bet_bigblind = min(self.players[self.id_bigblind].stack, self.smallblind * 2)
        self.can_bet_smallblind = min(self.players[self.id_smallblind].stack, self.smallblind)

        self.add_to_pots(self.players[self.id_smallblind], self.can_bet_smallblind)
        self.add_to_pots(self.players[self.id_bigblind], self.can_bet_bigblind)

    def get_obs(self, cur_player):
        # |n_alive|is_smallblind|is_bigblind|n_allin|n_spoken|n_tospeak|holecards...|stacks...|rebuys...
        obs = "|"
        obs += str(sum([self.players[_p].is_alive for _p in self.players])) + "|"
        obs += str(cur_player.id == self.id_smallblind) + "|"
        obs += str(cur_player.id == self.id_bigblind) + "|"
        obs += str(sum([self.actions[_p]["action"] == 1 for _p in self.actions])) + "|"
        obs += str(len(self.actions)) + "|"
        obs += str(sum([self.players[_p].is_alive for _p in self.players]) - len(self.actions)) + "|"
        obs += str(cur_player.cards[0]) + "|"
        obs += str(cur_player.cards[1]) + "|"
        for _p in self.players:
            if self.players[_p].is_alive:
                obs += str(self.players[_p].stack) + "|"
                obs += str(self.players[_p].rebuys) + "|"

        self.all_obs[cur_player.id] = {"obs":obs}

        return obs

    def get_actions(self):
        self.actions = {}
        cur_player_id = self.id_bigblind
        for _i in range(4):
            cur_player_id = self.get_next_player_pos_alive(cur_player_id)
            cur_player = self.players[cur_player_id]
            if cur_player in self.actions:
                break
            if cur_player.is_alive:
                obs = self.get_obs(cur_player)
                cur_action = cur_player.get_action(obs)
                if cur_action == 0 and cur_player.id == self.id_bigblind and cur_player.stack == 0:
                    cur_action = 1
                    cur_amount = self.can_bet_bigblind
                elif cur_action == 0 and cur_player.id == self.id_smallblind and cur_player.stack == 0:
                    cur_action = 1
                    cur_amount = self.can_bet_smallblind
                elif cur_action == 1:
                    cur_amount = cur_player.stack
                    self.add_to_pots(cur_player, cur_amount)
                elif cur_action == 0:
                    cur_amount = 0
                self.actions[cur_player] = {
                    "action" : cur_action,
                    "amount" : cur_amount
                }
                self.all_obs[cur_player.id]["action"] = cur_action
                str_action = "ALLIN" if cur_action else "FOLD"
                self.log(f"Player {cur_player.id} action: {str_action} for {cur_amount}")

    def resolve_round(self):
        self.evaluator = Evaluator()
        total_wins = {}
        if sum([self.actions[_a]["action"] for _a in self.actions]) == 0:
            total_pot = 0
            for _pot in self.pots:
                total_pot += sum([_pot["players"][_p] for _p in _pot["players"]])
            self.players[self.id_bigblind].stack += total_pot
        else:
            for _pot in self.pots:
                cur_players_in_pot = [_p for _p in _pot["players"] if self.actions[_p]["action"] == 1]
                hand_strengths = [(player, self.evaluator.evaluate(player.cards, self.communitycards)) for player in cur_players_in_pot]
                winner = min(hand_strengths, key=lambda x: x[1])[0]
                winner.stack += sum(_pot["players"][_p] for _p in _pot["players"])
                if winner not in total_wins:
                    total_wins[winner.id] = sum(_pot["players"][_p] for _p in _pot["players"])
                else:
                    total_wins[winner.id] += sum(_pot["players"][_p] for _p in _pot["players"])
        
        self.log(total_wins, is_pprint=True)
        for _player in self.players:
            if self.players[_player].is_learning and self.players[_player].is_alive:
                if _player in total_wins:
                    self.players[_player].update_q_table(
                        state = self.all_obs[_player]["obs"],
                        action = self.all_obs[_player]["action"],
                        reward = 1#total_wins[_player]/1000,
                    )
                else:
                    self.players[_player].update_q_table(
                        state = self.all_obs[_player]["obs"],
                        action = self.all_obs[_player]["action"],
                        reward = -2#(self.players[_player].stack - self.players[_player].previous_stack)*2/1000,
                    )

    def deal_holecards(self):
        for _p in self.players:
            if self.players[_p].is_alive:
                self.players[_p].cards = self.deck.draw(2)

    def deal_communitycards(self):
        self.communitycards = self.deck.draw(5)

    def end_round_checks(self):
        for _p in self.players:
            cur_player = self.players[_p]
            if cur_player.stack == 0:
                if cur_player.rebuys > 0:
                    cur_player.rebuy()
                else:
                    cur_player.is_alive = False
                    self.log(f"Player {cur_player.id} lost")
        if sum([self.players[_p].is_alive for _p in self.players]) == 1:
            self.table_finished = True
            winner = [self.players[_p].id for _p in self.players if self.players[_p].is_alive][0]
            self.log(f"TABLE WINNER: {winner} in {self.rounds} rounds!")
            self.players[winner].wins += 1
        for _p in self.players:
            self.players[_p].previous_stack = self.players[_p].stack
    
    def new_round(self):
        self.all_obs = {}
        self.pots = []
        self.actions = {}
        self.deck = Deck()
        self.deck.shuffle()
        self.communitycards = []
        self.rounds += 1
        if self.rounds % 5 == 0:
            self.smallblind *= 2
        log_players_alive = {self.players[_p].id: [self.players[_p].is_alive, self.players[_p].stack, self.players[_p].rebuys] for _p in self.players if self.players[_p].is_alive}
        self.log(f"   *** NEW ROUND ({self.rounds}) ***")
        self.log(f"Players:")
        self.log(log_players_alive, is_pprint=True)
        self.move_dealer_button()
        self.pay_blinds()
        self.deal_holecards()
        self.get_actions()
        self.deal_communitycards()
        self.resolve_round()
        self.end_round_checks()

    def start_tournament(self):
        while not self.table_finished:
            self.new_round()