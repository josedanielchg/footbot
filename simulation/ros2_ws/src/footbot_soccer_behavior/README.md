# footbot_soccer_behavior

Deterministic ROS 2 soccer behavior nodes for the FootBot simulation.

Current nodes:

- `ball_state_estimator`: converts `vision_msgs/msg/Detection2D` ball detections into `footbot_soccer_msgs/msg/BallState`.
- `ball_control_fsm`: finite-state machine that publishes `/cmd_vel` commands for one-robot ball control.

This package does not implement shooting, team play, opponent interaction, or reinforcement learning.
