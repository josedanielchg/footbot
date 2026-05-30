# footbot_control

Control package for the Footbot simulation.

Current contents:

- `gesture_to_cmd_vel`: converts gesture intent topics into `/cmd_vel`.
- `ball_follower`: converts ball detections into `/cmd_vel`.

Subscribed topics:

```text
/gesture/direction  std_msgs/msg/String
/gesture/speed      std_msgs/msg/Float32
/ball_detection     vision_msgs/msg/Detection2D
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

Run ball following control:

```bash
ros2 run footbot_control ball_follower
```

The control nodes publish zero velocity when commands or detections time out or when they shut down.
Only run one `/cmd_vel` controller at a time.

Not implemented yet:

- Hardware controller integration
- Navigation
- Advanced command smoothing
