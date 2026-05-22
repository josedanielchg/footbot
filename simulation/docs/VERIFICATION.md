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
