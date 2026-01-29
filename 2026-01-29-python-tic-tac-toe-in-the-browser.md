---
layout: post
title: "Build a Zoo Tic-Tac-Toe AI in Python — Running Entirely in the Browser"
date: 2026-01-29
tags: [python, minimax, ai, pyodide, webassembly]
---

Most Python programs need a server, but what if you could run Python directly in
the browser — no backend at all? In this post we build a fully playable
zoo-themed Tic-Tac-Toe game with animal emoji tokens, three AI difficulty levels
(Bunny, Fox, and Lion), all powered by Python compiled to WebAssembly.

The finished game runs on a static site (including GitHub Pages) with zero
server-side code.

---

## How Python Runs in the Browser

[Pyodide](https://pyodide.org/) is the CPython interpreter compiled to
WebAssembly with Emscripten. When a visitor loads the page their browser
downloads a ~10 MB runtime, and from that point on every `pyodide.runPython()`
call executes real CPython — standard library included — inside a sandboxed
WebAssembly module.

The workflow is straightforward:

1. Load Pyodide from a CDN with a single `<script>` tag.
2. Call `loadPyodide()` to initialise the runtime (async, one-time cost).
3. Pass your Python source to `pyodide.runPython()`.
4. Call Python functions from JavaScript via `pyodide.globals.get("fn_name")`.

Because WebAssembly runs at near-native speed, algorithms like Minimax finish in
milliseconds — more than fast enough for a 3 x 3 game tree.

---

## Project Structure

The entire game lives in **one HTML file** with three logical sections:

| Section | Language | Responsibility |
|---------|----------|----------------|
| `<style>` | CSS | Safari-themed board grid, earth-tone colours, layout |
| Inline string (`pythonSource`) | Python | Game state, win detection, Minimax AI, emoji tokens |
| `<script>` | JavaScript | Boots Pyodide, renders the UI with animal emojis, relays clicks to Python |

Below each section is reproduced separately so you can study (or customise) the
parts independently.

---

## Zoo Theme

The game uses a safari/savanna visual theme with warm earth tones (sandy gold,
soft green). Players choose their animal from a row of emoji buttons, and each
difficulty level is represented by a zoo animal:

- **Easy** — 🐰 Bunny (random moves)
- **Medium** — 🦊 Fox (60% optimal, 40% random)
- **Hard** — 🦁 Lion (unbeatable minimax)

The player can pick from six animal tokens: 🐶 🐱 🐵 🐼 🐸 🐧. The selected
emoji replaces "X" visually on the board, while the game logic internally still
uses "X" and "O".

---

## Section 1 — CSS (Styling)

A safari-themed design: savanna gradient background, parchment-coloured board
cells with earthy brown borders, and a leafy green highlight for winning lines.

```css
* { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: linear-gradient(160deg, #e8c87a 0%, #d4a853 30%, #a8c686 70%, #7ba05b 100%);
  color: #3b2f1e;
}

h1 {
  margin-bottom: 0.15em;
  font-size: 1.8em;
  color: #3b2f1e;
}

#subtitle {
  font-size: 0.95em;
  color: #5c4a2e;
  margin-bottom: 0.5em;
}

#loading {
  margin: 2em 0;
  font-style: italic;
  color: #6b5a3e;
}

#game-container { display: none; text-align: center; }

/* --- Token selector --- */
#token-selector {
  margin: 0.5em 0 0.25em;
  display: flex;
  gap: 0.4em;
  justify-content: center;
  align-items: center;
}

#token-selector .label {
  font-size: 0.85em;
  font-weight: 600;
  color: #5c4a2e;
  margin-right: 0.3em;
}

#token-selector button {
  width: 40px;
  height: 40px;
  border: 2px solid #b89a5a;
  border-radius: 8px;
  background: #faf3e0;
  cursor: pointer;
  font-size: 1.3em;
  transition: background 0.15s, border-color 0.15s, transform 0.1s;
  display: flex;
  align-items: center;
  justify-content: center;
}

#token-selector button.active {
  background: #d4a853;
  border-color: #8b6914;
  transform: scale(1.1);
}

#token-selector button:hover:not(.active) {
  background: #f0e0b8;
}

/* --- Difficulty selector --- */
#difficulty-selector {
  margin: 0.5em 0 0.75em;
  display: flex;
  gap: 0.5em;
  justify-content: center;
}

#difficulty-selector button {
  padding: 0.4em 1.1em;
  border: 2px solid #8b6914;
  border-radius: 8px;
  background: #faf3e0;
  cursor: pointer;
  font-size: 0.95em;
  transition: background 0.15s, color 0.15s;
  color: #3b2f1e;
}

#difficulty-selector button.active {
  background: #8b6914;
  color: #faf3e0;
}

#difficulty-selector button:hover:not(.active) {
  background: #f0e0b8;
}

/* --- Board --- */
#board {
  display: grid;
  grid-template-columns: repeat(3, 100px);
  grid-template-rows: repeat(3, 100px);
  gap: 5px;
  margin: 0 auto;
}

.cell {
  width: 100px;
  height: 100px;
  background: #faf3e0;
  border: 2px solid #b89a5a;
  border-radius: 10px;
  font-size: 2.4em;
  cursor: pointer;
  transition: background 0.12s;
  display: flex;
  align-items: center;
  justify-content: center;
  user-select: none;
}

.cell:hover { background: #f5e8c8; }
.cell.win { background: #b8e6a0; }

/* --- Status & reset --- */
#status {
  margin: 0.75em 0 0.5em;
  font-size: 1.15em;
  min-height: 1.5em;
  font-weight: 600;
  color: #3b2f1e;
}

#reset-btn {
  padding: 0.5em 1.6em;
  border: none;
  border-radius: 8px;
  background: #8b6914;
  color: #faf3e0;
  font-size: 1em;
  cursor: pointer;
  margin-top: 0.25em;
  transition: background 0.15s;
}

#reset-btn:hover { background: #a07b1a; }
```

---

## Section 2 — Python (Game Logic & AI)

This is the core of the project. It is passed to Pyodide as a string and
executed once; after that JavaScript calls individual functions like
`human_move()` on every click.

### Board Representation & Zoo Tokens

```python
import random

# The board is a flat list of 9 cells (indices 0-8):
#
#   0 | 1 | 2
#   ---------
#   3 | 4 | 5
#   ---------
#   6 | 7 | 8
#
# Each cell is "" (empty), "X" (human), or "O" (AI).

WIN_COMBOS = [
    [0, 1, 2], [3, 4, 5], [6, 7, 8],  # rows
    [0, 3, 6], [1, 4, 7], [2, 5, 8],  # columns
    [0, 4, 8], [2, 4, 6],             # diagonals
]

board = [""] * 9
game_over = False
difficulty = "medium"  # "easy" | "medium" | "hard"

# Zoo theme tokens — display only, game logic uses "X"/"O" internally
player_token = "\U0001f436"  # default: dog
ai_tokens = {
    "easy":   "\U0001f430",  # bunny
    "medium": "\U0001f98a",  # fox
    "hard":   "\U0001f981",  # lion
}

def ai_token():
    return ai_tokens.get(difficulty, "\U0001f98a")
```

### Helper Functions

```python
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
```

### The Minimax Algorithm

Minimax is a classic decision-making algorithm for two-player zero-sum games. It
works by exploring **every possible future game state** recursively and assigning
a score:

- **+10** if O (the AI) wins
- **-10** if X (the human) wins
- **0** for a draw

The AI is the **maximising** player — it picks the move that leads to the
highest score. The human is the **minimising** player — we assume they always
pick the move that is worst for the AI (i.e. best for themselves).

A `depth` parameter is subtracted from winning scores so the AI prefers winning
*sooner* and losing *later*.

```
        O plays (maximise)
       /        |        \
    X plays  X plays   X plays   (minimise)
     / \       |         |
   ...  ...   ...       ...      (recurse until terminal)
```

```python
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
        # AI wins: high score, minus depth so sooner wins rank higher.
        return 10 - depth
    if winner == "X":
        # Human wins: low score, plus depth so later losses are preferred.
        return depth - 10
    if is_draw(b):
        # Draw is neutral.
        return 0

    if is_maximising:
        # AI's turn: find the move with the *maximum* score.
        best = -100
        for move in available_moves(b):
            b[move] = "O"
            score = minimax(b, depth + 1, False)
            b[move] = ""             # undo the move (backtrack)
            best = max(best, score)
        return best
    else:
        # Human's turn: find the move with the *minimum* score.
        best = 100
        for move in available_moves(b):
            b[move] = "X"
            score = minimax(b, depth + 1, True)
            b[move] = ""             # undo the move (backtrack)
            best = min(best, score)
        return best
```

`best_move_minimax` simply calls `minimax` for every available cell and returns
the one with the highest score:

```python
def best_move_minimax(b):
    """
    Choose the optimal cell for O by scoring every available
    move with minimax and returning the one with the highest score.
    """
    best_score = -100
    move = None
    for i in available_moves(b):
        b[i] = "O"
        score = minimax(b, 0, False)  # next turn is human (minimising)
        b[i] = ""
        if score > best_score:
            best_score = score
            move = i
    return move
```

### AI Difficulty Levels

Each difficulty is represented by an animal: 🐰 Bunny (easy), 🦊 Fox (medium),
🦁 Lion (hard).

```python
def ai_move():
    """
    Pick a cell for the AI based on the current difficulty setting.

    - easy (Bunny):   purely random among available cells.
    - medium (Fox):   uses minimax 60% of the time, random otherwise.
    - hard (Lion):    always minimax (unbeatable).
    """
    global board, game_over
    moves = available_moves(board)
    if not moves or game_over:
        return -1

    if difficulty == "easy":
        choice = random.choice(moves)

    elif difficulty == "medium":
        # 60% chance of playing optimally; 40% random.
        if random.random() < 0.6:
            choice = best_move_minimax(board)
        else:
            choice = random.choice(moves)

    else:  # hard
        choice = best_move_minimax(board)

    board[choice] = "O"
    return choice
```

### Move Handler (Called from JavaScript)

The `human_move` function now returns `player_token` and `ai_token` fields so
the JavaScript UI knows which emojis to render.

```python
def human_move(index):
    """
    Place an X in the given cell.

    Returns a dict consumed by the JS front-end:
      ok           - whether the move was accepted
      ai_cell      - where the AI placed its O (-1 if game ended)
      status       - "play", "win_x", "win_o", or "draw"
      win_cells    - indices of the winning line (if any)
      player_token - the player's chosen animal emoji
      ai_token     - the AI's animal emoji for the current difficulty
    """
    global board, game_over

    if game_over or board[index] != "":
        return {"ok": False}

    board[index] = "X"

    base = {
        "player_token": player_token,
        "ai_token": ai_token(),
    }

    if check_winner(board) == "X":
        game_over = True
        return {**base, "ok": True, "ai_cell": -1, "status": "win_x",
                "win_cells": winning_cells(board)}
    if is_draw(board):
        game_over = True
        return {**base, "ok": True, "ai_cell": -1, "status": "draw",
                "win_cells": []}

    ai_cell = ai_move()

    if check_winner(board) == "O":
        game_over = True
        return {**base, "ok": True, "ai_cell": ai_cell, "status": "win_o",
                "win_cells": winning_cells(board)}
    if is_draw(board):
        game_over = True
        return {**base, "ok": True, "ai_cell": ai_cell, "status": "draw",
                "win_cells": []}

    return {**base, "ok": True, "ai_cell": ai_cell, "status": "play",
            "win_cells": []}
```

---

## Section 3 — JavaScript (Pyodide Glue & UI)

### HTML Skeleton

The HTML now includes a player token selector and themed difficulty buttons with
animal emojis.

```html
<h1>&#127796; Zoo Tic-Tac-Toe &#127793;</h1>
<p id="subtitle">Pick your animal and challenge the zoo!</p>
<p id="loading">Loading Python runtime (Pyodide)&hellip;</p>

<div id="game-container">
  <div id="token-selector">
    <span class="label">Your animal:</span>
    <button data-token="&#128054;" class="active">&#128054;</button>
    <button data-token="&#128049;">&#128049;</button>
    <button data-token="&#128053;">&#128053;</button>
    <button data-token="&#128060;">&#128060;</button>
    <button data-token="&#128056;">&#128056;</button>
    <button data-token="&#128039;">&#128039;</button>
  </div>

  <div id="difficulty-selector">
    <button data-level="easy">&#128048; Bunny</button>
    <button data-level="medium" class="active">&#129418; Fox</button>
    <button data-level="hard">&#129409; Lion</button>
  </div>

  <div id="board"></div>
  <div id="status">Your turn</div>
  <button id="reset-btn">New Game</button>
</div>

<!-- Pyodide CDN -->
<script src="https://cdn.jsdelivr.net/pyodide/v0.27.5/full/pyodide.js"></script>
```

### JavaScript Glue Code

The JS now tracks the selected player token and uses animal names in status
messages (e.g. "🦁 Lion wins!" instead of "AI wins!").

```javascript
// The entire Python source from Section 2 is stored in a template
// literal called `pythonSource` (omitted here for brevity).

const AI_NAMES = { easy: "\ud83d\udc30 Bunny", medium: "\ud83e\udd8a Fox", hard: "\ud83e\udd81 Lion" };
let currentPlayerToken = "\ud83d\udc36";
let currentDifficulty = "medium";
let pyodide = null;

async function boot() {
  pyodide = await loadPyodide();
  pyodide.runPython(pythonSource);

  document.getElementById("loading").style.display = "none";
  document.getElementById("game-container").style.display = "block";
  buildBoard();
}

function buildBoard() {
  const boardEl = document.getElementById("board");
  boardEl.innerHTML = "";
  for (let i = 0; i < 9; i++) {
    const cell = document.createElement("div");
    cell.className = "cell";
    cell.dataset.index = i;
    cell.addEventListener("click", onCellClick);
    boardEl.appendChild(cell);
  }
}

function setStatus(text) {
  document.getElementById("status").textContent = text;
}

function getAiToken() {
  return pyodide.globals.get("ai_token")();
}

function renderResult(result) {
  if (!result.ok) return;

  const cells = document.querySelectorAll(".cell");
  const aiEmoji = result.ai_token || getAiToken();

  // Show AI move with its animal emoji
  if (result.ai_cell >= 0) {
    cells[result.ai_cell].textContent = aiEmoji;
  }

  // Highlight winning line
  if (result.win_cells && result.win_cells.length) {
    for (const idx of result.win_cells) {
      cells[idx].classList.add("win");
    }
  }

  // Status text with animal names
  const aiName = AI_NAMES[currentDifficulty] || "AI";
  switch (result.status) {
    case "win_x": setStatus("You win! \ud83c\udf89"); break;
    case "win_o": setStatus(aiName + " wins!"); break;
    case "draw":  setStatus("It's a draw!"); break;
    default:      setStatus("Your turn");
  }
}

function onCellClick(e) {
  const idx = Number(e.currentTarget.dataset.index);

  // Call Python's human_move() and convert the proxy to a JS object.
  const proxy = pyodide.globals.get("human_move")(idx);
  const result = Object.fromEntries(proxy.toJs());
  proxy.destroy();

  if (!result.ok) return;

  // Show the human move with selected animal emoji
  const cells = document.querySelectorAll(".cell");
  cells[idx].textContent = currentPlayerToken;

  // Normalise win_cells (may still be a Pyodide proxy).
  if (result.win_cells && typeof result.win_cells.toJs === "function") {
    result.win_cells = Array.from(result.win_cells.toJs());
  } else if (result.win_cells instanceof Map) {
    result.win_cells = Array.from(result.win_cells.values());
  }

  renderResult(result);
}

// Reset button
document.getElementById("reset-btn").addEventListener("click", () => {
  pyodide.runPython("reset()");
  buildBoard();
  setStatus("Your turn");
});

// Difficulty buttons
document.querySelectorAll("#difficulty-selector button").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll("#difficulty-selector button")
      .forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    currentDifficulty = btn.dataset.level;
    pyodide.runPython(`difficulty = "${btn.dataset.level}"`);
    pyodide.runPython("reset()");
    buildBoard();
    setStatus("Your turn");
  });
});

// Token selector buttons
document.querySelectorAll("#token-selector button").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll("#token-selector button")
      .forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    currentPlayerToken = btn.dataset.token;
    pyodide.runPython(`player_token = "${btn.dataset.token}"`);
  });
});

boot();
```

---

## Embedding in Jekyll / GitHub Pages

To use this on a Jekyll site:

1. **Single-file approach** — save the complete HTML file (all three sections
   combined) as `tic-tac-toe.html` in your repo root or a `/games/` directory.
   Jekyll will serve it as-is.

2. **Embed in a post** — if your Jekyll theme supports raw HTML in posts, paste
   the `<style>`, markup, and `<script>` blocks directly into your `.md` file
   between `{% raw %}` tags, or place them in an HTML layout.

3. **iframe approach** — keep the game in its own HTML file and embed it in any
   post with:

   ```html
   <iframe src="/tic-tac-toe.html" width="400" height="600"
           style="border:none;"></iframe>
   ```

No build step, no npm, no bundler. Push to GitHub and it works.

---

## Key Takeaways

- **Pyodide** makes it practical to run non-trivial Python in the browser with
  no server.
- **Minimax** guarantees optimal play on a 3 x 3 board because the game tree is
  small enough to search exhaustively.
- Mixing difficulty levels is as simple as deciding *when* to consult Minimax
  versus picking at random — each level gets its own zoo animal personality.
- The zoo theme shows how a simple token/emoji system can reskin a game without
  changing any core logic.
- The entire game is a single file — copy it, tweak the CSS, and ship it.
