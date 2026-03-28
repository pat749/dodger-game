# Romulan War (Dodger)

A dodge-survival **pygame** game with a menu, scaling difficulty, power-ups, lives, local **two-player versus**, and a **playable web build** on **GitHub Pages** (via [pygbag](https://github.com/pygame-web/pygbag)).

## Play in the browser (GitHub Pages)

1. Push this repository to GitHub (default branch `main` or `master`).
2. Open **Settings → Pages**.
3. Under **Build and deployment**, set **Source** to **GitHub Actions** (not “Deploy from a branch”).
4. The workflow **Deploy to GitHub Pages** will run on push; when it finishes, open:

   **`https://<your-username>.github.io/<repository-name>/`**

   Example: repo `dodger-game` → `https://YOURUSER.github.io/dodger-game/`

5. First load can take a while while the browser caches the Python/pygame WebAssembly runtime. Use a **Chromium-based** browser for the fewest issues.

If the workflow is missing permission the first time, approve **Pages** deployment under the **Actions** tab when GitHub prompts you.

## Run on your computer

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cd game
python main.py
```

You can also run `python dodger.py` from `Dodger-game python/Dodger-master/`; it forwards to `game/main.py`.

## Controls

| Action | Keys |
|--------|------|
| Menu | Up/Down or W/S, Enter |
| Quit | Esc |
| Pause | P |
| 1P | Mouse + WASD or arrows |
| 2P | P1: WASD · P2: arrow keys |

## Repository layout

| Path | Purpose |
|------|--------|
| `game/main.py` | Game code (required name for pygbag) |
| `game/*.png`, `*.wav`, `background.mid` | Assets |
| `.github/workflows/github-pages.yml` | Builds and deploys the web version |
| `requirements.txt` | `pygame-ce` for desktop |

`game/highscores.txt` is created locally when you play and is gitignored.

## Credits

Extended from the classic Dodger-style pygame tutorial.
