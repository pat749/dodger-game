# Romulan War (Dodger)

Dodge-survival game with a **polished desktop build** (Python/pygame), a **reliable web build** (HTML5 canvas — no WebAssembly), and an **RL / ML research slice** (formal MDP + tabular Q-learning) suitable to extend for coursework or a thesis-side project.

## Play in the browser (GitHub Pages)

The site is served from the **`web/`** folder (plain HTML + Canvas + JavaScript). **Pygbag is no longer required** — deployment is a simple static upload.

1. Push **`main`** and wait for **Actions → Deploy to GitHub Pages** to finish.
2. **Settings → Pages →** source **Deploy from a branch →** **`gh-pages`** **/** **(root)**.
3. Open **`https://<user>.github.io/<repo>/`** (e.g. `https://pat749.github.io/dodger-game/`).

Hard-refresh after updates (**Ctrl+Shift+R**). Use a Chromium-based browser for best results.

## Run on your computer (full Python game)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd game
python main.py
```

Legacy launcher: `python dodger.py` in `Dodger-game python/Dodger-master/` (forwards to `game/main.py`).

## Machine learning / RL baseline

See **`ml/README.md`**. Summary:

- **`ml/dodge_env.py`** — discrete dodge **MDP** (stochastic hazards, lane actions).
- **`ml/train_q.py`** — **Q-learning** baseline; writes `ml/checkpoints/q_table.json` (gitignored).

```bash
pip install -r requirements-ml.txt
python3 -m ml.train_q --seed 0
```

**`CITATION.cff`** is included for GitHub’s “Cite this repository” widget.

## Repository layout

| Path | Role |
|------|------|
| `web/` | **GitHub Pages** game (canvas + JS) |
| `game/` | Python/pygame sources + assets |
| `ml/` | MDP + Q-learning experiments |
| `.github/workflows/github-pages.yml` | Deploy **`web/`** → **`gh-pages`** |
| `requirements.txt` | Desktop game (`pygame-ce`) |
| `requirements-ml.txt` | NumPy only for `ml/` |

## Controls (desktop & web)

| | |
|--|--|
| Menu | ↑↓ or W/S, Enter |
| 1P | Mouse + WASD / arrows; **Z / X** cheats (1P, desktop) |
| 2P | P1 WASD · P2 arrows |
| Pause | **P** · **Esc** menu |

## Troubleshooting

- **Old Jekyll / `docs` errors:** use **`gh-pages`** + **`/ (root)`**, not **`/docs`**, for the live game (see `docs/` note in earlier commits if applicable).
- **Pygbag black screen:** use the **`web/`** build instead; it is the supported browser target now.

## Credits

Extended from the classic Dodger-style pygame tutorial; web and RL layers added for teaching and research demos.
