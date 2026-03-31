/**
 * Romulan War — canvas build for GitHub Pages (no WebAssembly).
 * Parity with Python: menu, 1P + mouse, 2P, lives, shields, power-ups, ramping difficulty.
 */

const W = 880;
const H = 720;

const canvas = document.getElementById("game");
const ctx = canvas.getContext("2d");

const STATE = { MENU: 0, PLAY: 1, PAUSE: 2, GAMEOVER: 3, CITE: 4 };
let state = STATE.MENU;
let menuIndex = 0;
const menuOpts = ["1 Player", "2 Players (versus)", "How to cite (ML / research)"];

let mode1P = true;
let score = 0;
let p1Score = 0;
let p2Score = 0;
let stars = [];
let enemies = [];
let powerups = [];
let spawnAcc = 0;
let powerAcc = 0;
let slowUntil = 0;
let cheatsUsed = false;

const START_LIVES = 3;
let p1 = { x: W / 2, y: H - 50, r: 18, lives: START_LIVES, shields: 0, invUntil: 0 };
let p2 = { x: (3 * W) / 4, y: H - 50, r: 18, lives: START_LIVES, shields: 0, invUntil: 0 };
let p1Dead = false;
let p2Dead = false;
let winnerText = "";

const keys = new Set();
let mouseX = W / 2;
let mouseY = H / 2;

function initStars() {
  stars = [];
  for (let i = 0; i < 140; i++) {
    stars.push({
      x: Math.random() * W,
      y: Math.random() * H,
      sp: 20 + Math.random() * 100,
      br: 90 + Math.random() * 130,
      rad: Math.random() < 0.7 ? 1 : 2,
    });
  }
}

function drawStarfield(dt, drift = 1) {
  ctx.fillStyle = "rgb(10,14,32)";
  ctx.fillRect(0, 0, W, H);
  for (const s of stars) {
    s.y += s.sp * dt * 0.06 * drift;
    if (s.y > H) {
      s.y = 0;
      s.x = Math.random() * W;
    }
    const b = Math.min(255, s.br | 0);
    ctx.fillStyle = `rgb(${b},${b},${Math.min(255, b + 40)})`;
    ctx.beginPath();
    ctx.arc(s.x, s.y, s.rad, 0, Math.PI * 2);
    ctx.fill();
  }
}

function difficultyFactor(s) {
  return Math.min(1 + s / 3500, 2.35);
}

function resetMatch(oneP) {
  mode1P = oneP;
  score = 0;
  p1Score = 0;
  p2Score = 0;
  enemies = [];
  powerups = [];
  spawnAcc = 0;
  powerAcc = 0;
  slowUntil = 0;
  cheatsUsed = false;
  p1 = { x: W / (oneP ? 2 : 4), y: H - 50, r: 18, lives: START_LIVES, shields: 0, invUntil: 0 };
  p2 = { x: (3 * W) / 4, y: H - 50, r: 18, lives: START_LIVES, shields: 0, invUntil: 0 };
  p1Dead = false;
  p2Dead = false;
  winnerText = "";
  mouseX = p1.x;
  mouseY = p1.y;
}

function spawnEnemy(diff) {
  const lo = Math.max(2, (2 * diff) | 0);
  const hi = Math.max(lo + 1, (10 * diff) | 0);
  const size = 14 + (Math.random() * 34) | 0;
  const spd = lo + ((Math.random() * (hi - lo)) | 0);
  const x = Math.random() * (W - size);
  enemies.push({
    x,
    y: -size,
    w: size,
    h: size,
    vy: spd,
    hue: Math.random() < 0.5 ? "romulan" : "klingon",
  });
}

const POW_KINDS = [
  ["shield", [120, 200, 255]],
  ["slow", [255, 220, 100]],
  ["life", [120, 255, 160]],
  ["bonus", [255, 140, 200]],
];

function spawnPowerup() {
  const [kind, rgb] = POW_KINDS[(Math.random() * POW_KINDS.length) | 0];
  const r = 16;
  powerups.push({
    x: r + Math.random() * (W - 2 * r),
    y: -r * 2,
    r,
    vy: 3 + Math.random() * 3,
    kind,
    rgb,
  });
}

function drawShip(x, y, r, cold) {
  const g = ctx.createRadialGradient(x - 4, y - 4, 0, x, y, r * 1.5);
  if (cold) {
    g.addColorStop(0, "#e0f0ff");
    g.addColorStop(0.5, "#6090d0");
    g.addColorStop(1, "#304878");
  } else {
    g.addColorStop(0, "#ffe8e0");
    g.addColorStop(0.5, "#d08060");
    g.addColorStop(1, "#703828");
  }
  ctx.fillStyle = g;
  ctx.beginPath();
  ctx.moveTo(x, y - r);
  ctx.lineTo(x + r * 0.9, y + r * 0.8);
  ctx.lineTo(x - r * 0.9, y + r * 0.8);
  ctx.closePath();
  ctx.fill();
  ctx.strokeStyle = "rgba(255,255,255,.35)";
  ctx.lineWidth = 2;
  ctx.stroke();
}

function drawEnemy(e) {
  const cx = e.x + e.w / 2;
  const cy = e.y + e.h / 2;
  const grd = ctx.createRadialGradient(cx - e.w * 0.2, cy - e.h * 0.2, 0, cx, cy, e.w * 0.6);
  if (e.hue === "romulan") {
    grd.addColorStop(0, "#c080ff");
    grd.addColorStop(1, "#402060");
  } else {
    grd.addColorStop(0, "#ff9080");
    grd.addColorStop(1, "#602020");
  }
  ctx.fillStyle = grd;
  ctx.beginPath();
  ctx.arc(cx, cy, e.w * 0.45, 0, Math.PI * 2);
  ctx.fill();
  ctx.strokeStyle = "rgba(0,0,0,.4)";
  ctx.lineWidth = 2;
  ctx.stroke();
}

function drawPowerup(p) {
  const { x, y, r, rgb, kind } = p;
  const cx = x;
  const cy = y;
  ctx.fillStyle = `rgb(${rgb[0]},${rgb[1]},${rgb[2]})`;
  ctx.beginPath();
  ctx.arc(cx, cy, r, 0, Math.PI * 2);
  ctx.fill();
  ctx.strokeStyle = "#fff";
  ctx.lineWidth = 2;
  ctx.stroke();
  ctx.fillStyle = "#203020";
  if (kind === "life") {
    ctx.fillRect(cx - 6, cy - 2, 12, 4);
    ctx.fillRect(cx - 2, cy - 6, 4, 12);
  }
}

function drawText(text, x, y, size = 22, color = "#f0f4ff", shadow = true) {
  ctx.font = `bold ${size}px system-ui,Segoe UI,sans-serif`;
  if (shadow) {
    ctx.fillStyle = "rgba(0,0,0,.65)";
    ctx.fillText(text, x + 2, y + 2);
  }
  ctx.fillStyle = color;
  ctx.fillText(text, x, y);
}

function circHit(px, py, pr, ex, ey, ew, eh) {
  const cx = ex + ew / 2;
  const cy = ey + eh / 2;
  const cr = Math.min(ew, eh) * 0.42;
  const dx = px - cx;
  const dy = py - cy;
  return dx * dx + dy * dy < (pr + cr) * (pr + cr);
}

function nowMs() {
  return performance.now();
}

function collidesPl(ex, ey, ew, eh, pl) {
  return circHit(pl.x, pl.y, pl.r, ex, ey, ew, eh);
}

function hitPlayer(pl, powerupSound) {
  const t = nowMs();
  if (t < pl.invUntil) return false;
  if (pl.shields > 0) {
    pl.shields--;
    pl.invUntil = t + 400;
    if (powerupSound) playBeep(660, 0.05);
    return true;
  }
  pl.lives--;
  if (pl.lives <= 0) return true;
  pl.invUntil = t + 2200;
  return true;
}

let audioCtx = null;
function playBeep(freq, dur) {
  try {
    if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    const o = audioCtx.createOscillator();
    const g = audioCtx.createGain();
    o.connect(g);
    g.connect(audioCtx.destination);
    o.frequency.value = freq;
    g.gain.value = 0.06;
    o.start();
    o.stop(audioCtx.currentTime + dur);
  } catch (_) {}
}

function drawCiteOverlay() {
  drawStarfield(0.016, 0.5);
  drawText("Research & citations", W / 2 - 180, 80, 40, "#b8d4ff");
  const lines = [
    "Desktop + ML code: github.com/pat749/dodger-game",
    "See ml/README.md — tabular Q-learning on a formal dodge MDP.",
    "Cite: tabular RL baseline + stochastic obstacle field (repo README).",
    "Press Esc or Enter to return",
  ];
  let y = 160;
  for (const line of lines) {
    drawText(line, 60, y, 20, "#b0b8d0");
    y += 36;
  }
}

let last = performance.now();
function frame(t) {
  const dt = Math.min(0.05, (t - last) / 1000);
  last = t;

  if (state === STATE.MENU) {
    drawStarfield(dt, 1);
    drawText("ROMULAN WAR", W / 2 - 210, 100, 52, "#c8dcff");
    drawText("Survive the storm", W / 2 - 100, 155, 22, "#98a8c8");
    for (let i = 0; i < menuOpts.length; i++) {
      const sel = i === menuIndex;
      drawText((sel ? "> " : "  ") + menuOpts[i], W / 2 - 200, 300 + i * 48, 28, sel ? "#ffd87a" : "#c8c8e0");
    }
    drawText("↑↓ / W S · Enter · Esc quits menu cite view", W / 2 - 260, H - 48, 18, "#7888a8");
  } else if (state === STATE.CITE) {
    drawCiteOverlay();
  } else if (state === STATE.GAMEOVER) {
    drawStarfield(dt, 0.4);
    drawText("GAME OVER", W / 2 - 140, 200, 48, "#ff7878");
    if (winnerText) drawText(winnerText, W / 2 - 200, 280, 26, "#ffe0a0");
    if (mode1P) {
      drawText(`Score: ${score}`, W / 2 - 70, 340, 28);
    } else {
      drawText(`P1: ${p1Score}   P2: ${p2Score}`, W / 2 - 140, 340, 24);
    }
    drawText("Press any key for menu", W / 2 - 180, 420, 26, "#b8c8ff");
  } else if (state === STATE.PLAY) {
    const diffScore = mode1P ? score : Math.max(p1Score, p2Score);
    const diff = difficultyFactor(diffScore);
    const tMs = nowMs();
    const reverseCheat = mode1P && keys.has("z");
    const slowCheat = mode1P && keys.has("x");
    if (reverseCheat || slowCheat) cheatsUsed = true;
    const slowMo = tMs < slowUntil || slowCheat;

    if (!reverseCheat) spawnAcc += dt * 60;
    const spawnEvery = Math.max(8, (38 / diff) | 0);
    while (spawnAcc >= spawnEvery) {
      spawnAcc -= spawnEvery;
      spawnEnemy(diff);
      spawnEnemy(diff);
    }

    powerAcc += dt * 60;
    if (powerAcc >= 420 && powerups.length < 2 && Math.random() < 0.45) {
      powerAcc = 0;
      spawnPowerup();
    }

    const moveSp = 400 * dt;
    if (keys.has("a")) p1.x = Math.max(p1.r, p1.x - moveSp);
    if (keys.has("d")) p1.x = Math.min(W - p1.r, p1.x + moveSp);
    if (keys.has("w")) p1.y = Math.max(p1.r, p1.y - moveSp);
    if (keys.has("s")) p1.y = Math.min(H - p1.r, p1.y + moveSp);
    if (mode1P) {
      if (keys.has("arrowleft")) p1.x = Math.max(p1.r, p1.x - moveSp);
      if (keys.has("arrowright")) p1.x = Math.min(W - p1.r, p1.x + moveSp);
      if (keys.has("arrowup")) p1.y = Math.max(p1.r, p1.y - moveSp);
      if (keys.has("arrowdown")) p1.y = Math.min(H - p1.r, p1.y + moveSp);
      p1.x += (mouseX - p1.x) * Math.min(1, 14 * dt);
      p1.y += (mouseY - p1.y) * Math.min(1, 14 * dt);
      p1.x = Math.max(p1.r, Math.min(W - p1.r, p1.x));
      p1.y = Math.max(p1.r, Math.min(H - p1.r, p1.y));
    } else {
      if (keys.has("arrowleft")) p2.x = Math.max(p2.r, p2.x - moveSp);
      if (keys.has("arrowright")) p2.x = Math.min(W - p2.r, p2.x + moveSp);
      if (keys.has("arrowup")) p2.y = Math.max(p2.r, p2.y - moveSp);
      if (keys.has("arrowdown")) p2.y = Math.min(H - p2.r, p2.y + moveSp);
    }

    const vyMul = reverseCheat ? -0.5 : slowMo ? 0.38 : 1;
    for (const e of enemies) {
      e.y += e.vy * vyMul * dt * 60 * 0.4;
    }
    enemies = enemies.filter((e) => e.y < H + 80);

    for (const p of powerups) {
      p.y += p.vy * dt * 60 * 0.35;
    }
    powerups = powerups.filter((p) => p.y < H + 40);

    for (let i = powerups.length - 1; i >= 0; i--) {
      const p = powerups[i];
      const hit = (pl) => {
        const dx = pl.x - p.x;
        const dy = pl.y - p.y;
        return dx * dx + dy * dy < (pl.r + p.r) ** 2;
      };
      if (!p1Dead && hit(p1)) {
        applyPow(p, true);
        powerups.splice(i, 1);
        continue;
      }
      if (!mode1P && !p2Dead && hit(p2)) {
        applyPow(p, false);
        powerups.splice(i, 1);
      }
    }

    function applyPow(p, isP1) {
      playBeep(880, 0.04);
      const pl = isP1 ? p1 : p2;
      if (p.kind === "shield") pl.shields++;
      else if (p.kind === "slow") slowUntil = tMs + 4500;
      else if (p.kind === "life") pl.lives = Math.min(9, pl.lives + 1);
      else if (p.kind === "bonus") {
        if (mode1P) score += 350;
        else if (isP1) p1Score += 350;
        else p2Score += 350;
      }
    }

    for (let i = enemies.length - 1; i >= 0; i--) {
      const e = enemies[i];
      let removed = false;
      if (!p1Dead && collidesPl(e.x, e.y, e.w, e.h, p1)) {
        if (hitPlayer(p1, true)) {
          enemies.splice(i, 1);
          removed = true;
          if (p1.lives <= 0) p1Dead = true;
        }
      }
      if (!removed && !mode1P && !p2Dead && collidesPl(e.x, e.y, e.w, e.h, p2)) {
        if (hitPlayer(p2, true)) {
          enemies.splice(i, 1);
          if (p2.lives <= 0) p2Dead = true;
        }
      }
    }

    if (mode1P) {
      score++;
    } else {
      if (!p1Dead) p1Score++;
      if (!p2Dead) p2Score++;
    }

    let ended = false;
    if (mode1P && p1Dead) ended = true;
    if (!mode1P && (p1Dead || p2Dead)) {
      ended = true;
      if (p1Dead && p2Dead) winnerText = "Draw — both lost";
      else if (p1Dead) winnerText = "Player 2 wins";
      else winnerText = "Player 1 wins";
    }
    if (ended) {
      state = STATE.GAMEOVER;
      playBeep(120, 0.25);
      requestAnimationFrame(frame);
      return;
    }

    const drift = 0.85 + 0.15 * Math.min(diff, 2);
    drawStarfield(dt, drift);
    for (const e of enemies) drawEnemy(e);
    for (const p of powerups) drawPowerup(p);

    const blink = (pl) => tMs < pl.invUntil && ((tMs / 120) | 0) % 2 === 0;
    if (!p1Dead && !blink(p1)) drawShip(p1.x, p1.y, p1.r, true);
    if (p1.shields > 0) {
      ctx.strokeStyle = "rgba(100,180,255,.7)";
      ctx.lineWidth = 3;
      ctx.beginPath();
      ctx.arc(p1.x, p1.y, p1.r + 10, 0, Math.PI * 2);
      ctx.stroke();
    }
    if (!mode1P) {
      if (!p2Dead && !blink(p2)) drawShip(p2.x, p2.y, p2.r, false);
      if (p2.shields > 0) {
        ctx.strokeStyle = "rgba(255,160,130,.7)";
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.arc(p2.x, p2.y, p2.r + 10, 0, Math.PI * 2);
        ctx.stroke();
      }
    }

    if (mode1P) drawText(`Score ${score}`, 14, 32, 26);
    else drawText(`P1 ${p1Score}    P2 ${p2Score}`, 14, 32, 24);
    if (slowMo && !slowCheat) drawText("SLOW-MO", W - 110, 28, 18, "#ffd87a");
    if (mode1P) {
      drawText(`Lives ${p1.lives}`, W - 100, 60, 22, "#a8ffa8");
      if (p1.shields) drawText(`Shield ×${p1.shields}`, W - 120, 90, 18, "#a0d0ff");
    } else {
      drawText(`P1 ♥${p1.lives} sh ${p1.shields}`, 14, H - 72, 18);
      drawText(`P2 ♥${p2.lives} sh ${p2.shields}`, 14, H - 46, 18);
    }
    drawText("P pause · Esc menu", W - 220, H - 22, 16, "#687898");
  } else if (state === STATE.PAUSE) {
    drawStarfield(dt, 0.2);
    for (const e of enemies) drawEnemy(e);
    for (const p of powerups) drawPowerup(p);
    if (!p1Dead) drawShip(p1.x, p1.y, p1.r, true);
    if (!mode1P && !p2Dead) drawShip(p2.x, p2.y, p2.r, false);
    drawText("PAUSED", W / 2 - 90, H / 2 - 20, 44, "#fff8c0");
    drawText("P to resume", W / 2 - 80, H / 2 + 28, 24);
  }

  requestAnimationFrame(frame);
}

window.addEventListener("keydown", (ev) => {
  const k = ev.key.toLowerCase();
  if (k === "escape" && state === STATE.CITE) {
    state = STATE.MENU;
    ev.preventDefault();
    return;
  }
  if (state === STATE.CITE) {
    if (k === "enter" || k === " ") {
      state = STATE.MENU;
      ev.preventDefault();
    }
    return;
  }
  if (state === STATE.MENU) {
    if (k === "arrowup" || k === "w") menuIndex = (menuIndex + menuOpts.length - 1) % menuOpts.length;
    if (k === "arrowdown" || k === "s") menuIndex = (menuIndex + 1) % menuOpts.length;
    if (k === "enter" || k === " ") {
      if (menuIndex === 0) {
        resetMatch(true);
        state = STATE.PLAY;
        canvas.style.cursor = "none";
      } else if (menuIndex === 1) {
        resetMatch(false);
        state = STATE.PLAY;
        canvas.style.cursor = "default";
      } else {
        state = STATE.CITE;
      }
    }
    ev.preventDefault();
    return;
  }
  if (state === STATE.GAMEOVER) {
    state = STATE.MENU;
    canvas.style.cursor = "default";
    ev.preventDefault();
    return;
  }
  if (state === STATE.PLAY) {
    if (k === "escape") {
      state = STATE.MENU;
      canvas.style.cursor = "default";
      ev.preventDefault();
      return;
    }
    if (k === "p") {
      state = STATE.PAUSE;
      ev.preventDefault();
      return;
    }
  }
  if (state === STATE.PAUSE && k === "p") {
    state = STATE.PLAY;
    ev.preventDefault();
    return;
  }

  keys.add(k);
  if (ev.key === "ArrowLeft") keys.add("arrowleft");
  if (ev.key === "ArrowRight") keys.add("arrowright");
  if (ev.key === "ArrowUp") keys.add("arrowup");
  if (ev.key === "ArrowDown") keys.add("arrowdown");
});

window.addEventListener("keyup", (ev) => {
  const k = ev.key.toLowerCase();
  keys.delete(k);
  if (ev.key === "ArrowLeft") keys.delete("arrowleft");
  if (ev.key === "ArrowRight") keys.delete("arrowright");
  if (ev.key === "ArrowUp") keys.delete("arrowup");
  if (ev.key === "ArrowDown") keys.delete("arrowdown");
});

canvas.addEventListener("mousemove", (ev) => {
  const r = canvas.getBoundingClientRect();
  const sx = W / r.width;
  const sy = H / r.height;
  mouseX = (ev.clientX - r.left) * sx;
  mouseY = (ev.clientY - r.top) * sy;
});

initStars();
requestAnimationFrame(frame);
