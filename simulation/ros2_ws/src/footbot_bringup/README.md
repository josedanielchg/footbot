# footbot_bringup

Launch and orchestration package for the FootBot simulation.

## Launch Modes

| Launch file | Purpose | `/cmd_vel` owner |
| --- | --- | --- |
| `spawn_footbot.launch.py` | Base robot, Gazebo, camera/odom bridge, optional HTTP bridge. | HTTP bridge or manual ROS topic commands |
| `sim_gesture_control.launch.py` | Full ROS-native webcam gesture control. | `gesture_to_cmd_vel` |
| `gesture_perception.launch.py` | Webcam + MediaPipe perception only. | none |
| `gesture_control.launch.py` | Gesture topics to velocity commands only. | `gesture_to_cmd_vel` |
| `ball_following.launch.py` | Simple HSV ball follower. | `ball_follower` |
| `ball_control.launch.py` | Current deterministic soccer ball-control behavior. | `ball_control_fsm` |
| `ball_control_multi.launch.py` | Three isolated ball-control test lanes. | one FSM per lane topic |
| `reach_goal.launch.py` | One robot, one ball, one goal, YOLO ball/goal detection, score monitor, and Reach-goal behavior. | `reach_goal_fsm` |
| `opponent_detection.launch.py` | Opponent-detection test world and YOLO node. | none |
| `soccer_detection.launch.py` | Soccer field camera with goal/opponent detection. | none |
| `soccer_field.launch.py` | Field, walls, goals, teams, and center ball visualization. | none |

Run only one control-owning mode at a time.

## Common Commands

```bash
ros2 launch footbot_bringup spawn_footbot.launch.py
ros2 launch footbot_bringup ball_control.launch.py scenario:=front show_debug_view:=true
ros2 launch footbot_bringup reach_goal.launch.py show_debug_view:=true
ros2 launch footbot_bringup soccer_detection.launch.py show_debug_view:=true
```

See the simulation docs:

- `simulation/docs/en/modes.md`
- `simulation/docs/en/ball-control.md`
- `simulation/docs/en/architecture.md`
