# Setup

The supported simulation stack is:

```text
Ubuntu 22.04 jammy
ROS 2 Humble Hawksbill
Gazebo Fortress
ros-humble-ros-gz
Python 3.10
```

Use [install-ubuntu-22-04.md](install-ubuntu-22-04.md) for the detailed apt
installation steps. The stack decision and future migration notes are in
[stack-decision.md](stack-decision.md).

## Baseline Checks

```bash
source /opt/ros/humble/setup.bash
ros2 doctor
ros2 pkg list | grep ros_gz
ign gazebo --versions
```

Expected result:

- ROS 2 CLI is available.
- `ros_gz_bridge` and `ros_gz_sim` are discoverable.
- Gazebo reports Fortress/Ignition Gazebo versions.

## Optional Python Dependencies

Gesture perception:

```bash
python3 -m pip install --user --force-reinstall "numpy==1.26.4" "mediapipe==0.10.14"
```

YOLO soccer vision:

```bash
python3 -m pip install --user -r simulation/requirements-yolo.txt
```

Keep NumPy on `1.26.4` for this Ubuntu 22.04 workflow. NumPy 2.x can break ROS,
OpenCV, Matplotlib, and MediaPipe binary wheels.

## First Build

```bash
cd /media/josedanielchg/Data/Proyectos/Robotica/footbot
source /opt/ros/humble/setup.bash
cd simulation/ros2_ws
colcon build --symlink-install
source install/setup.bash
```

Check package visibility:

```bash
colcon list --base-paths src
ros2 pkg list | grep footbot
```
