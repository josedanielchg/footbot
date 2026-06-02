# footbot_soccer_behavior

Deterministic ROS 2 soccer behavior nodes for the FootBot simulation.

Current executables:

- `ball_state_estimator`: converts `vision_msgs/msg/Detection2D` ball detections into `footbot_soccer_msgs/msg/BallState`.
- `ball_control_fsm`: finite-state machine that publishes `/cmd_vel` commands for one-robot ball control.

Internal layout:

- `state_estimation/`: image detections to ball-relative state.
- `fsm/`: high-level ball-control orchestration.
- `skills/`: bounded low-level `Twist` generation for each FSM state.
- `config/ball_control.yaml`: documented defaults for estimator and FSM parameters.

This package does not implement shooting, team play, opponent interaction, or reinforcement learning.
