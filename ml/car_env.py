"""
Discrete **ring-racing** MDP aligned with the web "Neon Circuit" idea (no pygame).

State: angular sector, lateral offset bin, speed bin. Actions combine lateral nudge and throttle.
Suitable for **DQN** / tabular baselines; observation is a single integer index (factored decoding in nn_embedding or one-hot in a linear layer).

This is a simplified abstraction — the browser game uses continuous physics; train policies here, then discuss sim-to-real / distillation in write-ups.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class CarStep:
    observation: int
    reward: float
    terminated: bool


class CarRingEnv:
    N_ANG = 36
    N_OFF = 9
    N_SPD = 6
    LAP_LEN = N_ANG
    PROGRESS_REW = 0.15
    OFF_PENALTY = 0.08
    CRASH_PENALTY = -12.0

    def __init__(self, seed: int | None = 0) -> None:
        self.rng = np.random.default_rng(seed)
        self.ang = 0
        self.off = self.N_OFF // 2
        self.spd = 2
        self.progress = 0

    def reset(self) -> int:
        self.ang = int(self.rng.integers(0, self.N_ANG))
        self.off = self.N_OFF // 2
        self.spd = 2
        self.progress = 0
        return self._obs()

    def _obs(self) -> int:
        return (self.ang * self.N_OFF + self.off) * self.N_SPD + self.spd

    def step(self, action: int) -> CarStep:
        """
        action in 0..8: lateral in {left, stay, right} + throttle in {down, stay, up}
        encoded as lat*3 + thr
        """
        if action < 0 or action > 8:
            raise ValueError("action 0..8")
        lat = action // 3
        thr = action % 3

        if lat == 0:
            self.off = max(0, self.off - 1)
        elif lat == 2:
            self.off = min(self.N_OFF - 1, self.off + 1)

        if thr == 0:
            self.spd = max(0, self.spd - 1)
        elif thr == 2:
            self.spd = min(self.N_SPD - 1, self.spd + 1)

        # forward motion proportional to speed
        step = max(1, self.spd)
        self.ang = (self.ang + step) % self.N_ANG
        self.progress += step

        off_err = abs(self.off - self.N_OFF // 2)
        r = self.PROGRESS_REW * step - self.OFF_PENALTY * off_err
        done = False
        if off_err >= 4:
            r += self.CRASH_PENALTY
            done = True
        if self.progress >= self.LAP_LEN * 24:
            done = True
        return CarStep(self._obs(), float(r), done)
