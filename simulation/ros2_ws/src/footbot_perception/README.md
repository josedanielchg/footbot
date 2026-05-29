# footbot_perception

Perception package for the Footbot simulation.

Current contents:

- `webcam_publisher`: publishes a computer webcam on `/webcam/image_raw`.
- `hand_detector`: runs MediaPipe Hands on a ROS image topic.
- Gesture classification helpers adapted from the legacy `manual_control/` app.
- Optional debug image publishing on `/gesture/debug_image`.

Published gesture topics:

```text
/gesture/direction    std_msgs/msg/String
/gesture/speed        std_msgs/msg/Float32
/gesture/debug_image  sensor_msgs/msg/Image
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

Not implemented yet:

- Object detection
- Robot-camera autonomy
- Gesture calibration UI
