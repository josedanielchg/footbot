# Verification

Run these checks after installing the simulation stack.

## ROS 2 CLI

```bash
source /opt/ros/humble/setup.bash
ros2 --version
ros2 doctor
ros2 pkg list | grep demo_nodes
```

Expected result:

- `ros2` is available.
- `ros2 doctor` runs without blocking errors.
- Demo packages are visible.

## ROS 2 Talker/Listener

Terminal 1:

```bash
source /opt/ros/humble/setup.bash
ros2 run demo_nodes_cpp talker
```

Terminal 2:

```bash
source /opt/ros/humble/setup.bash
ros2 run demo_nodes_py listener
```

Expected result:

- The talker prints publishing messages.
- The listener prints received messages.

## Gazebo Fortress

```bash
ign gazebo --versions
ign gazebo
```

Expected result:

- Gazebo reports Fortress/Ignition Gazebo versions.
- The Gazebo GUI opens.

For Fortress, prefer `ign gazebo`. The newer `gz sim` command is used by later Gazebo releases such as Harmonic.

## ROS/Gazebo Packages

```bash
source /opt/ros/humble/setup.bash
ros2 pkg list | grep ros_gz
```

Expected result:

- Packages such as `ros_gz_bridge`, `ros_gz_sim`, or related `ros_gz` packages are listed.

## Optional Workspace Sanity Check

The workspace source directory should exist:

```bash
test -d simulation/ros2_ws/src
```

## FootBot Movement Simulation

Build and source the workspace:

```bash
cd /media/josedanielchg/Data/Proyectos/Robotica/footbot
source /opt/ros/humble/setup.bash
cd simulation/ros2_ws
colcon build --symlink-install
source install/setup.bash
```

Launch the simulation:

```bash
ros2 launch footbot_bringup spawn_footbot.launch.py
```

For a headless server-only check:

```bash
ros2 launch footbot_bringup spawn_footbot.launch.py use_gui:=false
```

In another terminal, check movement topics:

```bash
source /opt/ros/humble/setup.bash
source /media/josedanielchg/Data/Proyectos/Robotica/footbot/simulation/ros2_ws/install/setup.bash

ros2 topic list | sort
ros2 topic info /cmd_vel
ros2 topic echo --once /odom
```

Send test commands:

```bash
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist \
"{linear: {x: 0.12, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}"

ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist \
"{linear: {x: -0.12, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}"

ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist \
"{linear: {x: 0.0, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.8}}"

ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist \
"{linear: {x: 0.0, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: -0.8}}"

ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist \
"{linear: {x: 0.0, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}"
```

Expected result:

- `/cmd_vel` exists as `geometry_msgs/msg/Twist`.
- `/odom` publishes `nav_msgs/msg/Odometry`.
- Positive `linear.x` moves the robot forward.
- Negative `linear.x` moves the robot backward.
- Positive `angular.z` rotates left.
- Negative `angular.z` rotates right.
- Zero Twist stops the robot.

If odometry is missing, inspect the underlying Gazebo topic:

```bash
ign topic -l | grep -E 'cmd_vel|odom|odometry'
```

The current bridge maps Gazebo `/model/footbot/odometry` to ROS `/odom`.
