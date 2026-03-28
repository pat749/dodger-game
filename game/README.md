# Romulan War (game sources)

This folder is the **canonical** copy of the game. It must contain `main.py` (pygbag expects that name for web builds).

```bash
cd game
pip install pygame-ce
python main.py
```

GitHub Actions builds `game/build/web` with [pygbag](https://github.com/pygame-web/pygbag) and deploys it to **GitHub Pages**.
