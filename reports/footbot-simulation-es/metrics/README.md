# FootBot Simulation Metrics

This folder contains the scripts used to collect and process the metrics for
`reports/footbot-simulation-es/main.tex`.

The normal workflow is:

1. Record Reach Goal episodes as ROS 2 bags.
2. Convert the bags into CSV files.
3. Generate report figures from those CSV files.

Generated bags, CSVs, figures, model outputs, and caches are local artifacts.
They should not be committed unless a specific report deliverable requires it.

## Folder Map

```text
metrics/
  common/        Shared bag-reading and CSV helpers.
  scripts/       Metric builders, recorder, and plotting script.
  csv/           Generated CSV files, ignored by Git.
  bags/          Generated ROS 2 bags, ignored by Git.
  run_all.sh     Best-effort wrapper for individual builders.
```

Important scripts:

| Script | Purpose |
|---|---|
| `01_loop_latency.py` | Camera-to-command latency, only when `/camera/image_raw` was recorded. |
| `02_topic_hz.py` | Topic publication frequency. |
| `03_time_to_ball_control.py` | Time until the robot first controls the ball. |
| `04_time_to_goal.py` | Time until `/soccer/goal_scored` becomes true. |
| `05_goal_success_rate.py` | Success rate across multiple episode bags. |
| `06_fsm_state_time.py` | Time spent in each FSM state. |
| `07_fsm_event_counts.py` | Counts events such as `RECOVER_BALL` and `COMMIT_TO_GOAL`. |
| `08_yolo_eval.py` | YOLO validation metrics and PR/F1 curves. |
| `09_trajectory_xy.py` | Robot and ball XY trajectory from Gazebo pose data. |
| `10_record_reach_goal_trials.py` | Runs multiple Reach Goal episodes and builds batch CSVs. |
| `11_heatmap_xy.py` | Heatmap bins derived from trajectory CSVs. |
| `12_plot_metric_figures.py` | Creates report-ready plots from generated CSVs. |

## Environment

Use a terminal with ROS 2 and the simulation workspace sourced:

```bash
cd /media/josedanielchg/Data/Proyectos/Robotica/footbot

source /opt/ros/humble/setup.bash
source simulation/ros2_ws/install/setup.bash

python3 -m pip install --user -r reports/footbot-simulation-es/metrics/requirements.txt
```

`rclpy`, `rosbag2_py`, and custom ROS interfaces come from the sourced ROS 2
workspace. The Python requirements only cover data processing and plotting.

## Main Command

Record five Reach Goal episodes and generate the batch CSV folder:

```bash
python3 reports/footbot-simulation-es/metrics/scripts/10_record_reach_goal_trials.py \
  --episodes 5 \
  --timeout-sec 300 \
  --model-path simulation/ros2_ws/src/footbot_soccer_vision/models/reach_goal_ball_goal/reach_goal_ball_goal_v1_best.pt \
  --use-gui false \
  --show-debug-view false \
  --confidence-threshold 0.25 \
  --device 0 \
  --min-free-gb 20
```

Use `--device cpu` if CUDA is not available.

The recorder stops each episode when `/soccer/goal_scored` becomes true or when
the timeout expires. It writes:

```text
metrics/bags/reach_goal_trials_YYYYMMDD_HHMMSS/
metrics/csv/reach_goal_trials_YYYYMMDD_HHMMSS/
```

## Disk Safety

Long runs do not record `/camera/image_raw` by default. Raw camera images can
turn one episode into tens of gigabytes.

For a short latency-only run, enable camera recording explicitly:

```bash
python3 reports/footbot-simulation-es/metrics/scripts/10_record_reach_goal_trials.py \
  --episodes 1 \
  --timeout-sec 60 \
  --record-camera \
  --model-path simulation/ros2_ws/src/footbot_soccer_vision/models/reach_goal_ball_goal/reach_goal_ball_goal_v1_best.pt \
  --use-gui false \
  --show-debug-view false \
  --confidence-threshold 0.25 \
  --device 0 \
  --min-free-gb 40
```

Useful recorder options:

```text
--build-only                 Rebuild CSVs from existing bags.
--overwrite                  Replace an existing episode bag.
--record-camera              Add /camera/image_raw.
--record-ball-control-topics Add legacy Ball Control topics.
--extra-topic /topic/name    Record one extra topic; repeat as needed.
--goal-ignore-sec 8          Ignore stale score messages during startup.
--compression-mode file      Use rosbag compression.
--min-free-gb 20             Abort before filling the disk.
```

## Rebuild CSVs From Existing Bags

Use this when the bags already exist and only the CSVs need to be regenerated:

```bash
python3 reports/footbot-simulation-es/metrics/scripts/10_record_reach_goal_trials.py \
  --build-only \
  --output-dir reports/footbot-simulation-es/metrics/bags/reach_goal_trials_YYYYMMDD_HHMMSS \
  --csv-dir reports/footbot-simulation-es/metrics/csv/reach_goal_trials_YYYYMMDD_HHMMSS
```

This does not launch Gazebo and does not record new data.

## Generate Figures

After CSVs exist, build report-ready figures:

```bash
python3 reports/footbot-simulation-es/metrics/scripts/12_plot_metric_figures.py \
  --csv-dir reports/footbot-simulation-es/metrics/csv/reach_goal_trials_YYYYMMDD_HHMMSS \
  --output-dir reports/footbot-simulation-es/figures/metrics
```

The plotting script is best-effort. If a CSV is missing, for example latency
without `--record-camera`, it skips that figure and continues.

## Key CSVs

| CSV | Use |
|---|---|
| `00_reach_goal_trial_runs.csv` | Episode metadata and stop reason. |
| `02_topic_hz_trials.csv` | Topic rates. |
| `03_time_to_ball_control_trials.csv` | Time to first ball control. |
| `04_time_to_goal_trials.csv` | Time to score. |
| `05_goal_success_rate.csv` | Success rate summary. |
| `06_fsm_state_time_trials.csv` | Time spent in each FSM state. |
| `06_fsm_state_timeline_trials.csv` | Raw FSM timeline for state-band plots. |
| `07_fsm_event_counts_trials.csv` | Recovery and commit event counts. |
| `09_trajectory_xy_trials.csv` | Robot and ball trajectories. |
| `11_heatmap_xy_trials.csv` | Robot and ball heatmap source data. |

## Manual Debug Run

To watch one Reach Goal simulation without recording metrics:

```bash
cd /media/josedanielchg/Data/Proyectos/Robotica/footbot

source /opt/ros/humble/setup.bash
source simulation/ros2_ws/install/setup.bash

ros2 launch footbot_bringup reach_goal.launch.py \
  model_path:=/media/josedanielchg/Data/Proyectos/Robotica/footbot/simulation/ros2_ws/src/footbot_soccer_vision/models/reach_goal_ball_goal/reach_goal_ball_goal_v1_best.pt \
  use_gui:=true \
  show_debug_view:=true \
  run_behavior:=true \
  run_score_monitor:=true \
  confidence_threshold:=0.25 \
  device:=0
```

## Notes

- `/world/footbot_world/pose/info` is recorded only for analysis and referee
  metrics. The robot behavior remains camera/perception driven.
- Use `/soccer/reach_goal_fsm_state` for Reach Goal experiments.
- Use `/soccer/fsm_state` for older Ball Control experiments.
- If later episodes finish in only a few seconds, inspect
  `/soccer/goal_scored` and consider increasing `--goal-ignore-sec`.
