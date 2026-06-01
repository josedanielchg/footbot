# FootBot Simulation Docs

This directory documents the ROS 2 + Gazebo simulation layer under
`simulation/`. The legacy firmware and host-control applications remain outside
this layer and are treated as references unless a future task explicitly changes
them.

## Reading Path

1. [SETUP.md](SETUP.md) - install and verify ROS 2 Humble + Gazebo Fortress.
2. [WORKSPACE.md](WORKSPACE.md) - build, source, and understand ROS packages.
3. [ARCHITECTURE.md](ARCHITECTURE.md) - package boundaries, topics, and control ownership.
4. [MODES.md](MODES.md) - manual, gesture, perception-only, and autonomous launch modes.
5. [BALL_CONTROL.md](BALL_CONTROL.md) - the currently implemented autonomous soccer behavior.

## Reference Guides

- [PERCEPTION_AND_DATASETS.md](PERCEPTION_AND_DATASETS.md)
- [WORLDS_AND_SCENARIOS.md](WORLDS_AND_SCENARIOS.md)
- [PLANNED_SOCCER_STAGES.md](PLANNED_SOCCER_STAGES.md)
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- [DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md)
- [STACK_DECISION.md](STACK_DECISION.md)
- [INSTALL_UBUNTU_22_04.md](INSTALL_UBUNTU_22_04.md)

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
