"""Pytest test suite for Zoo Tic-Tac-Toe game logic."""

import game_logic as gl


# -------------------------------------------------------
#  Fixtures / helpers
# -------------------------------------------------------

def _reset():
    """Reset global game state between tests."""
    gl.board = [""] * 9
    gl.game_over = False
    gl.difficulty = "medium"
    gl.player_token = "\U0001f436"


def setup_function():
    _reset()


# For class-based tests, use a shared base with setup_method
class _ResetBase:
    def setup_method(self):
        _reset()


# -------------------------------------------------------
#  Board helpers
# -------------------------------------------------------

class TestAvailableMoves(_ResetBase):
    def test_empty_board(self):
        b = [""] * 9
        assert gl.available_moves(b) == list(range(9))

    def test_partially_filled(self):
        b = ["X", "", "O", "", "X", "", "", "O", ""]
        assert gl.available_moves(b) == [1, 3, 5, 6, 8]

    def test_full_board(self):
        b = ["X", "O", "X", "O", "X", "O", "O", "X", "O"]
        assert gl.available_moves(b) == []


class TestCheckWinner(_ResetBase):
    def test_no_winner_empty(self):
        assert gl.check_winner([""] * 9) is None

    def test_row_wins(self):
        for row_start in (0, 3, 6):
            for player in ("X", "O"):
                b = [""] * 9
                for i in range(3):
                    b[row_start + i] = player
                assert gl.check_winner(b) == player

    def test_col_wins(self):
        for col in (0, 1, 2):
            for player in ("X", "O"):
                b = [""] * 9
                for r in range(3):
                    b[col + r * 3] = player
                assert gl.check_winner(b) == player

    def test_diagonal_wins(self):
        for player in ("X", "O"):
            b = [""] * 9
            b[0] = b[4] = b[8] = player
            assert gl.check_winner(b) == player

            b = [""] * 9
            b[2] = b[4] = b[6] = player
            assert gl.check_winner(b) == player

    def test_no_winner_in_progress(self):
        b = ["X", "O", "", "", "X", "", "", "", ""]
        assert gl.check_winner(b) is None


class TestIsDraw(_ResetBase):
    def test_draw_on_full_board(self):
        b = ["X", "O", "X",
             "X", "O", "O",
             "O", "X", "X"]
        assert gl.check_winner(b) is None
        assert gl.is_draw(b) is True

    def test_no_draw_not_full(self):
        b = ["X", "O", "", "", "", "", "", "", ""]
        assert gl.is_draw(b) is False

    def test_no_draw_with_winner(self):
        b = ["X", "X", "X",
             "O", "O", "",
             "", "", ""]
        assert gl.is_draw(b) is False


class TestWinningCells(_ResetBase):
    def test_returns_winning_indices(self):
        b = ["X", "X", "X", "", "", "", "", "", ""]
        assert gl.winning_cells(b) == [0, 1, 2]

    def test_diagonal(self):
        b = ["O", "", "", "", "O", "", "", "", "O"]
        assert gl.winning_cells(b) == [0, 4, 8]

    def test_no_winner(self):
        assert gl.winning_cells([""] * 9) == []


# -------------------------------------------------------
#  Minimax correctness
# -------------------------------------------------------

class TestMinimax(_ResetBase):
    def test_ai_takes_winning_move(self):
        b = ["X", "X", "",
             "O", "O", "",
             "", "", ""]
        move = gl.best_move_minimax(b)
        assert move == 5  # O wins with row 2

    def test_ai_blocks_human_win(self):
        b = ["X", "X", "",
             "O", "", "",
             "", "", ""]
        move = gl.best_move_minimax(b)
        assert move == 2  # block X's top row

    def test_optimal_play_from_empty_always_draws(self):
        """If both sides play optimally, the game is a draw."""
        b = [""] * 9
        # AI goes first at center (optimal)
        b[4] = "O"
        # Simulate optimal play: human plays corner
        b[0] = "X"
        # From here, minimax should never lose
        score = gl.minimax(b, 0, True)
        assert score >= 0  # AI should at least draw

    def test_terminal_scores(self):
        # O wins immediately
        b = ["O", "O", "O", "", "", "", "", "", ""]
        assert gl.minimax(b, 0, False) == 10

        # X wins immediately
        b = ["X", "X", "X", "", "", "", "", "", ""]
        assert gl.minimax(b, 0, True) == -10

        # Draw
        b = ["X", "O", "X",
             "X", "O", "O",
             "O", "X", "X"]
        assert gl.minimax(b, 0, True) == 0


# -------------------------------------------------------
#  Difficulty levels
# -------------------------------------------------------

class TestDifficulty(_ResetBase):
    def test_easy_returns_valid_move(self):
        gl.difficulty = "easy"
        gl.board = ["X", "", "O", "", "", "", "", "", ""]
        move = gl.ai_move()
        assert move in gl.available_moves(["X", "", "O", "", "", "", "", "", ""])

    def test_medium_returns_valid_move(self):
        gl.difficulty = "medium"
        gl.board = ["X", "", "O", "", "", "", "", "", ""]
        move = gl.ai_move()
        assert move in [1, 3, 4, 5, 6, 7, 8]

    def test_hard_returns_optimal(self):
        gl.difficulty = "hard"
        gl.board = ["X", "X", "",
                    "O", "O", "",
                    "", "", ""]
        expected = gl.best_move_minimax(list(gl.board))
        move = gl.ai_move()
        assert move == expected


# -------------------------------------------------------
#  human_move integration
# -------------------------------------------------------

class TestHumanMove(_ResetBase):
    def test_rejects_occupied_cell(self):
        gl.board[0] = "X"
        result = gl.human_move(0)
        assert result["ok"] is False

    def test_rejects_when_game_over(self):
        gl.game_over = True
        result = gl.human_move(4)
        assert result["ok"] is False

    def test_human_win(self):
        gl.board = ["X", "X", "",
                    "O", "O", "",
                    "", "", ""]
        result = gl.human_move(2)
        assert result["ok"] is True
        assert result["status"] == "win_x"
        assert result["win_cells"] == [0, 1, 2]
        assert result["ai_cell"] == -1

    def test_returns_tokens(self):
        gl.difficulty = "hard"
        result = gl.human_move(0)
        assert result["ok"] is True
        assert result["player_token"] == "\U0001f436"
        assert result["ai_token"] == "\U0001f981"

    def test_ongoing_play(self):
        gl.difficulty = "hard"
        result = gl.human_move(0)
        assert result["ok"] is True
        assert result["status"] in ("play", "win_o", "draw")
        if result["status"] == "play":
            assert result["ai_cell"] >= 0

    def test_draw(self):
        # Set up board one move from draw, no winner possible
        gl.board = ["X", "O", "X",
                    "X", "O", "O",
                    "O", "X", ""]
        result = gl.human_move(8)
        assert result["ok"] is True
        assert result["status"] == "draw"

    def test_ai_win(self):
        # Set up so human move lets AI win
        gl.difficulty = "hard"
        gl.board = ["X", "X", "O",
                    "", "O", "",
                    "", "", ""]
        # AI has O at 2,4 — needs 6 to win diagonal
        result = gl.human_move(3)  # human plays 3
        if result["status"] == "win_o":
            assert result["ai_cell"] == 6
            assert 2 in result["win_cells"]
            assert 4 in result["win_cells"]
            assert 6 in result["win_cells"]


# -------------------------------------------------------
#  Reset
# -------------------------------------------------------

class TestReset(_ResetBase):
    def test_clears_board(self):
        gl.board = ["X", "O", "X", "O", "X", "O", "O", "X", "O"]
        gl.game_over = True
        gl.reset()
        assert gl.board == [""] * 9
        assert gl.game_over is False


# -------------------------------------------------------
#  Token helpers
# -------------------------------------------------------

class TestTokens(_ResetBase):
    def test_ai_token_easy(self):
        gl.difficulty = "easy"
        assert gl.ai_token() == "\U0001f430"

    def test_ai_token_medium(self):
        gl.difficulty = "medium"
        assert gl.ai_token() == "\U0001f98a"

    def test_ai_token_hard(self):
        gl.difficulty = "hard"
        assert gl.ai_token() == "\U0001f981"
