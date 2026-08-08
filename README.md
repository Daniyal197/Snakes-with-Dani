# Snakes-with-Dani
# 🐍 Snake — GUI Edition

A polished, feature-rich implementation of the classic Snake game built with **Python** and **Pygame**. This project goes beyond a basic terminal snake game by featuring a fully animated GUI, a procedurally generated audio engine, particle effects, and persistent high-score tracking — all built from scratch with no external asset files.

---

## ✨ Features

- **Animated GUI** — gradient background with twinkling stars, glowing checkerboard playfield, and gradient-shaded snake body
- **Procedural Sound Engine** — all sound effects (eat, game over, start, pause) are generated in real time using `numpy` sine-wave synthesis; no `.wav` or `.mp3` files required
- **Particle System** — dynamic particle bursts on eating food and on collision
- **Persistent High Scores** — automatically saved to a local JSON file and loaded on startup
- **Progressive Difficulty** — game speed increases as your score grows
- **Full Game State Management** — dedicated Menu, Play, Pause, and Game Over screens
- **Mute Toggle** — enable/disable sound effects on the fly
- **Zero External Assets** — every visual and audio element is generated programmatically

---

## 🎮 Controls

| Key                | Action                  |
|--------------------|--------------------------|
| `Arrow Keys` / `WASD` | Move the snake         |
| `SPACE`            | Start / Restart game    |
| `P`                | Pause / Resume          |
| `M`                | Mute / Unmute sound     |
| `ESC`              | Quit                    |

---

## 🚀 Getting Started

### Prerequisites

- Python 3.9 or higher
- pip

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/<your-username>/<your-repo-name>.git
   cd <your-repo-name>
   ```

2. (Recommended) Create and activate a virtual environment:
   ```bash
   python -m venv .venv

   # Windows (PowerShell)
   .venv\Scripts\Activate.ps1

   # macOS / Linux
   source .venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

   > **Note (Python 3.13+):** The classic `pygame` package may not yet provide pre-built wheels for the latest Python versions on Windows. If installation fails while trying to build from source, install the actively maintained community fork instead — it's a drop-in replacement:
   > ```bash
   > pip install pygame-ce numpy
   > ```

### Running the Game

```bash
python snake_game.py
```

---

## 🗂️ Project Structure

```
.
├── snake_game.py       # Complete game source code
├── requirements.txt     # Python dependencies
└── snake_highscore.json # Auto-generated on first run (stores high score)
```

---

## 🛠️ Technical Highlights

This project was built to demonstrate practical implementation of core game-development and software-engineering concepts:

- **Finite State Machine** architecture (`MENU`, `PLAYING`, `PAUSED`, `GAMEOVER`) for clean, extensible state handling
- **Delta-time based game loop** ensuring frame-rate-independent, consistent gameplay speed
- **Digital audio synthesis** — sine-wave tone and frequency-sweep generation with fade envelopes, converted to 16-bit stereo PCM and played via `pygame.sndarray`
- **Grid-based collision detection** with correct handling of the "growing snake" edge case
- **Object-oriented design** with dedicated `SoundManager`, `Particle`, and `SnakeGame` classes
- **Memory-optimized data structures** using `__slots__` for high-frequency particle objects

---

## ⚙️ Configuration

Key gameplay parameters can be tuned directly at the top of `snake_game.py`:

| Constant              | Description                          |
|------------------------|----------------------------------------|
| `CELL_SIZE`             | Size of each grid cell in pixels     |
| `GRID_COLS` / `GRID_ROWS` | Playfield dimensions in cells     |
| `MOVE_INTERVAL_BASE`    | Initial snake movement speed          |
| `SPEEDUP_EVERY`         | Points required to trigger a speed increase |

---

## 📌 Roadmap

- [ ] Difficulty selection (Easy / Medium / Hard)
- [ ] Local leaderboard with multiple saved scores
- [ ] Custom themes / color palettes
- [ ] Obstacles / power-ups mode

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

---

## 👤 Author

**Daniyal Ahmed**
BS Information Technology (Cybersecurity) — University of Gujrat

Feel free to connect or reach out for feedback and suggestions!
