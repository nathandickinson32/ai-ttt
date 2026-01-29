import random

# -------------------------------------------------------
#  Board representation
# -------------------------------------------------------
# The board is a flat list of 9 cells (indices 0-8):
#
#   0 | 1 | 2
#   ---------
#   3 | 4 | 5
#   ---------
#   6 | 7 | 8
#
# Each cell is "" (empty), "X" (human), or "O" (AI).
# -------------------------------------------------------

# All possible three-in-a-row combinations.
WIN_COMBOS = [
    [0, 1, 2], [3, 4, 5], [6, 7, 8],  # rows
    [0, 3, 6], [1, 4, 7], [2, 5, 8],  # columns
    [0, 4, 8], [2, 4, 6],             # diagonals
]

board = [""] * 9      # current game state
game_over = False      # flag so we stop accepting moves
difficulty = "medium"  # "easy" | "medium" | "hard"

# --- Zoo theme tokens (display only, logic uses "X"/"O") ---
player_token = "\U0001f436"  # 🐶
ai_tokens = {
    "easy":   "\U0001f430",  # 🐰
    "medium": "\U0001f98a",  # 🦊
    "hard":   "\U0001f981",  # 🦁
}


def ai_token():
    """Return the emoji token for the current AI difficulty."""
    return ai_tokens.get(difficulty, "\U0001f98a")


def reset():
    """Clear the board and start a new game."""
    global board, game_over
    board = [""] * 9
    game_over = False


def available_moves(b):
    """Return indices of all empty cells on board *b*."""
    return [i for i in range(9) if b[i] == ""]


def check_winner(b):
    """Return 'X', 'O', or None depending on who (if anyone) has won."""
    for combo in WIN_COMBOS:
        a, c, e = combo
        if b[a] and b[a] == b[c] == b[e]:
            return b[a]
    return None


def is_draw(b):
    """True when every cell is filled and nobody has won."""
    return all(cell != "" for cell in b) and check_winner(b) is None


def winning_cells(b):
    """Return the list of cell indices that form the winning line, or []."""
    for combo in WIN_COMBOS:
        a, c, e = combo
        if b[a] and b[a] == b[c] == b[e]:
            return combo
    return []


# -------------------------------------------------------
#  Minimax algorithm
# -------------------------------------------------------

def minimax(b, depth, is_maximising):
    """
    Recursively evaluate every possible game state.

    Parameters
    ----------
    b : list[str]
        The current board state (may be a future hypothetical state).
    depth : int
        How many moves deep we are in the search tree.
    is_maximising : bool
        True when it is O's turn (AI), False for X (human).

    Returns
    -------
    int
        The best score reachable from this state.
    """
    winner = check_winner(b)

    # --- Base cases (leaf nodes of the game tree) ---
    if winner == "O":
        return 10 - depth
    if winner == "X":
        return depth - 10
    if is_draw(b):
        return 0

    if is_maximising:
        best = -100
        for move in available_moves(b):
            b[move] = "O"
            score = minimax(b, depth + 1, False)
            b[move] = ""
            best = max(best, score)
        return best
    else:
        best = 100
        for move in available_moves(b):
            b[move] = "X"
            score = minimax(b, depth + 1, True)
            b[move] = ""
            best = min(best, score)
        return best


def best_move_minimax(b):
    """
    Choose the optimal cell for O by scoring every available
    move with minimax and returning the one with the highest score.
    """
    best_score = -100
    move = None
    for i in available_moves(b):
        b[i] = "O"
        score = minimax(b, 0, False)
        b[i] = ""
        if score > best_score:
            best_score = score
            move = i
    return move


# -------------------------------------------------------
#  AI move dispatcher (difficulty levels)
# -------------------------------------------------------

def ai_move():
    """
    Pick a cell for the AI based on the current difficulty setting.

    - easy:   purely random among available cells.
    - medium: uses minimax 60 % of the time, random otherwise.
    - hard:   always minimax (unbeatable).
    """
    global board, game_over
    moves = available_moves(board)
    if not moves or game_over:
        return -1

    if difficulty == "easy":
        choice = random.choice(moves)

    elif difficulty == "medium":
        if random.random() < 0.6:
            choice = best_move_minimax(board)
        else:
            choice = random.choice(moves)

    else:  # hard
        choice = best_move_minimax(board)

    board[choice] = "O"
    return choice


# -------------------------------------------------------
#  Human move handler (called from JavaScript)
# -------------------------------------------------------

def human_move(index):
    """
    Place an X in the given cell.

    Returns a dict consumed by the JS front-end:
      ok           - whether the move was accepted
      ai_cell      - where the AI placed its O (-1 if game ended)
      status       - "play", "win_x", "win_o", or "draw"
      win_cells    - indices of the winning line (if any)
      player_token - the player's emoji token
      ai_token     - the AI's emoji token for the current difficulty
    """
    global board, game_over

    if game_over or board[index] != "":
        return {"ok": False}

    board[index] = "X"

    base = {
        "player_token": player_token,
        "ai_token": ai_token(),
    }

    # Check if human just won or triggered a draw.
    if check_winner(board) == "X":
        game_over = True
        return {
            **base,
            "ok": True, "ai_cell": -1,
            "status": "win_x",
            "win_cells": winning_cells(board),
        }
    if is_draw(board):
        game_over = True
        return {
            **base,
            "ok": True, "ai_cell": -1,
            "status": "draw", "win_cells": [],
        }

    # AI responds.
    ai_cell = ai_move()

    if check_winner(board) == "O":
        game_over = True
        return {
            **base,
            "ok": True, "ai_cell": ai_cell,
            "status": "win_o",
            "win_cells": winning_cells(board),
        }
    if is_draw(board):
        game_over = True
        return {
            **base,
            "ok": True, "ai_cell": ai_cell,
            "status": "draw", "win_cells": [],
        }

    return {
        **base,
        "ok": True, "ai_cell": ai_cell,
        "status": "play", "win_cells": [],
    }
