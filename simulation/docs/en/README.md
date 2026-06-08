# FootBot Simulation Docs 🤖⚽

This documentation set explains the ROS 2 + Gazebo simulation layer under
`simulation/`: robot spawning, camera topics, control modes, soccer worlds,
perception pipelines, dataset tools, and the current autonomous behaviors.

<p align="center">
  <img src="src/simulation-overview.png" alt="FootBot simulation overview screenshot" />
</p>

**Figure 1.** FootBot running in Gazebo with the simulated robot camera and
camera-validation scene.

---

## Table of Contents

- 🚀 [Setup](setup.md)
- 🧱 [Workspace](workspace.md)
- 🧭 [Architecture](architecture.md)
- 🎮 [Modes](modes.md)
- ⚽ [Ball Control](ball-control.md)
- 🥅 [Reach Goal With Ball](reach-goal.md)
- 👁️ [Perception And Datasets](perception-and-datasets.md)
- 🌍 [Worlds And Scenarios](worlds-and-scenarios.md)
- 🧪 [Troubleshooting](troubleshooting.md)
- 🛠️ [Development Guide](development-guide.md)
- 🧬 [Stack Decision](stack-decision.md)
- 🐧 [Ubuntu 22.04 Install Notes](install-ubuntu-22-04.md)
- 🗺️ [Planned Soccer Stages](planned-soccer-stages.md)

---

## Recommended Reading Path

1. Start with [setup.md](setup.md) to install and verify ROS 2 Humble + Gazebo Fortress.
2. Read [workspace.md](workspace.md) to understand packages, builds, and generated folders.
3. Read [architecture.md](architecture.md) for package boundaries, data flow, and `/cmd_vel` ownership.
4. Use [modes.md](modes.md) to choose the correct launch mode.
5. Use [ball-control.md](ball-control.md) and [reach-goal.md](reach-goal.md) for the autonomous soccer behaviors.

---

## Current Scope

Implemented:

- FootBot robot model and Gazebo spawning.
- Differential-drive movement through `/cmd_vel`.
- HTTP `/move` compatibility bridge.
- Simulated robot camera.
- ROS-native webcam gesture control.
- HSV ball detection and simple ball follower.
- Deterministic one-robot ball control with FSM orchestration.
- Deterministic Reach Goal behavior with YOLO ball+goal perception, temporal goal memory, and a simulation score monitor.
- YOLO opponent/goal detector plumbing, Label Studio export handling, dataset validation, dataset preparation, training, evaluation, and prediction tools.
- Soccer field and multi-scenario worlds.

Planned only:

- Steal the ball from an opponent.
- Team play with three robots per side.
- RL/MARL, MCTS, or SPO-style tactical experiments.
