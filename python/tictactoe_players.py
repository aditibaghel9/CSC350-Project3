import copy


class TicTacToeHumanPlayer:
    def __init__(self, model, symbol):
        self.model = model
        self.symbol = symbol

    def is_automated(self):
        return False

    def get_move(self):
        valid_input = False
        valid_moves = self.model.get_valid_moves()

        while not valid_input:
            try:
                move = int(input('Enter move (1-9): '))
                if move < 1 or move > 9:
                    raise ValueError()
                else:
                    valid_input = True

                if move in valid_moves:
                    return move
                else:
                    print('That spot is full. Pick again.')
                    valid_input = False
            except ValueError:
                print('Invalid input.')

        # Should not get here
        return -1


class TicTacToeAIPlayer:
    def __init__(self, model, symbol):
        self.model = model
        self.symbol = symbol

    def is_automated(self):
        return True

    # Assume actions are numbered 1-9
    def result(self, state, action):
        newstate = copy.deepcopy(state)
        turn = self._get_turn(state)

        action -= 1 # Adjustment of 1
        col = action % 3
        row = action // 3
        newstate[row][col] = turn

        return newstate

    def actions(self, state):
        moves = []
        for row in range(3):
            for col in range(3):
                if state[row][col] is None:
                    moves.append(row*3 + col + 1)
        return moves

    def terminal_test(self, state):
        for row in range(3):
            if state[row][0] is not None and state[row][0] == state[row][1] and state[row][0] == state[row][2]:
                return True
        for col in range(3):
            if state[0][col] is not None and state[0][col] == state[1][col] and state[0][col] == state[2][col]:
                return True
        if state[0][0] is not None and state[0][0] == state[1][1] and state[0][0] == state[2][2]:
            return True
        if state[2][0] is not None and state[2][0] == state[1][1] and state[2][0] == state[0][2]:
            return True

        return self._is_draw(state)

    def utility(self, state):
        if self._get_winner(state) == self.symbol:
            return 1000
        elif self._get_winner(state) is not None:
            return -1000
        if self._is_draw(state):
            return 0

        score = 0
        opponents = [s for s in ['X', 'O', '+'] if s != self.symbol]

        score += self._count_threats(state, self.symbol, 3) * 10
        score += self._count_threats(state, self.symbol, 2) * 3

        for opp in opponents:
            score -= self._count_threats(state, opp, 3) * 10
            score -= self._count_threats(state, opp, 2) * 3

        return score

        

    def _is_draw(self, state):
        all_filled = True
        for row in range(3):
            for col in range(3):
                if state[row][col] is None:
                    all_filled = False
        return all_filled

    def _get_winner(self, state):
        for row in range(3):
            if state[row][0] is not None and state[row][0] == state[row][1] and state[row][0] == state[row][2]:
                return state[row][0]
        for col in range(3):
            if state[0][col] is not None and state[0][col] == state[1][col] and state[0][col] == state[2][col]:
                return state[0][col]
        if state[0][0] is not None and state[0][0] == state[1][1] and state[0][0] == state[2][2]:
            return state[0][0]
        if state[2][0] is not None and state[2][0] == state[1][1] and state[2][0] == state[0][2]:
            return state[2][0]

        return None # Uh-oh

    def _get_turn(self, state):
        empties = 0
        for row in range(3):
            for col in range(3):
                if state[row][col] is None:
                    empties += 1

        if empties % 2 == 1:
            return 'X'
        else:
            return 'O'

    def get_move(self):
        state = self.model.get_grid()
        return self.alpha_beta_search(state)

    def alpha_beta_search(self, state):
        v= float('-inf')
        alpha = float('-inf')
        beta = float('inf')
        best_action = None
        best_value = float('-inf')
 
        for action in self.actions(state):
            action_value = self.min_value(self.result(state, action), alpha, beta, depth=1)
            if action_value > v:
                v=action_value
                best_action = action
            alpha = max(alpha, v)
 
        return best_action

    def max_value(self, state, alpha, beta, depth):
        if self.terminal_test(state) or depth >= self.max_depth:
            return self.utility(state, depth)
 
        v = float('-inf')
        for action in self.actions(state):
            v = max(v, self.min_value(self.result(state, action), alpha, beta, depth + 1))
            if v >= beta:
                return v          # Beta cut-off
            alpha = max(alpha, v)
        return v

    def min_value(self, state, alpha, beta, depth):
        """INSERT YOUR CODE HERE"""
        if self.terminal_test(state) or depth >= self.max_depth:
            return self.utility(state, depth)

        v = float('inf')
        for action in self.actions(state):
            v = min(v, self.max_value(self.result(state, action), alpha, beta, depth+1))
            if v <= alpha:
                return v          # Alpha cut-off
            beta = min(beta, v)
        return v
