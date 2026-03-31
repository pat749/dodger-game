# Romulan War (Dodger) · Arcade Lab

Dodge-survival game with a **polished desktop build** (Python/pygame), a **reliable web hub** (HTML5 canvas — no WebAssembly) including **Neon Circuit** (car arena with human / AI / versus + engine audio), and an **ML / RL stack**: tabular **Double Q** on dodge, **DQN** on a discrete car-ring env, documented in **`ml/ALGORITHMS.md`**.

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

## Machine learning / RL

See **`ml/README.md`** and **`ml/ALGORITHMS.md`**. Summary:

- **`ml/dodge_env.py`** + **`ml/train_q.py`** — tabular Q / Double Q → `ml/checkpoints/q_table.json`.
- **`ml/car_env.py`** + **`ml/train_dqn_car.py`** — DQN (PyTorch) → `ml/checkpoints/dqn_car.pt`.

```bash
pip install -r requirements-ml.txt
python3 -m ml.train_q --seed 0

pip install -r requirements-ml-rl.txt
python3 -m ml.train_dqn_car --steps 20000
python3 -m ml.eval_dqn_car --episodes 300
python3 -m ml.export_dqn_car_web   # optional: Neon Circuit AI in the browser (see web/dqn_car_policy.json)
```

**`CITATION.cff`** is included for GitHub’s “Cite this repository” widget.

## Repository layout

| Path | Role |
|------|------|
| `web/` | **GitHub Pages** hub: Dodger + Car arena (`index.html`, `dodger.*`, `car.*`) |
| `game/` | Python/pygame sources + assets |
| `ml/` | MDPs + `train_q` + `train_dqn_car` |
| `.github/workflows/github-pages.yml` | Deploy **`web/`** → **`gh-pages`** |
| `requirements.txt` | Desktop game (`pygame-ce`) |
| `requirements-ml.txt` | NumPy for tabular RL |
| `requirements-ml-rl.txt` | PyTorch + NumPy for DQN |

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
