# Reach Goal YOLO Training

This folder prepares YOLO training for Soccer Behavior Reach Goal: reaching the
goal with the ball.

Default Reach Goal classes:

```text
ball
goal
```

Optional full soccer classes:

```text
ball
goal
opponent
robot
teammate
```

## Prepare Dataset

```bash
python3 simulation/ros2_ws/src/footbot_soccer_vision/datasets/prepare_reach_goal_dataset.py \
  --input-dir simulation/ros2_ws/src/footbot_soccer_vision/datasets/exports/soccer_v1_labelstudio_yolo \
  --output-dir simulation/ros2_ws/src/footbot_soccer_vision/datasets/exports/reach_goal_ball_goal_v1 \
  --classes ball goal \
  --copy-images \
  --seed 42
```

## Validate Dataset

```bash
python3 simulation/ros2_ws/src/footbot_soccer_vision/datasets/validate_yolo_dataset.py \
  --dataset-dir simulation/ros2_ws/src/footbot_soccer_vision/datasets/exports/reach_goal_ball_goal_v1 \
  --require-splits train val
```

## Dry Run

```bash
python3 simulation/ros2_ws/src/footbot_soccer_vision/training/train_yolo_reach_goal.py \
  --config simulation/ros2_ws/src/footbot_soccer_vision/training/configs/reach_goal_ball_goal.yaml \
  --dry-run
```

## Train

```bash
python3 simulation/ros2_ws/src/footbot_soccer_vision/training/train_yolo_reach_goal.py \
  --config simulation/ros2_ws/src/footbot_soccer_vision/training/configs/reach_goal_ball_goal.yaml
```

## Evaluate

```bash
python3 simulation/ros2_ws/src/footbot_soccer_vision/training/evaluate_yolo.py \
  --weights simulation/ros2_ws/src/footbot_soccer_vision/models/reach_goal_ball_goal/reach_goal_ball_goal_v1_best.pt \
  --data simulation/ros2_ws/src/footbot_soccer_vision/datasets/exports/reach_goal_ball_goal_v1/data.yaml \
  --device cpu
```

## Predict On Images

```bash
python3 simulation/ros2_ws/src/footbot_soccer_vision/training/predict_images.py \
  --weights simulation/ros2_ws/src/footbot_soccer_vision/models/reach_goal_ball_goal/reach_goal_ball_goal_v1_best.pt \
  --source simulation/ros2_ws/src/footbot_soccer_vision/datasets/exports/reach_goal_ball_goal_v1/images/val \
  --conf 0.25
```

## Augmentation Policy

Keep simulation augmentation conservative. Mild brightness variation is useful,
but heavy blur, noise, perspective warps, cutouts, random crops, and large
mosaic-style changes can move the dataset away from the Gazebo camera domain.

Do not apply image-only transforms to already labeled datasets unless bounding
boxes are transformed at the same time.
