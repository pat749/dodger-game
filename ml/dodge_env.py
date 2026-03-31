"""
Discrete dodge-survival MDP for reinforcement learning (no graphics).

Formulation (good for a methods / RL side project):
- Partially observable in the full game; here we expose a fixed *sufficient statistic*
  of nearby hazards so tabular methods remain tractable.
- Actions: move left, stay, move right on a 1D lane graph.
- Stochastic exogenous process: hazards spawn i.i.d. at the top with probability p.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class StepResult:
    observation: tuple[int, ...]
    reward: float
    terminated: bool


class DodgeEnv:
    N_LANES = 9
    N_ROWS = 8
    SPAWN_P = 0.34

    def __init__(self, seed: int | None = 0) -> None:
        self.rng = np.random.default_rng(seed)
        self.player_lane = self.N_LANES // 2
        self.grid = np.zeros((self.N_ROWS, self.N_LANES), dtype=np.int8)

    def reset(self) -> tuple[int, ...]:
        self.player_lane = self.N_LANES // 2
        self.grid.fill(0)
        return self._obs()

    def _obs(self) -> tuple[int, int, int, int]:
        """Tuple state for interpretability and moderate |S|."""
        # Vertical distance to nearest hazard in player's lane (capped)
        dist = 99
        for r in range(self.N_ROWS - 1, -1, -1):
            if self.grid[r, self.player_lane]:
                dist = (self.N_ROWS - 1 - r)
                break
        dist = min(dist, 7)
        threat_here = int(self.grid[-1, self.player_lane])
        # Neighbours on row just above player (relative hazard pattern)
        row = max(0, self.N_ROWS - 2)
        left = int(self.grid[row, self.player_lane - 1]) if self.player_lane > 0 else 0
        right = int(self.grid[row, self.player_lane + 1]) if self.player_lane < self.N_LANES - 1 else 0
        mid = int(self.grid[row, self.player_lane])
        pattern = left + 2 * mid + 4 * right
        return (self.player_lane, dist, pattern, threat_here)

    def step(self, action: int) -> StepResult:
        """action: 0=left, 1=stay, 2=right"""
        if action == 0:
            self.player_lane = max(0, self.player_lane - 1)
        elif action == 2:
            self.player_lane = min(self.N_LANES - 1, self.player_lane + 1)
        elif action == 1:
            pass
        else:
            raise ValueError("action must be 0,1,2")

        # Hazards already on the collision row must be detected *before* scrolling,
        # otherwise they are overwritten and collisions never register.
        if self.grid[-1, self.player_lane] == 1:
            self.grid.fill(0)
            return StepResult(self._obs(), -25.0, True)

        self.grid[1:] = self.grid[:-1].copy()
        self.grid[0] = 0
        if self.rng.random() < self.SPAWN_P:
            self.grid[0, int(self.rng.integers(0, self.N_LANES))] = 1

        hit = self.grid[-1, self.player_lane] == 1
        reward = 1.0 if not hit else -25.0
        if hit:
            self.grid.fill(0)
        return StepResult(self._obs(), float(reward), bool(hit))
