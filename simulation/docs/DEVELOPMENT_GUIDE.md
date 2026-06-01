# Development Guide

## Boundaries

- Keep implementation work inside `simulation/` unless a task explicitly says otherwise.
- Do not modify `esp32cam_robot/` or `manual_control/` for simulation refactors.
- Keep stable simulation modes separate from experiments.
- Do not commit generated build output, datasets, virtualenvs, model weights, or caches.

## Package Guidelines

- Put shared constants and tiny helpers in `footbot_common`.
- Put robot model changes in `footbot_description`.
- Put Gazebo worlds, models, and plugins in `footbot_gazebo`.
- Put launch orchestration in `footbot_bringup`.
- Put generic perception in `footbot_perception`.
- Put soccer-specific YOLO and dataset tools in `footbot_soccer_vision`.
- Put soccer behavior FSM, state estimation, and skills in `footbot_soccer_behavior`.

## Validation Checklist

```bash
git status -sb
source /opt/ros/humble/setup.bash
cd simulation/ros2_ws
colcon build --symlink-install
source install/setup.bash
colcon list --base-paths src
ros2 pkg list | grep footbot
```

Compile Python:

```bash
python3 -m py_compile src/footbot_soccer_behavior/footbot_soccer_behavior/**/*.py
```

Check launch arguments:

```bash
ros2 launch footbot_bringup spawn_footbot.launch.py --show-args
ros2 launch footbot_bringup ball_control.launch.py --show-args
```

Check SDF/URDF:

```bash
ros2 run xacro xacro src/footbot_description/urdf/footbot.urdf.xacro > /tmp/footbot.urdf
check_urdf /tmp/footbot.urdf
ign sdf -k src/footbot_gazebo/worlds/footbot_soccer_field.sdf
```

## Documentation Rules

Keep docs English-only in `simulation/docs/` for now. Separate implemented
behavior from planned behavior. Prefer short topic-focused docs over one giant
reference file.
