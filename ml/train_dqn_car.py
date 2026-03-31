"""
Deep Q-Network (DQN) on `CarRingEnv` — optional **PyTorch** deep RL baseline.

Install:  pip install -r requirements-ml-rl.txt
Run:      python3 -m ml.train_dqn_car --steps 15000

Saves weights to ml/checkpoints/dqn_car.pt (gitignored).
"""

from __future__ import annotations

import argparse
import random
from collections import deque
from pathlib import Path

import numpy as np

from .car_env import CarRingEnv

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
except ImportError as e:
    raise SystemExit(
        "PyTorch is required. Install with: pip install -r requirements-ml-rl.txt\n" + str(e)
    ) from e


class QNetwork(nn.Module):
    def __init__(self, n_states: int, n_actions: int, emb_dim: int = 64):
        super().__init__()
        self.emb = nn.Embedding(n_states, emb_dim)
        self.net = nn.Sequential(
            nn.Linear(emb_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 128),
            nn.ReLU(),
            nn.Linear(128, n_actions),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(self.emb(x))


def train_loop(steps: int, lr: float, gamma: float, eps_start: float, eps_end: float, seed: int, batch: int, tgt_update: int) -> None:
    torch.manual_seed(seed)
    random.seed(seed)
    np.random.seed(seed)

    env = CarRingEnv(seed=seed)
    n_states = CarRingEnv.N_ANG * CarRingEnv.N_OFF * CarRingEnv.N_SPD
    n_actions = 9
    policy = QNetwork(n_states, n_actions)
    target = QNetwork(n_states, n_actions)
    target.load_state_dict(policy.state_dict())
    opt = optim.Adam(policy.parameters(), lr=lr)
    replay: deque[tuple[int, int, float, int, bool]] = deque(maxlen=50_000)

    def eps_for(u: int) -> float:
        t = min(1.0, u / max(1, steps))
        return eps_end + (eps_start - eps_end) * (1.0 - t)

    obs = env.reset()
    losses: list[float] = []
    for u in range(steps):
        e = eps_for(u)
        if random.random() < e:
            a = random.randrange(n_actions)
        else:
            with torch.no_grad():
                q = policy(torch.tensor([obs], dtype=torch.long))
                a = int(q.argmax(dim=1).item())

        step = env.step(a)
        nxt = step.observation
        replay.append((obs, a, step.reward, nxt, step.terminated))
        obs = nxt if not step.terminated else env.reset()

        if len(replay) >= batch:
            batch_s = random.sample(replay, batch)
            o, act, r, nx, d = zip(*batch_s)
            o_t = torch.tensor(o, dtype=torch.long)
            a_t = torch.tensor(act, dtype=torch.long)
            r_t = torch.tensor(r, dtype=torch.float32)
            nx_t = torch.tensor(nx, dtype=torch.long)
            d_t = torch.tensor(d, dtype=torch.float32)

            with torch.no_grad():
                q_next = target(nx_t).max(1)[0]
                y = r_t + gamma * q_next * (1.0 - d_t)

            q = policy(o_t).gather(1, a_t.unsqueeze(1)).squeeze(1)
            loss = nn.functional.mse_loss(q, y)
            opt.zero_grad()
            loss.backward()
            opt.step()
            losses.append(float(loss.item()))

        if u > 0 and u % tgt_update == 0:
            target.load_state_dict(policy.state_dict())

    out = Path(__file__).resolve().parent / "checkpoints" / "dqn_car.pt"
    out.parent.mkdir(exist_ok=True)
    torch.save({"policy": policy.state_dict(), "n_states": n_states, "n_actions": n_actions}, out)
    print(f"Saved {out} after {steps} env steps (mean last 500 loss {np.mean(losses[-500:]):.4f} if available)")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, default=20_000)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--gamma", type=float, default=0.99)
    ap.add_argument("--eps-start", type=float, default=0.35)
    ap.add_argument("--eps-end", type=float, default=0.05)
    ap.add_argument("--batch", type=int, default=64)
    ap.add_argument("--target-update", type=int, default=200)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    train_loop(args.steps, args.lr, args.gamma, args.eps_start, args.eps_end, args.seed, args.batch, args.target_update)


if __name__ == "__main__":
    main()
