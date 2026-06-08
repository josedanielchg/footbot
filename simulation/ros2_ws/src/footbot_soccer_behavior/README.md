# footbot_soccer_behavior

Deterministic ROS 2 soccer behavior nodes for the FootBot simulation.

Current executables:

- `ball_state_estimator`: converts `vision_msgs/msg/Detection2D` ball detections into `footbot_soccer_msgs/msg/BallState`.
- `ball_control_fsm`: finite-state machine that publishes `/cmd_vel` commands for one-robot ball control.
- `ball_goal_state_estimator`: converts `vision_msgs/msg/Detection2DArray` ball+goal detections into `footbot_soccer_msgs/msg/BallGoalState` (Reach Goal).
- `reach_goal_fsm`: Reach Goal finite-state machine that pushes the ball toward a visible goal and owns `/cmd_vel` in reach-goal mode.
- `reach_goal_score_monitor`: simulation-only referee node that publishes `/soccer/goal_scored` when the ball enters the Reach Goal goal zone.

Internal layout:

- `state_estimation/`: image detections to ball-relative and ball+goal state.
- `fsm/`: high-level ball-control and Reach-goal orchestration.
- `skills/`: bounded low-level `Twist` generation for each FSM state.
- `referee/`: simulation episode checks that do not guide robot perception or control.
- `config/ball_control.yaml`: documented defaults for the ball-control estimator and FSM.
- `config/reach_goal.yaml`: documented defaults for the Reach Goal estimator and FSM.

Reach Goal uses short temporal goal memory so momentary YOLO goal dropouts near
the goal mouth do not interrupt dribbling. Scoring is handled separately by
the simulation referee topic `/soccer/goal_scored`, which stops the FSM after
the ball enters the goal zone. The score monitor reads the Gazebo world pose
stream for `reach_goal_ball`; that pose is referee logic only, not robot navigation
input.

This package does not implement shooting, team play, opponent interaction, or reinforcement learning.
