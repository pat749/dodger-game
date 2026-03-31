# Machine learning & RL (side-project / thesis hook)

This folder turns the dodge idea into a **small, formal MDP** and a **tabular Q-learning** baseline—enough structure for a CS / ML / robotics student to extend (function approximation, POMDP, curriculum, imitation from human play, etc.).

## Problem framing

- **MDP** $\mathcal{M} = (\mathcal{S}, \mathcal{A}, P, r, \gamma)$ with stochastic falling hazards (exogenous spawn process).
- **Observation** in `DodgeEnv` is a deliberately compressed tuple `(player_lane, depth_bucket, neighbour_pattern, imminent_threat)` so **tabular** methods stay feasible (state space on the order of $10^3$–$10^4$).
- **Actions:** $\mathcal{A} = \{\mathrm{left}, \mathrm{stay}, \mathrm{right}\}$.
- **Reward:** $+1$ per survival step, large penalty on collision (sparse failure signal). You can reshape rewards (potential-based shaping, curiosity, etc.) for a course project.

## Related directions (for a “PhD-level” narrative)

| Direction | Hook |
|-----------|------|
| **POMDP / belief** | Partial grids + particle filter over hazard positions. |
| **Function approximation** | Neural Q / actor–critic on raw grid or CNN over local patches. |
| **MCTS / planning** | Model-based rollouts if you learn $P(s'|s,a)$. |
| **Opponent / curriculum** | Adaptive spawn rate as a *contextual bandit* (connects to **dynamic difficulty adjustment**). |
| **Offline RL** | Log `(s,a,r,s')` from the pygame or web game, run CQL / IQL on logs. |
| **Imitation** | Behaviour cloning from human trajectories vs. RL policy. |

## Run the baseline

From the **repository root**:

```bash
python3 -m venv .venv-ml
source .venv-ml/bin/activate   # Windows: .venv-ml\Scripts\activate
pip install -r requirements-ml.txt
python3 -m ml.train_q --seed 0
```

Defaults: **35k episodes**, **Double Q-learning**, **γ=0.99**, exponential **ε** decay, merged **Q₁+Q₂** written to `ml/checkpoints/q_table.json` (gitignored). Evaluation uses **300** episodes (horizon 8000) and prints mean ± std and median.

Push further (longer runs): e.g. `--episodes 80000 --alpha 0.2 --optimism 2`. A/B single-Q: `--no-double` (usually weaker).

## Integrity

- The **Python game** (`game/main.py`) and **web canvas** (`web/game.js`) are separate from this env: physics differ slightly. Treat `DodgeEnv` as a **research abstraction**; align them further if you need sim-to-real style transfer for a publication.

## Citation

If you use this in coursework or a paper, cite the repository URL and date accessed, or add a `CITATION.cff` at the repo root (included) for GitHub’s citation widget.
