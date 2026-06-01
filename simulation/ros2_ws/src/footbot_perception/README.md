# footbot_perception

Perception package for the Footbot simulation.

Current contents:

- `webcam_publisher`: publishes a computer webcam on `/webcam/image_raw`.
- `hand_detector`: runs MediaPipe Hands on a ROS image topic.
- `debug_image_viewer`: opens an OpenCV window for annotated gesture images.
- `ball_detector`: detects an orange ball from the simulated robot camera.
- Gesture classification helpers adapted from the legacy `manual_control/` app.
- Optional debug image publishing on `/gesture/debug_image`.

Published gesture topics:

```text
/gesture/direction    std_msgs/msg/String
/gesture/speed        std_msgs/msg/Float32
/gesture/debug_image  sensor_msgs/msg/Image
```

Published ball topics:

```text
/ball_detection    vision_msgs/msg/Detection2D
/ball/debug_image  sensor_msgs/msg/Image
```

Install the MediaPipe/NumPy versions used by `hand_detector`:

```bash
python3 -m pip install --user --force-reinstall "numpy==1.26.4" "mediapipe==0.10.14"
```

Run the webcam publisher:

```bash
ros2 run footbot_perception webcam_publisher
```

Run hand detection:

```bash
ros2 run footbot_perception hand_detector
```

Show the annotated debug image:

```bash
ros2 run footbot_perception debug_image_viewer
```

Or launch perception with the debug window enabled:

```bash
ros2 launch footbot_bringup gesture_perception.launch.py show_debug_view:=true
```

Run ball detection:

```bash
ros2 run footbot_perception ball_detector
```

Show the ball detector debug image:

```bash
ros2 run footbot_perception debug_image_viewer \
  --ros-args -p image_topic:=/ball/debug_image
```

Not implemented yet:

- ML object detection
- Gesture calibration UI

See also:

- `simulation/docs/PERCEPTION_AND_DATASETS.md`
- `simulation/docs/MODES.md`
