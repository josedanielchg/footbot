# FootBot Simulation Docs 🤖⚽

This English documentation set explains the ROS 2 + Gazebo simulation layer
under `simulation/`. Spanish and French versions are planned later under
parallel language folders.

<p align="center">
  <img src="src/simulation-overview.png" alt="FootBot simulation overview screenshot" />
</p>

**Figure 1.** Planned screenshot slot. Capture Gazebo with the FootBot spawned
in the camera-test world and save it as `simulation/docs/en/src/simulation-overview.png`.

---

## Table of Contents

- 🚀 [Setup](setup.md)
- 🧱 [Workspace](workspace.md)
- 🧭 [Architecture](architecture.md)
- 🎮 [Modes](modes.md)
- ⚽ [Ball Control](ball-control.md)
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
5. Use [ball-control.md](ball-control.md) for the current autonomous soccer behavior.

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
- YOLO opponent/goal detector plumbing and dataset capture workflow.
- Soccer field and multi-scenario worlds.

Planned only:

- Reach the goal while keeping ball control.
- Steal the ball from an opponent.
- Team play with three robots per side.
- RL/MARL, MCTS, or SPO-style tactical experiments.

---

## Screenshot Asset Guide

Place English documentation images in:

```text
simulation/docs/en/src/
```

Use these filenames so the docs render without later link churn:

| File | Screenshot to take | Used in |
| --- | --- | --- |
| `simulation-overview.png` | Gazebo camera-test world with one spawned FootBot. | `simulation/README.md`, `docs/en/README.md` |
| `soccer-field.png` | Full soccer field with walls, goals, ball, and mirrored teams. | `worlds-and-scenarios.md` |
| `ball-control-debug.png` | Ball-control run with Gazebo and debug image visible. | `ball-control.md` |
| `gesture-debug.png` | Webcam gesture debug window with MediaPipe landmarks. | `perception-and-datasets.md` |
| `yolo-labeling.png` | Label Studio task with ball/goal/opponent boxes. | `perception-and-datasets.md` |

Keep screenshots lightweight, preferably PNG, and avoid committing generated
datasets or model weights.
