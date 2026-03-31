# Algorithm map (ML / RL / deep learning)

| Algorithm | Where | Type | Notes |
|-----------|--------|------|--------|
| **Q-learning** | `train_q.py` (dodge) | Tabular RL | Baseline on stochastic hazards. |
| **Double Q-learning** | `train_q.py` (default) | Tabular RL | Reduces Maximization Bias (Hasselt et al.). |
| **DQN + replay + target net** | `train_dqn_car.py` | Deep RL | Embedding + MLP on discrete `CarRingEnv`; classic Mnih et al. recipe. |
| **Exported DQN inference** | `export_dqn_car_web.py` → `web/car.js` | Deployment | Greedy Q in the browser (discrete state from continuous pose); **L** toggles vs PD baseline. |
| **Waypoint AI** | `web/car.js` | Hand-crafted policy | Tangent tracking + PD-style steering (not trained). |

## Extensions (paper / thesis)

- **Dueling DQN**, **Rainbow** ablations on `CarRingEnv`.
- **CNN DQN** if you rasterize the ring to an image.
- **PPO / SAC** on continuous clones of the car physics.
- **Offline RL** on logs from human + AI races.
- **Imitation learning** (BC / GAIL) from expert trajectories.

## References (compact)

- Watkins (1989) — Q-learning.  
- Hasselt (2010) — Double Q-learning.  
- Mnih et al. (2015) — Human-level control through deep reinforcement learning (DQN).
