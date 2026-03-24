import random


class ConnectFourAIPlayer(ConnectFourPlayer):
    def __init__(self, model):
        self.model = model
    
    def get_move(self):
        valid_moves = self.model.get_valid_moves()
        # Pick the valid column closest to the center (column 3)
        center = 3
        for offset in range(7):
            for col in [center - offset, center + offset]:
                if 0 <= col <= 6 and valid_moves[col]:
                    return col

    # AI players return True
    def is_automated(self):
        return True

    def terminalTest(self, board):
        if self.model.check_for_winner(): # if someone won
            return True
        if self.model.check_for_draw(): # the board is full
            return True
        return False
