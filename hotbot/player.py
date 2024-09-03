import random
import numpy as np

class Player:
    def __init__(
            self,
            id,
            init_stack = 800,
            init_rebuys = 2,
            debug = False,
    ):
        self.id = id
        self.stack = init_stack
        self.init_stack = init_stack
        self.previous_stack = self.stack
        self.rebuys = init_rebuys
        self.init_rebuys = init_rebuys
        self.previous_rebuys = self.rebuys
        self.rebuy_amount = init_stack
        self.current_action = None
        self.previous_action = None
        self.hist_actions = []
        self.is_smallblind = False
        self.is_bigblind = False
        self.is_alive = True
        self.is_learning = False
        self.debug = debug
        self.wins = 0
        self.games = 0

    def log(self, message):
        if self.debug:
            print(message)

    def reset_stacks(self):
        self.stack = self.init_stack
        self.previous_stack = self.stack
        self.rebuys = self.init_rebuys
        self.previous_rebuys = self.rebuys
        self.rebuy_amount = self.init_stack
        self.current_action = None
        self.previous_action = None
        self.hist_actions = []
        self.is_smallblind = False
        self.is_bigblind = False
        self.is_alive = True
        self.games += 1

    def rebuy(self):
        self.rebuys -= 1
        self.stack += self.rebuy_amount
        self.log(f"Player {self.id} rebuys. Rebuys left: {self.rebuys}")
    
    def check_rebuy(self, small_blind):
        if self.stack <= small_blind:
            self.rebuy()

    def get_action_space(self):
        if self.stack > 0:
            return [0, 1]
        else:
            return [1]

class RandomPlayer(Player):
    def __init__(self, id, init_stack=800, init_rebuys=2, debug=False):
        super().__init__(id, init_stack, init_rebuys, debug)
    
    def get_action(self, obs=None):
        action_space = self.get_action_space()
        action = random.choice(action_space)
        self.previous_action = self.current_action
        self.current_action = action

        self.log(f"Player {self.id} action space: {action_space}... Choosing {action}")

        return self.current_action
    
class LearningAgent(Player):
    def __init__(self, id, init_stack=800, init_rebuys=2, debug=False):
        super().__init__(id, init_stack, init_rebuys, debug)

        self.q_table = {}  # This will be your Q-table
        self.alpha = 0.05   # Learning rate
        self.gamma = 0.95   # Discount factor
        self.epsilon = 0.3  # Exploration rate
        self.rewards = []
        self.game_finished = False
        self.wins = 0
        self.games = 0
        self.is_learning = True

    def get_action(self, obs):
        action_space = self.get_action_space()
        if len(action_space) == 1:
            self.previous_action = self.current_action
            self.current_action = action_space[0]

            self.log(f"Player {self.id} action space: {action_space}... Choosing {action_space[0]}")
            
            return self.current_action
        if obs not in self.q_table:
            self.q_table[obs] = np.zeros(2)
        action = np.argmax(self.q_table[obs]) if random.random() >= self.epsilon else random.choice(action_space)
        self.previous_action = self.current_action
        self.current_action = action

        self.log(f"Player {self.id} action space: {action_space}... Choosing {action}")

        # print(action_space, self.current_action)
        

        return self.current_action
    
    def update_q_table(self, state, action, reward):
        if state not in self.q_table:
            self.q_table[state] = np.zeros(2)
        best_future_q = np.max(self.q_table[state])
        self.q_table[state][action] = (1 - self.alpha) * self.q_table[state][action] + self.alpha * (reward + self.gamma * best_future_q)

    
# X = RandomPlayer(0, debug=True)
# X.get_action()
# X.get_action()
# X.stack=100
# X.check_rebuy(200)
