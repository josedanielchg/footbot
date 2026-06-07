# footbot_soccer_msgs

Custom ROS 2 message interfaces for FootBot soccer behavior.

Current messages:

- `BallState`: estimated ball visibility, image-space error, approximate range, and control-zone flags.
- `BallGoalState`: Reach-goal state with image-space ball and goal bearings, control flag, ball/goal alignment flag, and short-lived goal memory fields. The state is image-derived only; it never uses Gazebo ground-truth poses.
