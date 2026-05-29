# footbot_control

Control package for the Footbot simulation.

Current contents:

- `gesture_to_cmd_vel`: converts gesture intent topics into `/cmd_vel`.

Subscribed topics:

```text
/gesture/direction  std_msgs/msg/String
/gesture/speed      std_msgs/msg/Float32
```

Published topic:

```text
/cmd_vel            geometry_msgs/msg/Twist
```

Run the control node:

```bash
ros2 run footbot_control gesture_to_cmd_vel
```

Test it with fake gesture messages:

```bash
ros2 topic pub --once /gesture/speed std_msgs/msg/Float32 "{data: 0.6}"
ros2 topic pub --once /gesture/direction std_msgs/msg/String "{data: forward}"
```

The node publishes zero velocity when commands time out or when it shuts down.

Not implemented yet:

- Hardware controller integration
- Navigation
- Advanced command smoothing
