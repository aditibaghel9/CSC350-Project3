import random
import copy
import c4model
from c4players import ConnectFourPlayer

# --------------------------------------------------------------------------- #
#  Constants                                                                   #
# --------------------------------------------------------------------------- #
WIN_SCORE  =  1_000_000   # Score awarded for a terminal win
LOSS_SCORE = -1_000_000   # Score awarded for a terminal loss

# Column order to search: center-out (improves alpha-beta pruning efficiency)
COLUMN_ORDER = [3, 2, 4, 1, 5, 0, 6]


# --------------------------------------------------------------------------- #
#  Helper functions that operate on a raw board (list-of-columns)              #
# --------------------------------------------------------------------------- #

def _get_valid_moves(board):
    """Return list of columns that still have at least one empty cell."""
    return [col for col in range(c4model.NUMCOLS)
            if board[col][0] == c4model.EMPTY]


def _apply_move(board, col, player):
    """
    Return a NEW board (deep copy) with *player*'s token dropped in *col*.
    Does NOT mutate the original board.
    """
    new_board = copy.deepcopy(board)
    for row in range(c4model.NUMROWS - 1, -1, -1):
        if new_board[col][row] == c4model.EMPTY:
            new_board[col][row] = player
            break
    return new_board


def _check_winner(board):
    """
    Return the winning player number (1 or 2) if there is a winner,
    otherwise return -1.  Mirrors the logic in ConnectFourModel.
    """
    def four_in_a_row(a, b, c, d):
        return a != c4model.EMPTY and a == b == c == d

    R, C = c4model.NUMROWS, c4model.NUMCOLS

    # Horizontal
    for row in range(R):
        for col in range(C - 3):
            if four_in_a_row(board[col][row], board[col+1][row],
                              board[col+2][row], board[col+3][row]):
                return board[col][row]
    # Vertical
    for col in range(C):
        for row in range(R - 3):
            if four_in_a_row(board[col][row], board[col][row+1],
                              board[col][row+2], board[col][row+3]):
                return board[col][row]
    # Diagonal (positive slope)
    for col in range(C - 3):
        for row in range(R - 3):
            if four_in_a_row(board[col][row],   board[col+1][row+1],
                              board[col+2][row+2], board[col+3][row+3]):
                return board[col][row]
    # Diagonal (negative slope)
    for col in range(3, C):
        for row in range(R - 3):
            if four_in_a_row(board[col][row],   board[col-1][row+1],
                              board[col-2][row+2], board[col-3][row+3]):
                return board[col][row]

    return -1


def _is_draw(board):
    """Return True when every cell is filled."""
    return all(board[col][row] != c4model.EMPTY
               for col in range(c4model.NUMCOLS)
               for row in range(c4model.NUMROWS))


def _is_terminal(board):
    """Return True if the position is a win for either player or a draw."""
    return _check_winner(board) != -1 or _is_draw(board)


# --------------------------------------------------------------------------- #
#  Heuristic evaluation (used at the depth cut-off)                            #
# --------------------------------------------------------------------------- #

def _count_window(window, player):
    """
    Score a window of 4 cells for *player*.
    Rewards having 2 or 3 of our tokens with empty fillers;
    penalises the opponent having 3-in-a-window.
    """
    opponent = c4model.PLAYER2 if player == c4model.PLAYER1 else c4model.PLAYER1
    score = 0
    p_count  = window.count(player)
    opp_count = window.count(opponent)
    empty    = window.count(c4model.EMPTY)

    if p_count == 4:
        score += 100
    elif p_count == 3 and empty == 1:
        score += 5
    elif p_count == 2 and empty == 2:
        score += 2

    if opp_count == 3 and empty == 1:
        score -= 4        # Urgently block opponent's 3-in-a-row

    return score


def _heuristic(board, player):
    """
    Static evaluation of *board* from *player*'s perspective.
    Higher is better for *player*.
    """
    score = 0
    R, C = c4model.NUMROWS, c4model.NUMCOLS

    # Prefer centre column
    centre_col = [board[C // 2][r] for r in range(R)]
    score += centre_col.count(player) * 3

    # Horizontal windows
    for row in range(R):
        for col in range(C - 3):
            window = [board[col + k][row] for k in range(4)]
            score += _count_window(window, player)

    # Vertical windows
    for col in range(C):
        for row in range(R - 3):
            window = [board[col][row + k] for k in range(4)]
            score += _count_window(window, player)

    # Positive-slope diagonal windows
    for col in range(C - 3):
        for row in range(R - 3):
            window = [board[col + k][row + k] for k in range(4)]
            score += _count_window(window, player)

    # Negative-slope diagonal windows
    for col in range(3, C):
        for row in range(R - 3):
            window = [board[col - k][row + k] for k in range(4)]
            score += _count_window(window, player)

    return score


# --------------------------------------------------------------------------- #
#  Alpha-Beta Minimax                                                           #
# --------------------------------------------------------------------------- #

def _alphabeta(board, depth, alpha, beta, maximising_player, ai_player):
    """
    Minimax with alpha-beta pruning and a hard depth cut-off.

    Parameters
    ----------
    board              : current board state (list of columns)
    depth              : remaining search depth (stops when depth == 0)
    alpha              : best score the maximiser can guarantee so far
    beta               : best score the minimiser can guarantee so far
    maximising_player  : True  → it is the AI's turn (maximiser)
                         False → it is the opponent's turn (minimiser)
    ai_player          : the player number (1 or 2) for the AI

    Returns
    -------
    (score, column)  – best score and the column that achieves it.
    Column is None at leaf nodes (depth 0 or terminal).
    """
    opponent = c4model.PLAYER2 if ai_player == c4model.PLAYER1 else c4model.PLAYER1

    # ---- Terminal / depth cut-off ---------------------------------------- #
    if _is_terminal(board):
        winner = _check_winner(board)
        if winner == ai_player:
            return (WIN_SCORE, None)
        elif winner == opponent:
            return (LOSS_SCORE, None)
        else:                            # draw
            return (0, None)

    if depth == 0:                       # depth cut-off → use heuristic
        return (_heuristic(board, ai_player), None)

    # ---- Recursive search ------------------------------------------------- #
    valid_moves = [c for c in COLUMN_ORDER if c in _get_valid_moves(board)]

    if maximising_player:
        best_score = float('-inf')
        best_col   = valid_moves[0]
        current_player = ai_player

        for col in valid_moves:
            child = _apply_move(board, col, current_player)
            score, _ = _alphabeta(child, depth - 1, alpha, beta,
                                   False, ai_player)
            if score > best_score:
                best_score = score
                best_col   = col
            alpha = max(alpha, best_score)
            if alpha >= beta:
                break          # β cut-off

        return (best_score, best_col)

    else:   # minimising (opponent's turn)
        best_score = float('inf')
        best_col   = valid_moves[0]
        current_player = opponent

        for col in valid_moves:
            child = _apply_move(board, col, current_player)
            score, _ = _alphabeta(child, depth - 1, alpha, beta,
                                   True, ai_player)
            if score < best_score:
                best_score = score
                best_col   = col
            beta = min(beta, best_score)
            if alpha >= beta:
                break          # α cut-off

        return (best_score, best_col)


# --------------------------------------------------------------------------- #
#  Player class                                                                 #
# --------------------------------------------------------------------------- #

class ConnectFourAIPlayer(ConnectFourPlayer):
    """
    Connect Four AI using Minimax with Alpha-Beta pruning.

    Parameters
    ----------
    model     : ConnectFourModel instance
    max_depth : how many half-moves (plies) to look ahead.
                Higher = stronger but slower.
                Recommended range: 4–8.
                Depth 5 is a good balance for interactive play.
    """

    def __init__(self, model, max_depth=5):
        self.model     = model
        self.max_depth = max_depth   # ← THE DEPTH CUT-OFF

    # ---------------------------------------------------------------------- #

    def get_move(self):
        board      = self.model.get_grid()
        ai_player  = self.model.get_turn()

        _, best_col = _alphabeta(
            board,
            depth             = self.max_depth,
            alpha             = float('-inf'),
            beta              = float('inf'),
            maximising_player = True,
            ai_player         = ai_player,
        )

        # Safety fallback: if alphabeta somehow returns None, pick randomly
        if best_col is None or not self.model.get_valid_moves()[best_col]:
            valid = [c for c in range(c4model.NUMCOLS)
                     if self.model.get_valid_moves()[c]]
            best_col = random.choice(valid)

        return best_col

    def is_automated(self):
        return True

    # ---------------------------------------------------------------------- #
    # Legacy method kept for compatibility – no longer drives search          #
    # ---------------------------------------------------------------------- #

    def terminalTest(self, board):
        return _is_terminal(board)
