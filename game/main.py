"""
Romulan War — dodge-survival (desktop + pygbag / GitHub Pages).
Python 3.9+, pygame or pygame-ce. Assets live next to this file.
"""
from __future__ import annotations

import asyncio
import math
import pathlib
import random
import sys
from enum import Enum, auto

import pygame
from pygame.locals import *

BASE_DIR = pathlib.Path(__file__).resolve().parent

# Display
WINDOWWIDTH = 880
WINDOWHEIGHT = 720
FPS = 60

# Gameplay
BADDIEMINSIZE = 14
BADDIEMAXSIZE = 48
BADDIEMINSPEED = 2
BADDIEMAXSPEED = 10
ADDNEWBADDIE_BASE = 38
PLAYERMOVERATE = 7
STARTING_LIVES = 3
INVINCIBLE_MS = 2200
POWERUP_SPAWN_FRAMES = 420
MAX_POWERUPS_ON_SCREEN = 2


class GameMode(Enum):
    MENU = auto()
    PLAYING = auto()
    GAME_OVER = auto()


class PlayStyle(Enum):
    ONE_PLAYER = auto()
    TWO_PLAYER = auto()


def load_asset_path(name: str) -> pathlib.Path:
    return BASE_DIR / name


def terminate() -> None:
    pygame.quit()
    if sys.platform == "emscripten":
        return
    sys.exit()


def safe_set_mouse_pos(x: int, y: int) -> None:
    try:
        pygame.mouse.set_pos((x, y))
    except pygame.error:
        pass


def load_high_scores() -> tuple[int, int, int]:
    path = BASE_DIR / "highscores.txt"
    if not path.is_file():
        return 0, 0, 0
    try:
        text = path.read_text(encoding="utf-8").strip().split()
        if len(text) >= 3:
            return int(text[0]), int(text[1]), int(text[2])
        if len(text) == 1:
            return int(text[0]), 0, 0
    except (ValueError, OSError):
        pass
    return 0, 0, 0


def save_high_scores(s1: int, s2: int, coop: int) -> None:
    try:
        (BASE_DIR / "highscores.txt").write_text(f"{s1} {s2} {coop}", encoding="utf-8")
    except OSError:
        pass


def tint_image(image: pygame.Surface, rgb: tuple[int, int, int]) -> pygame.Surface:
    tinted = image.copy()
    tinted.fill(rgb, special_flags=pygame.BLEND_RGBA_MULT)
    return tinted


def draw_text(
    surface: pygame.Surface,
    text: str,
    font: pygame.font.Font,
    x: int,
    y: int,
    color: tuple[int, int, int] = (240, 245, 255),
    shadow: bool = True,
) -> None:
    if shadow:
        sh = font.render(text, True, (0, 0, 0))
        surface.blit(sh, (x + 2, y + 2))
    img = font.render(text, True, color)
    surface.blit(img, (x, y))


def draw_starfield(
    surface: pygame.Surface,
    stars: list[dict],
    dt: float,
    drift: float = 1.0,
) -> None:
    surface.fill((10, 14, 32))
    h, w = WINDOWHEIGHT, WINDOWWIDTH
    for s in stars:
        s["y"] += s["speed"] * dt * 0.06 * drift
        if s["y"] > h:
            s["y"] = 0
            s["x"] = random.uniform(0, w)
        br = int(s["bright"])
        pygame.draw.circle(surface, (br, br, min(255, br + 40)), (int(s["x"]), int(s["y"])), s["radius"])


def init_stars(n: int = 140) -> list[dict]:
    w, h = WINDOWWIDTH, WINDOWHEIGHT
    out = []
    for _ in range(n):
        out.append(
            {
                "x": random.uniform(0, w),
                "y": random.uniform(0, h),
                "speed": random.uniform(20, 120),
                "bright": random.uniform(90, 220),
                "radius": random.choice([1, 1, 2]),
            }
        )
    return out


def difficulty_factor(score: int) -> float:
    return min(1.0 + score / 3500.0, 2.35)


def spawn_baddie(
    romulan: pygame.Surface,
    klingon: pygame.Surface,
    diff: float,
) -> list[dict]:
    baddie_size = random.randint(BADDIEMINSIZE, BADDIEMAXSIZE)
    top = 0 - baddie_size
    x = random.randint(0, WINDOWWIDTH - baddie_size)
    lo = int(BADDIEMINSPEED * diff)
    hi = int(BADDIEMAXSPEED * diff)
    hi = max(hi, lo + 1)
    speed = random.randint(lo, hi)
    img = romulan if random.random() < 0.5 else klingon
    scaled = pygame.transform.smoothscale(img, (baddie_size, baddie_size))
    return [
        {
            "rect": pygame.Rect(x, top, baddie_size, baddie_size),
            "speed": speed,
            "surface": scaled,
        }
    ]


def spawn_powerup() -> dict:
    kinds = [
        ("shield", (120, 200, 255)),
        ("slow", (255, 220, 100)),
        ("life", (120, 255, 160)),
        ("bonus", (255, 140, 200)),
    ]
    kind, color = random.choice(kinds)
    r = 16
    x = random.randint(r, WINDOWWIDTH - r)
    return {
        "rect": pygame.Rect(x, -r * 2, r * 2, r * 2),
        "kind": kind,
        "color": color,
        "speed": random.randint(3, 6),
    }


def draw_powerup(surf: pygame.Surface, p: dict) -> None:
    cx, cy = p["rect"].center
    r = p["rect"].width // 2
    pygame.draw.circle(surf, p["color"], (cx, cy), r)
    pygame.draw.circle(surf, (255, 255, 255), (cx, cy), r, 2)
    if p["kind"] == "life":
        pygame.draw.line(surf, (20, 40, 20), (cx - 6, cy), (cx + 6, cy), 3)
        pygame.draw.line(surf, (20, 40, 20), (cx, cy - 6), (cx, cy + 6), 3)
    elif p["kind"] == "shield":
        pygame.draw.arc(surf, (255, 255, 255), p["rect"].inflate(-4, -4), 0.3, 2.8, 3)
    elif p["kind"] == "slow":
        pygame.draw.polygon(surf, (40, 30, 10), [(cx + 5, cy), (cx - 6, cy - 7), (cx - 6, cy + 7)])
    elif p["kind"] == "bonus":
        for i in range(8):
            ang = i * math.pi / 4
            pygame.draw.line(
                surf,
                (255, 255, 255),
                (cx, cy),
                (cx + int(10 * math.cos(ang)), cy + int(10 * math.sin(ang))),
                2,
            )


async def main() -> None:
    pygame.init()
    pygame.mixer.init()
    main_clock = pygame.time.Clock()

    window = pygame.display.set_mode((WINDOWWIDTH, WINDOWHEIGHT))
    pygame.display.set_caption("Romulan War — Dodger")
    pygame.mouse.set_visible(True)

    try:
        title_font = pygame.font.SysFont("arial", 56, bold=True)
        menu_font = pygame.font.SysFont("arial", 34)
        hud_font = pygame.font.SysFont("arial", 28)
        small_font = pygame.font.SysFont("arial", 22)
    except Exception:
        title_font = pygame.font.Font(None, 56)
        menu_font = pygame.font.Font(None, 34)
        hud_font = pygame.font.Font(None, 28)
        small_font = pygame.font.Font(None, 22)

    pickup_sound = None
    game_over_sound = None
    try:
        pickup_sound = pygame.mixer.Sound(str(load_asset_path("pickup.wav")))
        game_over_sound = pygame.mixer.Sound(str(load_asset_path("gameover.wav")))
    except pygame.error:
        pass

    try:
        pygame.mixer.music.load(str(load_asset_path("background.mid")))
    except pygame.error:
        pass

    player_img = pygame.image.load(str(load_asset_path("player.png"))).convert_alpha()
    romulan_img = pygame.image.load(str(load_asset_path("romulan.png"))).convert_alpha()
    klingon_img = pygame.image.load(str(load_asset_path("klingon.png"))).convert_alpha()

    p1_surface = tint_image(player_img, (180, 220, 255))
    p2_surface = tint_image(player_img, (255, 190, 170))

    stars = init_stars()
    high_1p, high_p1, high_p2 = load_high_scores()

    game_state = GameMode.MENU
    play_style = PlayStyle.ONE_PLAYER
    menu_index = 0
    menu_options = ["1 Player", "2 Players (versus)", "Quit"]

    # Runtime (reset when starting a match)
    baddies: list[dict] = []
    powerups: list[dict] = []
    baddie_counter = 0
    powerup_counter = 0
    score = 0
    p1_score = 0
    p2_score = 0
    slow_until = 0
    global_slow = False
    p1_rect = player_img.get_rect()
    p2_rect = player_img.get_rect()
    p1_lives = STARTING_LIVES
    p2_lives = STARTING_LIVES
    p1_inv_until = 0
    p2_inv_until = 0
    p1_shields = 0
    p2_shields = 0
    p1_dead = False
    p2_dead = False
    move_left = move_right = move_up = move_down = False
    p2_left = p2_right = p2_up = p2_down = False
    paused = False
    winner_text = ""
    cheats_used = False

    def reset_match(style: PlayStyle) -> None:
        nonlocal baddies, powerups, baddie_counter, powerup_counter, score, p1_score, p2_score, slow_until
        nonlocal p1_rect, p2_rect, p1_lives, p2_lives, p1_inv_until, p2_inv_until
        nonlocal p1_shields, p2_shields, p1_dead, p2_dead, winner_text, cheats_used
        nonlocal move_left, move_right, move_up, move_down
        nonlocal p2_left, p2_right, p2_up, p2_down, global_slow, paused
        baddies = []
        powerups = []
        baddie_counter = 0
        powerup_counter = 0
        score = 0
        p1_score = 0
        p2_score = 0
        slow_until = 0
        global_slow = False
        paused = False
        cheats_used = False
        p1_rect = player_img.get_rect()
        p1_rect.midbottom = (WINDOWWIDTH // (4 if style == PlayStyle.TWO_PLAYER else 2), WINDOWHEIGHT - 24)
        p2_rect = player_img.get_rect()
        p2_rect.midbottom = (3 * WINDOWWIDTH // 4, WINDOWHEIGHT - 24)
        p1_lives = p2_lives = STARTING_LIVES
        p1_inv_until = p2_inv_until = 0
        p1_shields = p2_shields = 0
        p1_dead = p2_dead = False
        winner_text = ""
        move_left = move_right = move_up = move_down = False
        p2_left = p2_right = p2_up = p2_down = False
        pygame.mixer.music.play(-1, 0.0)

    running = True
    while running:
        dt = main_clock.tick(FPS) / 1000.0
        now = pygame.time.get_ticks()

        if game_state == GameMode.MENU:
            for event in pygame.event.get():
                if event.type == QUIT:
                    running = False
                    break
                if event.type == KEYDOWN:
                    if event.key == K_ESCAPE:
                        running = False
                        break
                    if event.key in (K_UP, K_w):
                        menu_index = (menu_index - 1) % len(menu_options)
                    if event.key in (K_DOWN, K_s):
                        menu_index = (menu_index + 1) % len(menu_options)
                    if event.key in (K_RETURN, K_SPACE):
                        choice = menu_options[menu_index]
                        if choice == "Quit":
                            running = False
                            break
                        play_style = (
                            PlayStyle.ONE_PLAYER if choice.startswith("1") else PlayStyle.TWO_PLAYER
                        )
                        reset_match(play_style)
                        game_state = GameMode.PLAYING
                        if play_style == PlayStyle.ONE_PLAYER:
                            pygame.mouse.set_visible(False)
                        else:
                            pygame.mouse.set_visible(True)

            draw_starfield(window, stars, dt, 1.0)
            draw_text(window, "ROMULAN WAR", title_font, WINDOWWIDTH // 2 - 200, 80, (200, 220, 255))
            draw_text(window, "Survive the storm", small_font, WINDOWWIDTH // 2 - 100, 145, (160, 170, 200))
            y0 = 280
            for i, label in enumerate(menu_options):
                prefix = "> " if i == menu_index else "   "
                col = (255, 230, 120) if i == menu_index else (200, 200, 220)
                draw_text(window, prefix + label, menu_font, WINDOWWIDTH // 2 - 160, y0 + i * 48, col)
            draw_text(
                window,
                "Up/Down or W/S · Enter to start · Esc quits",
                small_font,
                WINDOWWIDTH // 2 - 240,
                WINDOWHEIGHT - 88,
                (140, 150, 180),
            )
            draw_text(
                window,
                "1P: mouse + WASD/arrows   ·   2P: P1 WASD, P2 arrow keys",
                small_font,
                WINDOWWIDTH // 2 - 320,
                WINDOWHEIGHT - 58,
                (120, 130, 160),
            )
            pygame.display.flip()
            await asyncio.sleep(0)
            continue

        if game_state == GameMode.GAME_OVER:
            for event in pygame.event.get():
                if event.type == QUIT:
                    running = False
                    break
                if event.type == KEYDOWN:
                    if event.key == K_ESCAPE:
                        running = False
                        break
                    game_state = GameMode.MENU
                    pygame.mouse.set_visible(True)
                    if game_over_sound:
                        game_over_sound.stop()

            draw_starfield(window, stars, dt, 0.4)
            draw_text(window, "GAME OVER", title_font, WINDOWWIDTH // 2 - 140, 200, (255, 120, 120))
            if winner_text:
                draw_text(window, winner_text, menu_font, WINDOWWIDTH // 2 - 200, 280, (255, 220, 160))
            if play_style == PlayStyle.ONE_PLAYER:
                draw_text(window, f"Score: {score}", hud_font, WINDOWWIDTH // 2 - 80, 340, (220, 230, 255))
                draw_text(window, f"Best (1P): {high_1p}", small_font, WINDOWWIDTH // 2 - 90, 380, (160, 170, 200))
            else:
                draw_text(
                    window,
                    f"P1: {p1_score}  (best {high_p1})    P2: {p2_score}  (best {high_p2})",
                    small_font,
                    WINDOWWIDTH // 2 - 280,
                    330,
                    (200, 200, 220),
                )
            draw_text(window, "Press any key for menu", menu_font, WINDOWWIDTH // 2 - 180, 440, (180, 200, 255))
            pygame.display.flip()
            await asyncio.sleep(0)
            continue

        # PLAYING
        assert game_state == GameMode.PLAYING

        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
                break
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    game_state = GameMode.MENU
                    pygame.mixer.music.stop()
                    pygame.mouse.set_visible(True)
                    continue
                if event.key == K_p:
                    paused = not paused
                if play_style == PlayStyle.ONE_PLAYER:
                    if event.key == ord("z"):
                        cheats_used = True
                    if event.key == ord("x"):
                        cheats_used = True
                    if event.key in (K_LEFT, ord("a")):
                        move_right = False
                        move_left = True
                    if event.key in (K_RIGHT, ord("d")):
                        move_left = False
                        move_right = True
                    if event.key in (K_UP, ord("w")):
                        move_down = False
                        move_up = True
                    if event.key in (K_DOWN, ord("s")):
                        move_up = False
                        move_down = True
                else:
                    if event.key == ord("a"):
                        move_right = False
                        move_left = True
                    if event.key == ord("d"):
                        move_left = False
                        move_right = True
                    if event.key == ord("w"):
                        move_down = False
                        move_up = True
                    if event.key == ord("s"):
                        move_up = False
                        move_down = True
                if play_style == PlayStyle.TWO_PLAYER:
                    if event.key == K_LEFT:
                        p2_right = False
                        p2_left = True
                    if event.key == K_RIGHT:
                        p2_left = False
                        p2_right = True
                    if event.key == K_UP:
                        p2_down = False
                        p2_up = True
                    if event.key == K_DOWN:
                        p2_up = False
                        p2_down = True

            if event.type == KEYUP:
                if play_style == PlayStyle.ONE_PLAYER:
                    if event.key in (K_LEFT, ord("a")):
                        move_left = False
                    if event.key in (K_RIGHT, ord("d")):
                        move_right = False
                    if event.key in (K_UP, ord("w")):
                        move_up = False
                    if event.key in (K_DOWN, ord("s")):
                        move_down = False
                else:
                    if event.key == ord("a"):
                        move_left = False
                    if event.key == ord("d"):
                        move_right = False
                    if event.key == ord("w"):
                        move_up = False
                    if event.key == ord("s"):
                        move_down = False
                if play_style == PlayStyle.TWO_PLAYER:
                    if event.key == K_LEFT:
                        p2_left = False
                    if event.key == K_RIGHT:
                        p2_right = False
                    if event.key == K_UP:
                        p2_up = False
                    if event.key == K_DOWN:
                        p2_down = False

            if play_style == PlayStyle.ONE_PLAYER and event.type == MOUSEMOTION:
                p1_rect.centerx = event.pos[0]
                p1_rect.centery = event.pos[1]

        if not running:
            break

        if game_state != GameMode.PLAYING:
            continue

        if paused:
            draw_starfield(window, stars, dt, 0.2)
            for b in baddies:
                window.blit(b["surface"], b["rect"])
            window.blit(p1_surface if not p1_dead else player_img, p1_rect)
            if play_style == PlayStyle.TWO_PLAYER:
                window.blit(p2_surface if not p2_dead else player_img, p2_rect)
            for p in powerups:
                draw_powerup(window, p)
            draw_text(window, "PAUSED", title_font, WINDOWWIDTH // 2 - 100, WINDOWHEIGHT // 2 - 40, (255, 255, 200))
            draw_text(window, "P to resume", hud_font, WINDOWWIDTH // 2 - 80, WINDOWHEIGHT // 2 + 20, (200, 200, 220))
            pygame.display.flip()
            await asyncio.sleep(0)
            continue

        cheat_reverse = False
        cheat_slow = False
        if play_style == PlayStyle.ONE_PLAYER:
            keys = pygame.key.get_pressed()
            cheat_reverse = keys[ord("z")]
            cheat_slow = keys[ord("x")]
            if cheat_reverse or cheat_slow:
                cheats_used = True

        global_slow = now < slow_until
        enemy_slow = cheat_slow or global_slow

        if not paused:
            if play_style == PlayStyle.ONE_PLAYER:
                score += 1
            else:
                if not p1_dead:
                    p1_score += 1
                if not p2_dead:
                    p2_score += 1

        diff_score = score if play_style == PlayStyle.ONE_PLAYER else max(p1_score, p2_score)
        diff = difficulty_factor(diff_score)

        spawn_rate = max(8, int(ADDNEWBADDIE_BASE / diff))
        if not cheat_reverse:
            baddie_counter += 1
        if baddie_counter >= spawn_rate:
            baddie_counter = 0
            for _ in range(2):
                for nb in spawn_baddie(romulan_img, klingon_img, diff):
                    baddies.append(nb)

        powerup_counter += 1
        if (
            len(powerups) < MAX_POWERUPS_ON_SCREEN
            and powerup_counter >= POWERUP_SPAWN_FRAMES
            and random.random() < 0.45
        ):
            powerup_counter = 0
            powerups.append(spawn_powerup())

        rate = PLAYERMOVERATE
        if move_left and p1_rect.left > 0:
            p1_rect.move_ip(-rate, 0)
        if move_right and p1_rect.right < WINDOWWIDTH:
            p1_rect.move_ip(rate, 0)
        if move_up and p1_rect.top > 0:
            p1_rect.move_ip(0, -rate)
        if move_down and p1_rect.bottom < WINDOWHEIGHT:
            p1_rect.move_ip(0, rate)

        if play_style == PlayStyle.TWO_PLAYER and not p2_dead:
            if p2_left and p2_rect.left > 0:
                p2_rect.move_ip(-rate, 0)
            if p2_right and p2_rect.right < WINDOWWIDTH:
                p2_rect.move_ip(rate, 0)
            if p2_up and p2_rect.top > 0:
                p2_rect.move_ip(0, -rate)
            if p2_down and p2_rect.bottom < WINDOWHEIGHT:
                p2_rect.move_ip(0, rate)

        if play_style == PlayStyle.ONE_PLAYER:
            safe_set_mouse_pos(p1_rect.centerx, p1_rect.centery)

        for b in baddies:
            if cheat_reverse:
                dy = -max(3, abs(b["speed"]) // 2)
            elif enemy_slow:
                dy = max(1, int(b["speed"] * 0.38))
            else:
                dy = b["speed"]
            b["rect"].move_ip(0, int(dy))

        for p in powerups[:]:
            p["rect"].move_ip(0, p["speed"])
            if p["rect"].top > WINDOWHEIGHT:
                powerups.remove(p)

        for b in baddies[:]:
            if b["rect"].top > WINDOWHEIGHT:
                baddies.remove(b)

        # Power-up pickup (P1: overlap; P2: overlap in 2P)
        for p in powerups[:]:
            if not p1_dead and p1_rect.colliderect(p["rect"]):
                if p["kind"] == "shield":
                    p1_shields += 1
                elif p["kind"] == "slow":
                    slow_until = now + 4500
                elif p["kind"] == "life":
                    p1_lives = min(p1_lives + 1, 9)
                elif p["kind"] == "bonus":
                    score += 350 if play_style == PlayStyle.ONE_PLAYER else 0
                    if play_style == PlayStyle.TWO_PLAYER:
                        p1_score += 350
                powerups.remove(p)
                if pickup_sound:
                    pickup_sound.play()
                continue
            if play_style == PlayStyle.TWO_PLAYER and not p2_dead and p2_rect.colliderect(p["rect"]):
                if p["kind"] == "shield":
                    p2_shields += 1
                elif p["kind"] == "slow":
                    slow_until = now + 4500
                elif p["kind"] == "life":
                    p2_lives = min(p2_lives + 1, 9)
                elif p["kind"] == "bonus":
                    p2_score += 350
                powerups.remove(p)
                if pickup_sound:
                    pickup_sound.play()

        def handle_player_hit(
            inv_until: int,
            lives: int,
            shields: int,
        ) -> tuple[int, int, int, bool]:
            if now < inv_until:
                return inv_until, lives, shields, False
            if shields > 0:
                if pickup_sound:
                    pickup_sound.play()
                return now + 400, lives, shields - 1, True
            lives -= 1
            if lives <= 0:
                return inv_until, lives, shields, True
            return now + INVINCIBLE_MS, lives, shields, True

        for b in baddies[:]:
            hit_handled = False
            if not p1_dead and p1_rect.colliderect(b["rect"]):
                p1_inv_until, p1_lives, p1_shields, consumed = handle_player_hit(
                    p1_inv_until, p1_lives, p1_shields
                )
                if consumed:
                    baddies.remove(b)
                    hit_handled = True
                if p1_lives <= 0:
                    p1_dead = True
            if not hit_handled and play_style == PlayStyle.TWO_PLAYER and not p2_dead and p2_rect.colliderect(b["rect"]):
                p2_inv_until, p2_lives, p2_shields, consumed = handle_player_hit(
                    p2_inv_until, p2_lives, p2_shields
                )
                if consumed:
                    if b in baddies:
                        baddies.remove(b)
                if p2_lives <= 0:
                    p2_dead = True

        ended = False
        if play_style == PlayStyle.ONE_PLAYER and p1_dead:
            ended = True
            if not cheats_used and score > high_1p:
                high_1p = score
                save_high_scores(high_1p, high_p1, high_p2)
            winner_text = ""
        elif play_style == PlayStyle.TWO_PLAYER and (p1_dead or p2_dead):
            if p1_dead and p2_dead:
                ended = True
                winner_text = "Draw — both ships lost!"
                high_p1 = max(high_p1, p1_score)
                high_p2 = max(high_p2, p2_score)
                save_high_scores(high_1p, high_p1, high_p2)
            elif p1_dead and not p2_dead:
                ended = True
                winner_text = "Player 2 wins!"
                high_p2 = max(high_p2, p2_score)
                save_high_scores(high_1p, high_p1, high_p2)
            elif p2_dead and not p1_dead:
                ended = True
                winner_text = "Player 1 wins!"
                high_p1 = max(high_p1, p1_score)
                save_high_scores(high_1p, high_p1, high_p2)

        if ended:
            pygame.mixer.music.stop()
            if game_over_sound:
                game_over_sound.play()
            game_state = GameMode.GAME_OVER
            pygame.mouse.set_visible(True)
            continue

        draw_starfield(window, stars, dt, 0.85 + 0.15 * min(diff, 2.0))

        for b in baddies:
            window.blit(b["surface"], b["rect"])
        for p in powerups:
            draw_powerup(window, p)

        def blink_on(inv_until: int) -> bool:
            return (now < inv_until) and ((now // 120) % 2 == 0)

        if not p1_dead:
            if not blink_on(p1_inv_until):
                window.blit(p1_surface, p1_rect)
            if p1_shields > 0:
                rad = max(p1_rect.width, p1_rect.height) // 2 + 10
                pygame.draw.circle(window, (90, 170, 230), p1_rect.center, rad, 3)
        if play_style == PlayStyle.TWO_PLAYER and not p2_dead:
            if not blink_on(p2_inv_until):
                window.blit(p2_surface, p2_rect)
            if p2_shields > 0:
                rad = max(p2_rect.width, p2_rect.height) // 2 + 10
                pygame.draw.circle(window, (230, 150, 130), p2_rect.center, rad, 3)

        hud_y = 8
        if play_style == PlayStyle.ONE_PLAYER:
            draw_text(window, f"Score {score}", hud_font, 12, hud_y, (220, 230, 255))
        else:
            draw_text(
                window,
                f"P1 {p1_score}    P2 {p2_score}",
                hud_font,
                12,
                hud_y,
                (200, 220, 255),
            )
        draw_text(window, f"Best 1P: {high_1p}", small_font, 12, hud_y + 36, (150, 160, 190))
        if play_style == PlayStyle.TWO_PLAYER:
            draw_text(
                window,
                f"Best vs: {high_p1} / {high_p2}",
                small_font,
                12,
                hud_y + 62,
                (130, 140, 170),
            )
        if enemy_slow:
            draw_text(window, "SLOW-MO", small_font, WINDOWWIDTH - 120, hud_y, (255, 220, 120))
        if play_style == PlayStyle.ONE_PLAYER:
            draw_text(window, f"Lives {p1_lives}", hud_font, WINDOWWIDTH - 120, hud_y + 34, (200, 255, 200))
            if p1_shields:
                draw_text(window, f"Shield x{p1_shields}", small_font, WINDOWWIDTH - 140, hud_y + 68, (160, 210, 255))
        else:
            draw_text(window, f"P1 ♥{p1_lives}  shield {p1_shields}", small_font, 12, WINDOWHEIGHT - 78, (180, 210, 255))
            draw_text(window, f"P2 ♥{p2_lives}  shield {p2_shields}", small_font, 12, WINDOWHEIGHT - 48, (255, 200, 180))

        draw_text(window, "P pause  ·  Esc menu", small_font, WINDOWWIDTH - 220, WINDOWHEIGHT - 28, (100, 110, 140))

        pygame.display.flip()
        await asyncio.sleep(0)

    terminate()


if __name__ == "__main__":
    asyncio.run(main())
