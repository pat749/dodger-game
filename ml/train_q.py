"""
Tabular Q-learning (optional Double Q-learning) on DodgeEnv.

Double Q reduces overestimation bias and usually yields a stronger greedy policy.
Epsilon decays exponentially so the agent keeps exploring late in training.

Run:  python3 -m ml.train_q
"""

from __future__ import annotations

import argparse
import json
import math
import random
from collections import defaultdict
from pathlib import Path

import numpy as np

from .dodge_env import DodgeEnv


def state_key(s: tuple[int, ...]) -> str:
    return json.dumps(list(s))


def _epsilon(ep: int, episodes: int, eps_start: float, eps_end: float) -> float:
    """Exponential decay: more exploration mid-training than a linear schedule."""
    if episodes <= 1:
        return eps_end
    z = 6.0 * ep / (episodes - 1)
    return eps_end + (eps_start - eps_end) * math.exp(-z)


def train(
    episodes: int,
    alpha: float,
    gamma: float,
    eps_start: float,
    eps_end: float,
    seed: int,
    double_q: bool,
    optimism: float,
) -> dict[str, list[float]]:
    env = DodgeEnv(seed=seed)
    rng = random.Random(seed)

    def new_q():
        return defaultdict(lambda: np.full(3, optimism, dtype=np.float64))

    Q1 = new_q()
    Q2 = new_q() if double_q else None

    for ep in range(episodes):
        epsilon = _epsilon(ep, episodes, eps_start, eps_end)
        s = env.reset()
        done = False
        steps = 0
        while not done and steps < 8000:
            sk = state_key(s)
            if rng.random() < epsilon:
                a = rng.randint(0, 2)
            else:
                if double_q:
                    qa = Q1[sk] + Q2[sk]
                else:
                    qa = Q1[sk]
                a = int(np.argmax(qa))

            step = env.step(a)
            s2 = step.observation
            r = step.reward
            done = step.terminated
            sk2 = state_key(s2)
            steps += 1

            if double_q:
                assert Q2 is not None
                if rng.random() < 0.5:
                    a_star = int(np.argmax(Q1[sk2]))
                    nxt = 0.0 if done else Q2[sk2][a_star]
                    td = r + gamma * nxt - Q1[sk][a]
                    Q1[sk][a] += alpha * td
                else:
                    a_star = int(np.argmax(Q2[sk2]))
                    nxt = 0.0 if done else Q1[sk2][a_star]
                    td = r + gamma * nxt - Q2[sk][a]
                    Q2[sk][a] += alpha * td
            else:
                nxt = 0.0 if done else float(np.max(Q1[sk2]))
                td = r + gamma * nxt - Q1[sk][a]
                Q1[sk][a] += alpha * td

            s = s2

    all_keys = set(Q1.keys())
    if double_q and Q2 is not None:
        all_keys |= set(Q2.keys())
    merged: dict[str, list[float]] = {}
    for k in all_keys:
        v = np.zeros(3, dtype=np.float64)
        if k in Q1:
            v += Q1[k]
        if double_q and Q2 is not None and k in Q2:
            v += Q2[k]
        merged[k] = v.tolist()
    return merged


def main() -> None:
    parser = argparse.ArgumentParser(description="Tabular Q-learning on dodge MDP")
    parser.add_argument("--episodes", type=int, default=35_000)
    parser.add_argument("--alpha", type=float, default=0.18)
    parser.add_argument("--gamma", type=float, default=0.99)
    parser.add_argument("--eps-start", type=float, default=0.55)
    parser.add_argument("--eps-end", type=float, default=0.03)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument(
        "--no-double",
        action="store_true",
        help="Use single Q-learning instead of Double Q (usually weaker).",
    )
    parser.add_argument(
        "--optimism",
        type=float,
        default=1.5,
        help="Initial Q per action (small optimism boosts early exploration).",
    )
    args = parser.parse_args()

    q_dict = train(
        args.episodes,
        args.alpha,
        args.gamma,
        args.eps_start,
        args.eps_end,
        args.seed,
        double_q=not args.no_double,
        optimism=args.optimism,
    )

    out = Path(__file__).resolve().parent / "checkpoints"
    out.mkdir(exist_ok=True)
    path = out / "q_table.json"
    path.write_text(json.dumps(q_dict), encoding="utf-8")
    print(f"Wrote {len(q_dict)} states to {path}")
    print(
        f"Settings: episodes={args.episodes} alpha={args.alpha} gamma={args.gamma} "
        f"double_q={not args.no_double} optimism={args.optimism}"
    )

    loaded = {k: np.array(v, dtype=np.float64) for k, v in json.loads(path.read_text(encoding="utf-8")).items()}
    totals = []
    eval_horizon = 8000
    for i in range(300):
        env = DodgeEnv(seed=50_000 + i)
        s = env.reset()
        G = 0.0
        for _ in range(eval_horizon):
            sk = state_key(s)
            qa = loaded.get(sk, np.zeros(3, dtype=np.float64))
            a = int(np.argmax(qa))
            step = env.step(a)
            G += step.reward
            s = step.observation
            if step.terminated:
                break
        totals.append(G)
    print(
        f"Greedy eval over {len(totals)} episodes (horizon {eval_horizon}): "
        f"mean return = {np.mean(totals):.2f} ± {np.std(totals):.2f} "
        f"(median {np.median(totals):.0f})"
    )


if __name__ == "__main__":
    main()
