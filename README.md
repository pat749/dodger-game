# Romulan War (Dodger)

A dodge-survival **pygame** game with a menu, scaling difficulty, power-ups, lives, local **two-player versus**, and a **playable web build** on **GitHub Pages** (via [pygbag](https://github.com/pygame-web/pygbag)).

## Play in the browser (GitHub Pages)

The workflow builds the game and pushes the site to the **`gh-pages`** branch (no “GitHub Actions” Pages source needed).

1. Push **`main`** (or **`master`**). Wait until **Actions → Deploy to GitHub Pages** succeeds.
2. Open **Settings → Pages**.
3. Under **Build and deployment**, set **Source** to **Deploy from a branch**.
4. Choose branch **`gh-pages`**, folder **`/ (root)`**, then **Save**.
5. After a minute, open:

   **`https://<your-username>.github.io/<repository-name>/`**

   Example: `https://pat749.github.io/dodger-game/`

6. First load can take a while while the browser caches the Python/pygame WebAssembly runtime. A **Chromium-based** browser works best.

**If you already enabled “GitHub Actions” as the Pages source:** switch to **Deploy from a branch** and **`gh-pages`** as above, or the new workflow will not be used by Pages.

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
