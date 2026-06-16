#!/usr/bin/env bash

# Run the CSV builders for the FootBot simulation report.
# This script is intentionally best-effort: one failed builder does not stop the
# rest, which is useful when a bag does not contain every topic.

set -u

METRICS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
BAG=""
EPISODES_DIR=""
WEIGHTS=""
DATA=""
EPISODE="episode_001"
SCENARIO=""

usage() {
  cat <<'EOF'
Usage:
  ./run_all.sh --bag BAG_DIR [--episodes-dir DIR] [--weights MODEL.pt --data data.yaml]

Options:
  --bag DIR          rosbag2 directory for single-episode builders.
  --episodes-dir DIR Directory containing multiple episode bags for success rate.
  --weights PATH     YOLO weights for 08_yolo_eval.py.
  --data PATH        YOLO data.yaml for 08_yolo_eval.py.
  --episode LABEL    Episode label written by applicable CSV builders.
  --scenario LABEL   Scenario label written by applicable CSV builders.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --bag) BAG="$2"; shift 2 ;;
    --episodes-dir) EPISODES_DIR="$2"; shift 2 ;;
    --weights) WEIGHTS="$2"; shift 2 ;;
    --data) DATA="$2"; shift 2 ;;
    --episode) EPISODE="$2"; shift 2 ;;
    --scenario) SCENARIO="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "unknown argument: $1" >&2; usage; exit 2 ;;
  esac
done

run_step() {
  echo
  echo "==> $*"
  "$@" || echo "warning: failed: $*" >&2
}

if [[ -z "$BAG" ]]; then
  usage >&2
  exit 2
fi

if [[ -z "$EPISODES_DIR" ]]; then
  EPISODES_DIR="$(dirname "$BAG")"
fi

run_step "$PYTHON_BIN" "$METRICS_DIR/scripts/01_loop_latency.py" --input "$BAG"
run_step "$PYTHON_BIN" "$METRICS_DIR/scripts/02_topic_hz.py" --input "$BAG"
run_step "$PYTHON_BIN" "$METRICS_DIR/scripts/03_time_to_ball_control.py" --input "$BAG" --episode "$EPISODE" --scenario "$SCENARIO"
run_step "$PYTHON_BIN" "$METRICS_DIR/scripts/04_time_to_goal.py" --input "$BAG" --episode "$EPISODE" --scenario "$SCENARIO"
run_step "$PYTHON_BIN" "$METRICS_DIR/scripts/05_goal_success_rate.py" --input "$EPISODES_DIR"
run_step "$PYTHON_BIN" "$METRICS_DIR/scripts/06_fsm_state_time.py" --input "$BAG" --episode "$EPISODE" --scenario "$SCENARIO"
run_step "$PYTHON_BIN" "$METRICS_DIR/scripts/07_fsm_event_counts.py" --input "$BAG" --episode "$EPISODE" --scenario "$SCENARIO"
run_step "$PYTHON_BIN" "$METRICS_DIR/scripts/09_trajectory_xy.py" --input "$BAG" --episode "$EPISODE" --scenario "$SCENARIO"
if [[ -f "$METRICS_DIR/csv/09_trajectory_xy.csv" ]]; then
  run_step "$PYTHON_BIN" "$METRICS_DIR/scripts/11_heatmap_xy.py" \
    --input "$METRICS_DIR/csv/09_trajectory_xy.csv" \
    --output "$METRICS_DIR/csv/11_heatmap_xy.csv"
fi

if [[ -n "$WEIGHTS" && -n "$DATA" ]]; then
  run_step "$PYTHON_BIN" "$METRICS_DIR/scripts/08_yolo_eval.py" --weights "$WEIGHTS" --data "$DATA"
else
  echo
  echo "==> Skipping 08_yolo_eval.py; pass --weights and --data to enable it."
fi
