# footbot_soccer_vision

YOLO-based soccer vision package for the FootBot simulation.

This package complements `footbot_perception`. It focuses on soccer-specific
vision experiments such as opponent detection and dataset capture while the
existing package keeps generic camera, gesture, and ball-following utilities.

## Dependencies

Install ROS dependencies through the simulation install guide. Install YOLO
Python dependencies from the repository root:

```bash
python3 -m pip install --user -r simulation/requirements-yolo.txt
```

The requirements pin NumPy to `1.26.4` to avoid the NumPy 2.x compatibility
issues seen with ROS/OpenCV/MediaPipe on Ubuntu 22.04.
They also pin Ultralytics to `8.4.56`, the current non-yanked PyPI release
verified on 2026-05-30.

## Topics

Default input:

```text
/camera/image_raw
```

Default outputs:

```text
/opponent_detections
/opponent_detection/debug_image
/goal_detections
/goal_detection/debug_image
```

Detections use `vision_msgs/msg/Detection2DArray`.

Reach Goal combined ball/goal detection uses:

```text
/soccer/detections
/soccer/detections/debug_image
```

## Model Weights

Weights are not committed to Git. The first test model is `yolo11n.pt`:

```bash
python3 simulation/ros2_ws/src/footbot_soccer_vision/scripts/download_models.py
```

If no local weight file is present, Ultralytics may download/cache the named
model at runtime. Custom goal and opponent models are not trained yet.

## Run

After building and sourcing the workspace:

```bash
ros2 run footbot_soccer_vision opponent_detector
```

Or launch the full opponent-detection simulation:

```bash
ros2 launch footbot_bringup opponent_detection.launch.py show_debug_view:=true
```

Run soccer-field goal and opponent detection from the blue goalkeeper camera:

```bash
ros2 launch footbot_bringup soccer_detection.launch.py show_debug_view:=true
```

Run Reach-goal ball/goal YOLO inference after trained weights exist:

```bash
ros2 launch footbot_soccer_vision yolo_detector.launch.py \
  model_path:=/media/josedanielchg/Data/Proyectos/Robotica/footbot/simulation/ros2_ws/src/footbot_soccer_vision/models/reach_goal_ball_goal/reach_goal_ball_goal_v1_best.pt \
  target_classes:=ball,goal \
  show_debug_view:=true
```

Use custom trained weights when available:

```bash
ros2 launch footbot_bringup soccer_detection.launch.py model_path:=/path/to/best.pt
```

## Dataset Capture

Capture images from the robot camera:

```bash
ros2 run footbot_soccer_vision image_capture \
  --ros-args -p image_topic:=/camera/image_raw
```

Generated dataset files are ignored by Git.

Create a small simulation-appropriate unlabeled augmentation set:

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

The augmentation output is still unlabeled and must be manually labeled before
YOLO training.

## Reach Goal Training Preparation

Label Studio exports should go under:

```text
simulation/ros2_ws/src/footbot_soccer_vision/datasets/exports/
```

Prepare a focused `ball` + `goal` dataset:

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

## Current Limitations

- The default pretrained model detects COCO classes such as `person`.
- FootBot-like Gazebo opponent placeholders may not be detected reliably until a
  custom model is trained.
- Gazebo goals require a custom `goal` class before YOLO can detect them
  reliably.
- This package publishes perception outputs only; it does not command robot
  motion or implement tactical behavior.
