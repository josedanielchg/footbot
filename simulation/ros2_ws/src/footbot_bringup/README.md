# footbot_bringup

Launch and orchestration package for the Footbot simulation.

Current contents:

- Launch files for Gazebo
- Launch files for robot description
- Launch setup for ROS/Gazebo movement topic bridge
- Launch setup for ROS/Gazebo camera topic bridge
- Launch setup for the ESP32-compatible HTTP command bridge
- Launch setup for ROS-native webcam gesture perception
- Launch setup for ROS-native gesture-to-velocity control
- Optional server-only launch mode for headless checks

Gesture-control launch files:

```bash
ros2 launch footbot_bringup gesture_perception.launch.py
ros2 launch footbot_bringup gesture_control.launch.py
ros2 launch footbot_bringup sim_gesture_control.launch.py
```

Open the gesture debug image window with:

```bash
ros2 launch footbot_bringup sim_gesture_control.launch.py show_debug_view:=true
```

Future contents:

- Shared runtime configuration

Not implemented yet:

- Object detection startup
