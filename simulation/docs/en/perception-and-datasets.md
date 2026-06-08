# Perception And Datasets

<p align="center">
  <img src="src/gesture-debug.png" alt="Gesture debug screenshot with MediaPipe landmarks" />
</p>

**Figure 1.** ROS-native gesture-control debug view with MediaPipe hand
landmarks, direction, and speed feedback.

## Camera Topics

Default simulated robot camera:

```text
/camera/image_raw
/camera/camera_info
```

Soccer field goalkeeper camera:

```text
/soccer/camera/image_raw
/soccer/camera/camera_info
```

## HSV Ball Detection

`footbot_perception` provides `ball_detector`, which publishes:

```text
/ball_detection
/ball/debug_image
```

This detector is deterministic and tuned for the simulated orange ball.

## YOLO Soccer Vision

`footbot_soccer_vision` provides:

```text
opponent_detector
goal_detector
image_capture
```

Default outputs:

```text
/opponent_detections
/opponent_detection/debug_image
/goal_detections
/goal_detection/debug_image
```

Detections use `vision_msgs/msg/Detection2DArray`.

Reach-goal ball/goal detections use:

```text
/soccer/detections
/soccer/detections/debug_image
```

Run the one-robot Reach-goal vision scene:

```bash
ros2 launch footbot_bringup reach_goal.launch.py \
  model_path:=/media/josedanielchg/Data/Proyectos/Robotica/footbot/simulation/ros2_ws/src/footbot_soccer_vision/models/reach_goal_ball_goal/reach_goal_ball_goal_v1_best.pt \
  target_classes:=ball,goal \
  show_debug_view:=true
```

If using `soccer_field.launch.py` directly, pass
`image_topic:=/soccer/camera/image_raw` to the YOLO detector; otherwise the
debug image window will stay black because the detector is listening to the
wrong camera topic.

Install optional YOLO dependencies:

```bash
python3 -m pip install --user -r simulation/requirements-yolo.txt
```

Model weights are ignored by Git. Put local weights under:

```text
simulation/ros2_ws/src/footbot_soccer_vision/models/weights/
```

## Dataset Capture

```bash
ros2 run footbot_soccer_vision image_capture \
  --ros-args -p image_topic:=/camera/image_raw
```

Generated images and labels are ignored by Git.

<p align="center">
  <img src="src/yolo-labeling.png" alt="Label Studio screenshot with soccer object labels" />
</p>

**Figure 2.** Label Studio project view with soccer objects labeled for YOLO
training, including `ball`, `goal`, and `opponent` boxes.

## Conservative Augmentation

For 40 originals, create 40 copied originals plus 120 rotated/darkened images:

```bash
python3 simulation/ros2_ws/src/footbot_soccer_vision/datasets/augment_dataset.py \
  --input-dir simulation/ros2_ws/src/footbot_soccer_vision/datasets/raw/soccer_v1/images \
  --output-dir simulation/ros2_ws/src/footbot_soccer_vision/datasets/raw/soccer_v1/augmented_images \
  --output-size 640 640 \
  --rotation-angles 90 180 270 \
  --brightness-factor 0.85 \
  --copy-originals \
  --clean-output
```

The output remains unlabeled. Label generated images manually before YOLO
training.

## Reach Goal Training Preparation

Put Label Studio YOLO exports under:

```text
simulation/ros2_ws/src/footbot_soccer_vision/datasets/exports/
```

Prepare a `ball` + `goal` dataset:

```bash
python3 simulation/ros2_ws/src/footbot_soccer_vision/datasets/prepare_reach_goal_dataset.py \
  --input-dir simulation/ros2_ws/src/footbot_soccer_vision/datasets/exports/soccer_v1_labelstudio_yolo \
  --output-dir simulation/ros2_ws/src/footbot_soccer_vision/datasets/exports/reach_goal_ball_goal_v1 \
  --classes ball goal \
  --copy-images \
  --seed 42
```

Validate it:

```bash
python3 simulation/ros2_ws/src/footbot_soccer_vision/datasets/validate_yolo_dataset.py \
  --dataset-dir simulation/ros2_ws/src/footbot_soccer_vision/datasets/exports/reach_goal_ball_goal_v1 \
  --require-splits train val
```

Dry-run training:

```bash
python3 simulation/ros2_ws/src/footbot_soccer_vision/training/train_yolo_reach_goal.py \
  --config simulation/ros2_ws/src/footbot_soccer_vision/training/configs/reach_goal_ball_goal.yaml \
  --dry-run
```
