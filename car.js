/**
 * Neon Circuit — oval track, engine sound (Web Audio), Human / AI solo / Human vs AI.
 */

const W = 880;
const H = 720;
const cx = W / 2;
const cy = H / 2;
const rx = 320;
const ry = 190;
const D_IN = 0.84;
const D_OUT = 1.06;
const TARGET_LAPS = 3;

const canvas = document.getElementById("car");
const ctx = canvas.getContext("2d");
const keys = new Set();

const MODE_MENU = 0;
const MODE_PLAY = 1;
const MODE_RESULT = 2;

let screenMode = MODE_MENU;
let menuIndex = 0;
/** @type {"human" | "ai_solo" | "versus"} */
let playMode = "human";

/** Loaded from `dqn_car_policy.json` (run `python -m ml.export_dqn_car_web` after training). */
let dqnPolicy = null;
let dqnReady = false;
/** Press L during play to toggle DQN vs hand-tuned PD when a policy file exists. */
let dqnUseLearned = true;

let lastT = performance.now();

/* ---- Web Audio engine ---- */
let audioCtx = null;
let engineOsc = null;
let engineGain = null;
let audioReady = false;

function initAudio() {
  if (audioCtx) return;
  const AC = window.AudioContext || window.webkitAudioContext;
  if (!AC) return;
  audioCtx = new AC();
  engineOsc = audioCtx.createOscillator();
  engineOsc.type = "sawtooth";
  engineGain = audioCtx.createGain();
  engineGain.gain.value = 0;
  const filt = audioCtx.createBiquadFilter();
  filt.type = "lowpass";
  filt.frequency.value = 2800;
  engineOsc.connect(filt);
  filt.connect(engineGain);
  engineGain.connect(audioCtx.destination);
  engineOsc.start();
  audioReady = true;
}

async function unlockAudio() {
  initAudio();
  if (audioCtx && audioCtx.state === "suspended") await audioCtx.resume();
}

function setEngineSound(throttle, speed, humanDriving) {
  if (!audioReady || !engineOsc || !engineGain) return;
  const t = Math.max(0, Math.min(1, throttle));
  const sp = Math.max(0, Math.min(1, speed / 320));
  const base = 55 + sp * 95 + t * 70;
  engineOsc.frequency.setTargetAtTime(base, audioCtx.currentTime, 0.04);
  const vol = humanDriving ? 0.04 + t * 0.1 + sp * 0.06 : 0.03 + sp * 0.08;
  engineGain.gain.setTargetAtTime(vol, audioCtx.currentTime, 0.05);
}

function muteEngine() {
  if (engineGain && audioCtx)
    engineGain.gain.setTargetAtTime(0, audioCtx.currentTime, 0.08);
}

/* ---- Car factory ---- */
function makeCar(x, y, ang, colorCold) {
  return {
    x,
    y,
    ang,
    vel: 0,
    throttle: 0,
    steer: 0,
    laps: 0,
    psiAccum: 0,
    lastPsi: ellipsePsi(x, y),
    colorCold,
    name: "",
  };
}

function ellipsePsi(x, y) {
  return Math.atan2((y - cy) / ry, (x - cx) / rx);
}

function normEllipseD(x, y) {
  const nx = (x - cx) / rx;
  const ny = (y - cy) / ry;
  return Math.hypot(nx, ny);
}

function clampToTrack(x, y) {
  const psi = Math.atan2((y - cy) / ry, (x - cx) / rx);
  const mid = 0.94;
  return {
    x: cx + mid * rx * Math.cos(psi),
    y: cy + mid * ry * Math.sin(psi),
  };
}

function constrainCar(car) {
  const d = normEllipseD(car.x, car.y);
  if (d < D_IN || d > D_OUT) {
    const p = clampToTrack(car.x, car.y);
    car.x = p.x;
    car.y = p.y;
    car.vel *= 0.55;
  }
}

function tangentAngle(psi) {
  return Math.atan2(ry * Math.cos(psi), -rx * Math.sin(psi));
}

function wrapAng(a) {
  while (a > Math.PI) a -= Math.PI * 2;
  while (a < -Math.PI) a += Math.PI * 2;
  return a;
}

function updateLaps(car) {
  const psi = ellipsePsi(car.x, car.y);
  let delta = psi - car.lastPsi;
  if (delta > Math.PI) delta -= Math.PI * 2;
  if (delta < -Math.PI) delta += Math.PI * 2;
  car.psiAccum += delta;
  car.lastPsi = psi;
  while (car.psiAccum >= Math.PI * 2) {
    car.laps++;
    car.psiAccum -= Math.PI * 2;
  }
  while (car.psiAccum <= -Math.PI * 2) {
    car.laps--;
    car.psiAccum += Math.PI * 2;
  }
}

/* ---- DQN in browser (matches discrete ml/car_env.py encoding) ---- */
const DQN_N_ANG = 36;
const DQN_N_OFF = 9;
const DQN_N_SPD = 6;

function carToDqnObs(car) {
  const psi = ellipsePsi(car.x, car.y);
  let ang = Math.floor(((psi + Math.PI) / (Math.PI * 2)) * DQN_N_ANG);
  ang = ((ang % DQN_N_ANG) + DQN_N_ANG) % DQN_N_ANG;
  const d = normEllipseD(car.x, car.y);
  let off = Math.round(((d - D_IN) / (D_OUT - D_IN)) * (DQN_N_OFF - 1));
  off = Math.max(0, Math.min(DQN_N_OFF - 1, off));
  const maxV = 340;
  let spd = Math.min(
    DQN_N_SPD - 1,
    Math.floor((Math.abs(car.vel) / maxV) * DQN_N_SPD)
  );
  if (Math.abs(car.vel) < 6) spd = 0;
  return ang * (DQN_N_OFF * DQN_N_SPD) + off * DQN_N_SPD + spd;
}

function dqnLinear(x, W, b) {
  const out = new Array(W.length);
  for (let r = 0; r < W.length; r++) {
    const row = W[r];
    let s = b[r];
    for (let c = 0; c < x.length; c++) s += row[c] * x[c];
    out[r] = s;
  }
  return out;
}

function dqnLinearRelu(x, W, b) {
  const y = dqnLinear(x, W, b);
  for (let i = 0; i < y.length; i++) if (y[i] < 0) y[i] = 0;
  return y;
}

function dqnForward(policy, obs) {
  const x0 = policy.emb_w[obs];
  const x1 = dqnLinearRelu(x0, policy.fc1_w, policy.fc1_b);
  const x2 = dqnLinearRelu(x1, policy.fc2_w, policy.fc2_b);
  return dqnLinear(x2, policy.fc3_w, policy.fc3_b);
}

function applyDqnAction(car, action) {
  const lat = Math.floor(action / 3);
  const thr = action % 3;
  car.steer = lat === 0 ? -1 : lat === 2 ? 1 : 0;
  car.throttle = thr === 0 ? -0.65 : thr === 1 ? 0.45 : 1;
}

function dqnControl(car) {
  if (!dqnPolicy) return;
  const obs = carToDqnObs(car);
  const q = dqnForward(dqnPolicy, obs);
  let best = 0;
  for (let i = 1; i < q.length; i++) if (q[i] > q[best]) best = i;
  applyDqnAction(car, best);
}

function updateCarPhysics(car, dt, humanControl) {
  const accel = 520;
  const friction = 0.978;
  const maxV = 340;
  const turn = 3.2;

  if (humanControl) {
    let thr = 0;
    if (keys.has("w") || keys.has("arrowup")) thr += 1;
    if (keys.has("s") || keys.has("arrowdown")) thr -= 0.65;
    let st = 0;
    if (keys.has("a") || keys.has("arrowleft")) st -= 1;
    if (keys.has("d") || keys.has("arrowright")) st += 1;
    car.throttle = thr;
    car.steer = st;
  }

  car.vel += car.throttle * accel * dt;
  car.vel *= friction;
  car.vel = Math.max(-120, Math.min(maxV, car.vel));
  const spf = Math.min(1, Math.abs(car.vel) / maxV);
  car.ang += car.steer * turn * spf * dt * Math.sign(car.vel || 1);
  car.x += Math.cos(car.ang) * car.vel * dt;
  car.y += Math.sin(car.ang) * car.vel * dt;
  constrainCar(car);
  updateLaps(car);
}

function aiControl(car, bias, dt) {
  const psi = ellipsePsi(car.x, car.y);
  const want = tangentAngle(psi) + bias;
  const diff = wrapAng(want - car.ang);
  car.steer = Math.max(-1, Math.min(1, diff * 2.2));
  const err = Math.abs(diff);
  car.throttle = err > 0.35 ? 0.45 : 0.92 + 0.08 * Math.sin(performance.now() / 260);
}

function drawTrack() {
  ctx.fillStyle = "#0b0f1e";
  ctx.fillRect(0, 0, W, H);

  ctx.strokeStyle = "rgba(80,120,220,.15)";
  ctx.lineWidth = 1;
  for (let i = 0; i < 24; i++) {
    ctx.beginPath();
    const a = (i / 24) * Math.PI * 2;
    ctx.moveTo(cx + 40 * Math.cos(a), cy + 40 * Math.sin(a));
    ctx.lineTo(cx + (rx * 1.4) * Math.cos(a), cy + (ry * 1.4) * Math.sin(a));
    ctx.stroke();
  }

  ctx.beginPath();
  for (let i = 0; i <= 64; i++) {
    const t = (i / 64) * Math.PI * 2;
    const x = cx + D_OUT * rx * Math.cos(t);
    const y = cy + D_OUT * ry * Math.sin(t);
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  }
  ctx.closePath();
  ctx.fillStyle = "#151a2e";
  ctx.fill();
  ctx.strokeStyle = "#3a5080";
  ctx.lineWidth = 4;
  ctx.stroke();

  ctx.beginPath();
  for (let i = 0; i <= 64; i++) {
    const t = (i / 64) * Math.PI * 2;
    const x = cx + D_IN * rx * Math.cos(t);
    const y = cy + D_IN * ry * Math.sin(t);
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  }
  ctx.closePath();
  ctx.fillStyle = "#0b0f1e";
  ctx.fill();

  ctx.strokeStyle = "#5cf0c8";
  ctx.lineWidth = 3;
  ctx.setLineDash([14, 18]);
  ctx.beginPath();
  for (let i = 0; i <= 64; i++) {
    const t = (i / 64) * Math.PI * 2;
    const x = cx + 0.94 * rx * Math.cos(t);
    const y = cy + 0.94 * ry * Math.sin(t);
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  }
  ctx.closePath();
  ctx.stroke();
  ctx.setLineDash([]);

  ctx.fillStyle = "rgba(92,240,200,.12)";
  ctx.fillRect(cx - 6, cy - 8, 12, 16);
}

function drawCar(car, label) {
  ctx.save();
  ctx.translate(car.x, car.y);
  ctx.rotate(car.ang);
  const w = 34;
  const h = 18;
  const g = ctx.createLinearGradient(-w / 2, 0, w / 2, 0);
  if (car.colorCold) {
    g.addColorStop(0, "#80e8ff");
    g.addColorStop(1, "#2068a8");
  } else {
    g.addColorStop(0, "#ff9088");
    g.addColorStop(1, "#882018");
  }
  ctx.fillStyle = g;
  ctx.fillRect(-w / 2, -h / 2, w, h);
  ctx.strokeStyle = "rgba(255,255,255,.45)";
  ctx.lineWidth = 2;
  ctx.strokeRect(-w / 2, -h / 2, w, h);
  ctx.fillStyle = "#fff";
  ctx.fillRect(w / 2 - 10, -3, 8, 6);
  ctx.restore();

  if (label) {
    ctx.font = "bold 14px system-ui";
    ctx.fillStyle = "#b8c8e8";
    ctx.fillText(label, car.x - 20, car.y - 28);
    ctx.fillText(`Laps ${Math.max(0, car.laps)}/${TARGET_LAPS}`, car.x - 38, car.y + 42);
  }
}

let humanCar = null;
let aiCar = null;
let resultMsg = "";
let resultTimer = 0;

function resetRace() {
  const psi0 = -Math.PI / 2;
  const px = cx + 0.94 * rx * Math.cos(psi0 + 0.08);
  const py = cy + 0.94 * ry * Math.sin(psi0 + 0.08);
  const tang = tangentAngle(psi0 + 0.08);
  humanCar = makeCar(px - 22, py - 6, tang, true);
  humanCar.name = "You";
  aiCar = makeCar(px + 22, py + 8, tang, false);
  aiCar.name = "AI";
  resultMsg = "";
}

function startMode(mode) {
  playMode = mode;
  screenMode = MODE_PLAY;
  if (mode === "human") {
    aiCar = null;
    humanCar = makeCar(cx + 0.94 * rx * Math.cos(-1.2), cy + 0.94 * ry * Math.sin(-1.2), tangentAngle(-1.2), true);
    humanCar.name = "You";
  } else if (mode === "ai_solo") {
    humanCar = null;
    aiCar = makeCar(cx + 0.94 * rx * Math.cos(0.5), cy + 0.94 * ry * Math.sin(0.5), tangentAngle(0.5), false);
    aiCar.name = "Autopilot";
  } else {
    resetRace();
  }
}

function frame(t) {
  const dt = Math.min(0.045, (t - lastT) / 1000);
  lastT = t;

  if (screenMode === MODE_MENU) {
    drawTrack();
    ctx.font = "bold 48px system-ui";
    ctx.fillStyle = "#c8e0ff";
    ctx.fillText("NEON CIRCUIT", W / 2 - 200, 120);
    const opts = [
      ["Human drive", "human"],
      ["AI autopilot (demo)", "ai_solo"],
      ["Human vs AI (race)", "versus"],
    ];
    for (let i = 0; i < opts.length; i++) {
      const sel = i === menuIndex;
      ctx.font = `bold ${sel ? 28 : 24}px system-ui`;
      ctx.fillStyle = sel ? "#ffd87a" : "#a8b8d8";
      ctx.fillText((sel ? "> " : "  ") + opts[i][0], W / 2 - 220, 280 + i * 52);
    }
    ctx.font = "18px system-ui";
    ctx.fillStyle = "#7080a0";
    ctx.fillText("↑↓ / W S · Enter · Esc back to Arcade Lab (browser back)", W / 2 - 280, H - 52);
    ctx.font = "15px system-ui";
    ctx.fillStyle = dqnReady ? "#6a9" : "#865";
    ctx.fillText(
      dqnReady
        ? "Neural policy loaded — AI uses DQN (press L in race to toggle vs heuristic)"
        : "No dqn_car_policy.json — run: python3 -m ml.export_dqn_car_web (then refresh)",
      W / 2 - 360,
      H - 24
    );
    requestAnimationFrame(frame);
    return;
  }

  if (screenMode === MODE_RESULT) {
    drawTrack();
    ctx.font = "bold 36px system-ui";
    ctx.fillStyle = "#ffe0a0";
    ctx.fillText(resultMsg, W / 2 - resultMsg.length * 10, H / 2);
    ctx.font = "22px system-ui";
    ctx.fillStyle = "#a0b0d0";
    ctx.fillText("Enter / Space for menu", W / 2 - 160, H / 2 + 48);
    resultTimer += dt;
    requestAnimationFrame(frame);
    return;
  }

  /* PLAY */
  drawTrack();

  if (playMode === "human" && humanCar) {
    updateCarPhysics(humanCar, dt, true);
    drawCar(humanCar, humanCar.name);
    setEngineSound(
      Math.max(0, humanCar.throttle),
      Math.abs(humanCar.vel),
      true
    );
  } else if (playMode === "ai_solo" && aiCar) {
    if (dqnReady && dqnUseLearned) dqnControl(aiCar);
    else {
      aiControl(aiCar, 0, dt);
      aiCar.throttle = Math.max(0.2, aiCar.throttle);
    }
    updateCarPhysics(aiCar, dt, false);
    drawCar(aiCar, aiCar.name);
    setEngineSound(Math.max(0.15, aiCar.throttle), Math.abs(aiCar.vel), false);
  } else if (playMode === "versus" && humanCar && aiCar) {
    updateCarPhysics(humanCar, dt, true);
    if (dqnReady && dqnUseLearned) dqnControl(aiCar);
    else aiControl(aiCar, 0.02 * Math.sin(t / 900), dt);
    updateCarPhysics(aiCar, dt, false);
    drawCar(humanCar, humanCar.name);
    drawCar(aiCar, aiCar.name);
    const mixThr = Math.min(1, Math.max(0, humanCar.throttle) * 0.62 + Math.max(0.15, aiCar.throttle) * 0.48);
    const mixSpd = (Math.abs(humanCar.vel) + Math.abs(aiCar.vel)) * 0.5;
    setEngineSound(mixThr, mixSpd, true);

    if (humanCar.laps >= TARGET_LAPS) {
      resultMsg = "You win!";
      screenMode = MODE_RESULT;
      muteEngine();
    } else if (aiCar.laps >= TARGET_LAPS) {
      resultMsg = "AI wins!";
      screenMode = MODE_RESULT;
      muteEngine();
    }
  }

  if (playMode === "versus") {
    ctx.font = "bold 20px system-ui";
    ctx.fillStyle = "#8ab";
    ctx.fillText("First to 3 laps · Cyan = you · Red = AI", 20, 28);
  }
  if (playMode === "ai_solo" || playMode === "versus") {
    ctx.font = "14px system-ui";
    ctx.fillStyle = "#7088a8";
    const tag =
      !dqnReady
        ? "Red car: heuristic AI"
        : dqnUseLearned
          ? "Red car: DQN (L — heuristic)"
          : "Red car: heuristic (L — DQN)";
    ctx.fillText(tag, 20, H - 48);
  }
  ctx.font = "16px system-ui";
  ctx.fillStyle = "#607090";
  ctx.fillText("Esc — menu", W - 120, H - 20);

  requestAnimationFrame(frame);
}

canvas.addEventListener("click", () => unlockAudio());

window.addEventListener("keydown", (ev) => {
  const k = ev.key.toLowerCase();
  if (screenMode === MODE_PLAY && k === "escape") {
    screenMode = MODE_MENU;
    muteEngine();
    ev.preventDefault();
    return;
  }
  if (screenMode === MODE_PLAY && k === "l" && dqnReady) {
    dqnUseLearned = !dqnUseLearned;
    ev.preventDefault();
    return;
  }
  if (screenMode === MODE_RESULT && (k === "enter" || k === " ")) {
    screenMode = MODE_MENU;
    ev.preventDefault();
    return;
  }
  if (screenMode === MODE_MENU) {
    const optsLen = 3;
    if (k === "arrowup" || k === "w") menuIndex = (menuIndex + optsLen - 1) % optsLen;
    if (k === "arrowdown" || k === "s") menuIndex = (menuIndex + 1) % optsLen;
    if (k === "enter" || k === " ") {
      const modes = ["human", "ai_solo", "versus"];
      startMode(/** @type {any} */ (modes[menuIndex]));
    }
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

fetch("dqn_car_policy.json", { cache: "no-store" })
  .then((r) => (r.ok ? r.json() : Promise.reject(new Error("missing"))))
  .then((data) => {
    if (data && data.version === 1 && Array.isArray(data.emb_w)) {
      dqnPolicy = data;
      dqnReady = true;
    }
  })
  .catch(() => {
    dqnPolicy = null;
    dqnReady = false;
  });

requestAnimationFrame(frame);
