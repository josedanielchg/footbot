# FootBot Simulation — ROS 2 + Gazebo 🤖⚽

[English](docs/en/README.md) · Español soon · Français soon

> Simulation-first migration of FootBot using **ROS 2 Humble** and **Gazebo
> Fortress**. This layer keeps the legacy ESP32 and Python apps available as
> references while adding robot spawning, simulated camera data, ROS-native
> control, soccer perception, and autonomous ball-control experiments.

<p align="center">
  <img src="docs/en/src/simulation-overview.png" alt="FootBot simulation overview screenshot" />
</p>

**Figure 1.** Planned screenshot slot. Save a Gazebo screenshot of the spawned
FootBot at `simulation/docs/en/src/simulation-overview.png`.

---

## At A Glance

- 🤖 **Robot model:** FootBot Xacro model with wheels, caster, camera, and Gazebo plugins.
- 🎮 **Control:** `/cmd_vel`, legacy HTTP `/move`, and ROS-native gesture control.
- 👁️ **Perception:** simulated camera, HSV ball detection, YOLO detector plumbing, and dataset tools.
- ⚽ **Soccer worlds:** camera tests, ball-control scenarios, multi-lane tests, goals, walls, and teams.
- 🧠 **Autonomy:** deterministic ball-control FSM and Reach-goal FSM; stealing and team strategy are planned only.

> **Control rule:** run only one `/cmd_vel` owner at a time.

---

## Table of Contents

- 📚 [Docs index](docs/en/README.md)
- 🚀 [Setup](docs/en/setup.md)
- 🧱 [Workspace](docs/en/workspace.md)
- 🧭 [Architecture](docs/en/architecture.md)
- 🎮 [Simulation modes](docs/en/modes.md)
- ⚽ [Ball control](docs/en/ball-control.md)
- 🥅 [Reach goal with ball](docs/en/reach-goal.md)
- 👁️ [Perception and datasets](docs/en/perception-and-datasets.md)
- 🌍 [Worlds and scenarios](docs/en/worlds-and-scenarios.md)
- 🧪 [Troubleshooting](docs/en/troubleshooting.md)
- 🛠️ [Development guide](docs/en/development-guide.md)
- 🗺️ [Planned soccer stages](docs/en/planned-soccer-stages.md)

---

## Quick Start

```bash
cd /media/josedanielchg/Data/Proyectos/Robotica/footbot/simulation/ros2_ws
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source install/setup.bash
```

Base simulation:

```bash
ros2 launch footbot_bringup spawn_footbot.launch.py
```

Current autonomous ball-control example:

```bash
ros2 launch footbot_bringup ball_control.launch.py scenario:=front show_debug_view:=true
```

Reach-goal vision scene:

```bash
ros2 launch footbot_bringup reach_goal.launch.py show_debug_view:=true
```

See [simulation modes](docs/en/modes.md) for the rest of the launch commands.
