# Tic-Tac-Zoo

A zoo-themed Tic-Tac-Toe game that runs entirely in the browser, built as an experiment with [Claude Code](https://claude.ai/claude-code).

## About

This project was created to explore what it's like to build a complete, working application using Claude Code as the primary development tool. The goal was to see how well an AI-assisted workflow handles everything from game logic and AI algorithms to theming, testing, and deployment.

The game itself is a single HTML file — no server, no build step, no dependencies. Python handles the game logic and AI (via [Pyodide](https://pyodide.org/)), while JavaScript manages the UI.

## Features

- **Zoo theme** — safari-styled board with animal emoji tokens
- **Player token selector** — choose from five animal avatars (locked once the game starts)
- **Three AI difficulties**, each represented by a zoo animal:
  - Bunny (easy) — random moves
  - Fox (medium) — 60% optimal, 40% random
  - Lion (hard) — full minimax, unbeatable
- **Python in the browser** — game logic compiled to WebAssembly via Pyodide

## Files

| File | Purpose |
|------|---------|
| `tic-tac-toe.html` | The complete game (single file, self-contained) |
| `game_logic.py` | Standalone Python game logic (extracted for testing) |
| `test_game_logic.py` | Pytest suite — 32 tests covering board helpers, minimax, difficulty levels, and integration |
| `2026-01-29-python-tic-tac-toe-in-the-browser.md` | Blog post walkthrough of the code |

## Playing

Open `tic-tac-toe.html` in any modern browser. Pyodide loads from a CDN — no local setup required.
