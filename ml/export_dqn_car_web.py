"""
Export trained DQN weights to `web/dqn_car_policy.json` for browser inference.

Run from repo root after training:
  python3 -m ml.export_dqn_car_web
  python3 -m ml.export_dqn_car_web --checkpoint ml/checkpoints/custom.pt --out web/dqn_car_policy.json

The JSON is large (~0.5–1 MB); add to Pages only if you want the live site to run DQN (or load from release asset).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from .car_env import CarRingEnv

try:
    import torch
except ImportError as e:
    raise SystemExit("pip install -r requirements-ml-rl.txt") from e


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--checkpoint",
        type=Path,
        default=Path(__file__).resolve().parent / "checkpoints" / "dqn_car.pt",
    )
    ap.add_argument("--out", type=Path, default=Path(__file__).resolve().parents[1] / "web" / "dqn_car_policy.json")
    args = ap.parse_args()

    data = torch.load(args.checkpoint, map_location="cpu")
    n_states = int(data["n_states"])
    n_actions = int(data["n_actions"])
    sd = data["policy"]
    emb_dim = sd["emb.weight"].shape[1]

    def tolist(t):
        return t.detach().float().cpu().numpy().astype(np.float64).tolist()

    payload = {
        "version": 1,
        "n_states": n_states,
        "n_actions": n_actions,
        "emb_dim": emb_dim,
        "n_ang": CarRingEnv.N_ANG,
        "n_off": CarRingEnv.N_OFF,
        "n_spd": CarRingEnv.N_SPD,
        "emb_w": tolist(sd["emb.weight"]),
        "fc1_w": tolist(sd["net.0.weight"]),
        "fc1_b": tolist(sd["net.0.bias"]),
        "fc2_w": tolist(sd["net.2.weight"]),
        "fc2_b": tolist(sd["net.2.bias"]),
        "fc3_w": tolist(sd["net.4.weight"]),
        "fc3_b": tolist(sd["net.4.bias"]),
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(payload, f, separators=(",", ":"))

    size_mb = args.out.stat().st_size / (1024 * 1024)
    print(f"Wrote {args.out} ({size_mb:.2f} MB)")


if __name__ == "__main__":
    main()
