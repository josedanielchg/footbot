# Troubleshooting

## Workspace Package Not Found

```bash
source /opt/ros/humble/setup.bash
cd simulation/ros2_ws
colcon build --symlink-install
source install/setup.bash
ros2 pkg list | grep footbot
```

## Robot Does Not Move

Check topic ownership:

```bash
ros2 topic info /cmd_vel
ros2 topic echo /cmd_vel
```

Run only one control mode at a time.

## Camera Topic Missing

```bash
ros2 topic list | grep camera
ign topic -l | grep camera
```

If Gazebo has the topic but ROS does not, inspect the `ros_gz_bridge` arguments
in the active launch file.

## Ball Control Spins Forever

Check the robot camera and ball detection:

```bash
ros2 topic hz /camera/image_raw
ros2 topic echo /ball_detection
ros2 topic echo /soccer/ball_state
ros2 topic echo /soccer/fsm_state
```

Use `show_debug_view:=true` to see the detector overlay.

## YOLO Import Or NumPy Errors

Reinstall the pinned optional dependencies:

```bash
python3 -m pip install --user --force-reinstall -r simulation/requirements-yolo.txt
```

Avoid NumPy 2.x with this Ubuntu 22.04 ROS/OpenCV/MediaPipe setup.

## Ball Rolls Too Long

Confirm the ball drag plugin is installed and the world loads it:

```bash
cd simulation/ros2_ws
colcon build --symlink-install --packages-select footbot_gazebo footbot_bringup
source install/setup.bash
```

Then relaunch the simulation. Existing Gazebo processes must be restarted to
load a rebuilt plugin.
