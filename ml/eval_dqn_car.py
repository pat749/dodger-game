"""
Evaluate a saved car DQN with greedy action selection; optional rollout logging.

  python3 -m ml.eval_dqn_car --episodes 200
  python3 -m ml.eval_dqn_car --episodes 500 --log-csv ml/logs/rollouts.csv
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import numpy as np

from .car_env import CarRingEnv
from .train_dqn_car import QNetwork

try:
    import torch
except ImportError as e:
    raise SystemExit("pip install -r requirements-ml-rl.txt") from e


@torch.no_grad()
def greedy_action(policy: QNetwork, obs: int) -> int:
    q = policy(torch.tensor([obs], dtype=torch.long))
    return int(q.argmax(dim=1).item())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--checkpoint", type=Path, default=Path(__file__).resolve().parent / "checkpoints" / "dqn_car.pt")
    ap.add_argument("--episodes", type=int, default=300)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--horizon", type=int, default=800, help="Max steps per episode")
    ap.add_argument("--log-csv", type=Path, default=None, help="Append (s,a,r,s',done) rows")
    args = ap.parse_args()

    ckpt = torch.load(args.checkpoint, map_location="cpu")
    n_states = int(ckpt["n_states"])
    n_actions = int(ckpt["n_actions"])
    policy = QNetwork(n_states, n_actions)
    policy.load_state_dict(ckpt["policy"])
    policy.eval()

    rng = np.random.default_rng(args.seed)
    returns: list[float] = []
    lengths: list[int] = []

    log_f = None
    log_w = None
    if args.log_csv:
        args.log_csv.parent.mkdir(parents=True, exist_ok=True)
        new_file = not args.log_csv.exists()
        log_f = open(args.log_csv, "a", newline="", encoding="utf-8")
        log_w = csv.writer(log_f)
        if new_file:
            log_w.writerow(["episode", "t", "obs", "action", "reward", "next_obs", "done"])

    for ep in range(args.episodes):
        env = CarRingEnv(seed=int(rng.integers(0, 2**31)))
        obs = env.reset()
        total = 0.0
        for t in range(args.horizon):
            a = greedy_action(policy, obs)
            step = env.step(a)
            total += step.reward
            if log_w is not None:
                log_w.writerow([ep, t, obs, a, step.reward, step.observation, int(step.terminated)])
            obs = step.observation
            if step.terminated:
                break
        returns.append(total)
        lengths.append(t + 1)

    if log_f is not None:
        log_f.close()

    arr = np.array(returns, dtype=np.float64)
    print(
        f"{args.episodes} episodes: return mean={arr.mean():.3f} std={arr.std():.3f} "
        f"median={np.median(arr):.3f} len_mean={np.mean(lengths):.1f}"
    )


if __name__ == "__main__":
    main()
