# footbot_gazebo

Gazebo integration package for the Footbot simulation.

Current contents:

- Gazebo worlds
- Camera test world with visible colored targets
- Ball-following world with an orange target ball
- Ball-control world and dynamic orange ball model
- Multi-lane ball-control world with divider and boundary walls
- Opponent-detection world with FootBot-like robot placeholders
- Soccer field world with goals, walls, a center ball, and two mirrored teams
- ROS/Gazebo bridge reference configuration

Worlds:

```text
footbot_camera_test.sdf
footbot_ball_follow.sdf
footbot_ball_control.sdf
footbot_ball_control_multi.sdf
footbot_opponent_detection.sdf
footbot_soccer_field.sdf
```

Models:

```text
models/orange_ball
```

The opponent world is designed for YOLO pipeline tests and dataset capture. It
uses static FootBot-like robot placeholders so future robot-vs-robot scenarios
can grow from the same visual language. The placeholders are not guaranteed to
be recognized by a pretrained COCO model without later fine-tuning.

Future contents:

- SDF/model assets
- Spawn logic
- Simulation-specific plugin configuration

Not implemented yet:

- Physics tuning
- External model asset library
