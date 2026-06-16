#!/usr/bin/env python3
"""Record multiple Reach Goal trials and build batch metric CSVs.

This orchestration helper launches the Reach Goal simulation, starts
``ros2 bag record``, stops the episode when ``/soccer/goal_scored`` becomes true
or when the timeout expires, and repeats the process. After recording, it runs
the CSV builders needed for five-episode analysis.
"""

from __future__ import annotations

import argparse
import csv
import os
import shutil
import signal
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path


DEFAULT_TOPICS = [
    '/cmd_vel',
    '/soccer/detections',
    '/soccer/ball_goal_state',
    '/soccer/reach_goal_fsm_state',
    '/soccer/goal_scored',
    '/world/footbot_world/pose/info',
]

CAMERA_TOPICS = [
    '/camera/image_raw',
]

BALL_CONTROL_TOPICS = [
    '/ball_detection',
    '/soccer/ball_state',
    '/soccer/fsm_state',
]


def repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def metrics_root() -> Path:
    return Path(__file__).resolve().parents[1]


def default_model_path() -> Path:
    return (
        repo_root()
        / 'simulation/ros2_ws/src/footbot_soccer_vision/models/reach_goal_ball_goal/reach_goal_ball_goal_v1_best.pt'
    )


def parse_args():
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    default_bag_dir = metrics_root() / 'bags' / f'reach_goal_trials_{timestamp}'
    default_csv_dir = metrics_root() / 'csv' / f'reach_goal_trials_{timestamp}'

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--episodes', type=int, default=5)
    parser.add_argument('--timeout-sec', type=float, default=300.0)
    parser.add_argument('--output-dir', default=str(default_bag_dir), help='Directory where episode bags are stored.')
    parser.add_argument('--csv-dir', default=str(default_csv_dir), help='Directory where batch CSVs are written.')
    parser.add_argument('--model-path', default=str(default_model_path()))
    parser.add_argument('--confidence-threshold', default='0.25')
    parser.add_argument('--device', default='cpu')
    parser.add_argument('--use-gui', default='false')
    parser.add_argument('--show-debug-view', default='false')
    parser.add_argument('--scenario', default='reach_goal')
    parser.add_argument('--goal-topic', default='/soccer/goal_scored')
    parser.add_argument('--fsm-topic', default='/soccer/reach_goal_fsm_state')
    parser.add_argument(
        '--goal-ignore-sec',
        type=float,
        default=8.0,
        help=(
            'Ignore true /soccer/goal_scored messages during the first N seconds '
            'of each episode. This filters queued score messages and startup '
            'poses from the previous run.'
        ),
    )
    parser.add_argument('--post-goal-record-sec', type=float, default=1.0)
    parser.add_argument('--between-episodes-sec', type=float, default=3.0)
    parser.add_argument('--topics', nargs='*', default=DEFAULT_TOPICS)
    parser.add_argument(
        '--record-camera',
        action='store_true',
        help=(
            'Also record /camera/image_raw. This is required for latency metrics, '
            'but it creates very large bags; prefer short runs when enabling it.'
        ),
    )
    parser.add_argument(
        '--record-ball-control-topics',
        action='store_true',
        help='Also record legacy Ball Control topics used by older metrics.',
    )
    parser.add_argument(
        '--extra-topic',
        action='append',
        default=[],
        help='Additional topic to record. Can be repeated.',
    )
    parser.add_argument(
        '--min-free-gb',
        type=float,
        default=20.0,
        help='Abort before each episode if the output filesystem has less free space than this.',
    )
    parser.add_argument(
        '--compression-mode',
        choices=['file', 'message'],
        default='',
        help='Optional rosbag2 compression mode. Leave empty for no compression.',
    )
    parser.add_argument(
        '--compression-format',
        default='zstd',
        help='Compression format used when --compression-mode is set.',
    )
    parser.add_argument(
        '--launch-arg',
        action='append',
        default=[],
        help='Extra reach_goal.launch.py argument, e.g. --launch-arg ball_x:=0.70',
    )
    parser.add_argument('--overwrite', action='store_true')
    parser.add_argument('--skip-csv', action='store_true')
    parser.add_argument(
        '--build-only',
        action='store_true',
        help='Do not run simulations; rebuild batch CSVs from existing episode bags in --output-dir.',
    )
    return parser.parse_args()


def require_ros_environment():
    try:
        import rclpy  # noqa: F401
        from std_msgs.msg import Bool  # noqa: F401
    except ImportError as exc:
        raise SystemExit(
            'error: ROS Python modules are not importable. Source ROS 2 and the '
            'workspace first:\n'
            '  source /opt/ros/humble/setup.bash\n'
            '  source simulation/ros2_ws/install/setup.bash'
        ) from exc

    result = subprocess.run(
        ['ros2', 'pkg', 'prefix', 'footbot_bringup'],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if result.returncode != 0:
        raise SystemExit(
            'error: footbot_bringup was not found. Source the workspace first:\n'
            '  source simulation/ros2_ws/install/setup.bash'
        )


def terminate_process_group(process: subprocess.Popen, label: str, timeout_sec: float = 15.0):
    if process.poll() is not None:
        return
    try:
        os.killpg(os.getpgid(process.pid), signal.SIGINT)
        process.wait(timeout=timeout_sec)
        return
    except subprocess.TimeoutExpired:
        print(f'warning: {label} did not stop after SIGINT; sending SIGTERM', file=sys.stderr)
    except ProcessLookupError:
        return

    if process.poll() is None:
        try:
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            process.wait(timeout=5.0)
        except (subprocess.TimeoutExpired, ProcessLookupError):
            if process.poll() is None:
                process.kill()


def launch_command(args):
    command = [
        'ros2',
        'launch',
        'footbot_bringup',
        'reach_goal.launch.py',
        f'model_path:={args.model_path}',
        f'use_gui:={args.use_gui}',
        f'show_debug_view:={args.show_debug_view}',
        'run_behavior:=true',
        'run_score_monitor:=true',
        f'confidence_threshold:={args.confidence_threshold}',
        f'device:={args.device}',
    ]
    command.extend(args.launch_arg)
    return command


def recorder_command(args, bag_path):
    command = ['ros2', 'bag', 'record', *selected_topics(args), '-o', str(bag_path)]
    if args.compression_mode:
        command.extend([
            '--compression-mode',
            args.compression_mode,
            '--compression-format',
            args.compression_format,
        ])
    return command


def selected_topics(args):
    topics = list(args.topics)
    if args.record_camera:
        topics.extend(CAMERA_TOPICS)
    if args.record_ball_control_topics:
        topics.extend(BALL_CONTROL_TOPICS)
    topics.extend(args.extra_topic)

    unique_topics = []
    seen = set()
    for topic in topics:
        if topic not in seen:
            unique_topics.append(topic)
            seen.add(topic)
    return unique_topics


def ensure_free_space(path: Path, min_free_gb: float):
    if min_free_gb <= 0.0:
        return
    usage = shutil.disk_usage(path)
    free_gb = usage.free / (1024 ** 3)
    if free_gb < min_free_gb:
        raise SystemExit(
            f'error: only {free_gb:.1f} GB free at {path}. '
            f'Required at least {min_free_gb:.1f} GB. '
            'Delete old bags or lower --min-free-gb if you intentionally want to continue.'
        )


class GoalMonitor:
    def __init__(self, topic):
        import rclpy
        from rclpy.node import Node
        from std_msgs.msg import Bool

        self.rclpy = rclpy
        self.scored = False
        self.ignore_until = 0.0
        self.ignored_true_count = 0
        self.node = Node('reach_goal_trial_monitor')
        self.subscription = self.node.create_subscription(Bool, topic, self._on_goal, 10)

    def _on_goal(self, message):
        if bool(message.data):
            if time.monotonic() < self.ignore_until:
                self.ignored_true_count += 1
                return
            self.scored = True

    def reset(self, ignore_until=0.0):
        self.scored = False
        self.ignore_until = float(ignore_until)
        self.ignored_true_count = 0

    def spin_once(self, timeout_sec=0.2):
        self.rclpy.spin_once(self.node, timeout_sec=timeout_sec)

    def destroy(self):
        self.node.destroy_node()


def run_episode(args, monitor, output_dir: Path, episode_index: int):
    label = f'episode_{episode_index:03d}'
    bag_path = output_dir / label
    ensure_free_space(output_dir, args.min_free_gb)
    if bag_path.exists():
        if not args.overwrite:
            raise SystemExit(f'error: bag already exists: {bag_path}. Use --overwrite to replace it.')
        shutil.rmtree(bag_path)

    launch_log = output_dir / f'{label}_launch.log'
    record_log = output_dir / f'{label}_record.log'

    print(f'\n=== Starting {label} ===')
    print(f'bag: {bag_path}')
    print(f'recording topics: {", ".join(selected_topics(args))}')
    with launch_log.open('w', encoding='utf-8') as launch_handle, record_log.open('w', encoding='utf-8') as record_handle:
        launch_proc = subprocess.Popen(
            launch_command(args),
            stdout=launch_handle,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        record_proc = subprocess.Popen(
            recorder_command(args, bag_path),
            stdout=record_handle,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )

        start = time.monotonic()
        monitor.reset(ignore_until=start + max(args.goal_ignore_sec, 0.0))
        reason = 'timeout'
        scored = False
        try:
            while time.monotonic() - start < args.timeout_sec:
                monitor.spin_once(timeout_sec=0.2)
                if monitor.scored:
                    scored = True
                    reason = 'goal_scored'
                    print(f'{label}: goal scored, recording {args.post_goal_record_sec:.1f}s more...')
                    time.sleep(max(args.post_goal_record_sec, 0.0))
                    break
                if launch_proc.poll() is not None:
                    reason = f'launch_exited_{launch_proc.returncode}'
                    print(f'warning: {label}: launch process exited early', file=sys.stderr)
                    break
        finally:
            terminate_process_group(record_proc, f'{label} recorder')
            terminate_process_group(launch_proc, f'{label} launch')

    elapsed = time.monotonic() - start
    if monitor.ignored_true_count:
        print(
            f'{label}: ignored {monitor.ignored_true_count} early goal_scored=true '
            f'message(s) during startup grace period'
        )
    print(f'{label}: finished reason={reason} scored={scored} elapsed_s={elapsed:.2f}')
    if args.between_episodes_sec > 0.0:
        time.sleep(args.between_episodes_sec)
    return {
        'episode': label,
        'bag_path': str(bag_path),
        'scored_live': scored,
        'stop_reason': reason,
        'elapsed_wall_s': elapsed,
    }


def run_builder(command):
    print(f'==> {" ".join(command)}')
    result = subprocess.run(command, check=False)
    if result.returncode != 0:
        print(f'warning: builder failed with exit {result.returncode}: {" ".join(command)}', file=sys.stderr)
    return result.returncode


def combine_csv(inputs, output):
    inputs = [Path(path) for path in inputs if Path(path).exists()]
    if not inputs:
        return

    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    wrote_header = False
    with output.open('w', encoding='utf-8', newline='') as out_handle:
        writer = None
        for path in inputs:
            with path.open('r', encoding='utf-8', newline='') as in_handle:
                reader = csv.DictReader(in_handle)
                if reader.fieldnames is None:
                    continue
                if writer is None:
                    writer = csv.DictWriter(out_handle, fieldnames=reader.fieldnames)
                    writer.writeheader()
                    wrote_header = True
                for row in reader:
                    writer.writerow(row)
    if wrote_header:
        print(output)


def bag_has_topic(bag_path, topic):
    metadata = Path(bag_path) / 'metadata.yaml'
    if not metadata.exists():
        return False
    return topic in metadata.read_text(encoding='utf-8', errors='ignore')


def build_batch_csvs(args, run_rows, csv_dir: Path, output_dir: Path):
    scripts_dir = metrics_root() / 'scripts'
    csv_dir.mkdir(parents=True, exist_ok=True)

    trial_csv = csv_dir / '00_reach_goal_trial_runs.csv'
    with trial_csv.open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=['episode', 'bag_path', 'scored_live', 'stop_reason', 'elapsed_wall_s'],
        )
        writer.writeheader()
        writer.writerows(run_rows)
    print(trial_csv)

    latency_files = []
    latency_summary_files = []
    topic_hz_files = []
    ball_control_files = []
    time_goal_files = []
    state_time_files = []
    event_files = []
    timeline_files = []
    trajectory_files = []

    for row in run_rows:
        episode = row['episode']
        bag = row['bag_path']

        if bag_has_topic(bag, '/camera/image_raw'):
            run_builder([
                sys.executable,
                str(scripts_dir / '01_loop_latency.py'),
                '--input',
                bag,
                '--output',
                str(csv_dir / f'01_loop_latency_{episode}.csv'),
                '--summary-output',
                str(csv_dir / f'01_loop_latency_summary_{episode}.csv'),
            ])
            latency_files.append(csv_dir / f'01_loop_latency_{episode}.csv')
            latency_summary_files.append(csv_dir / f'01_loop_latency_summary_{episode}.csv')
        else:
            print(f'skipping 01_loop_latency for {episode}: /camera/image_raw was not recorded')

        run_builder([
            sys.executable,
            str(scripts_dir / '02_topic_hz.py'),
            '--input',
            bag,
            '--output',
            str(csv_dir / f'02_topic_hz_{episode}.csv'),
        ])
        topic_hz_files.append(csv_dir / f'02_topic_hz_{episode}.csv')

        run_builder([
            sys.executable,
            str(scripts_dir / '03_time_to_ball_control.py'),
            '--input',
            bag,
            '--episode',
            episode,
            '--scenario',
            args.scenario,
            '--fsm-topic',
            args.fsm_topic,
            '--control-states',
            'CONTROL_BALL',
            'DRIBBLE_TO_GOAL',
            'COMMIT_TO_GOAL',
            'GOAL_SCORED',
            '--output',
            str(csv_dir / f'03_time_to_ball_control_{episode}.csv'),
        ])
        ball_control_files.append(csv_dir / f'03_time_to_ball_control_{episode}.csv')

        run_builder([
            sys.executable,
            str(scripts_dir / '04_time_to_goal.py'),
            '--input',
            bag,
            '--episode',
            episode,
            '--output',
            str(csv_dir / f'04_time_to_goal_{episode}.csv'),
        ])
        time_goal_files.append(csv_dir / f'04_time_to_goal_{episode}.csv')

        run_builder([
            sys.executable,
            str(scripts_dir / '06_fsm_state_time.py'),
            '--input',
            bag,
            '--episode',
            episode,
            '--scenario',
            args.scenario,
            '--fsm-topic',
            args.fsm_topic,
            '--output',
            str(csv_dir / f'06_fsm_state_time_{episode}.csv'),
            '--timeline-output',
            str(csv_dir / f'06_fsm_state_timeline_{episode}.csv'),
        ])
        state_time_files.append(csv_dir / f'06_fsm_state_time_{episode}.csv')
        timeline_files.append(csv_dir / f'06_fsm_state_timeline_{episode}.csv')

        run_builder([
            sys.executable,
            str(scripts_dir / '07_fsm_event_counts.py'),
            '--input',
            bag,
            '--episode',
            episode,
            '--scenario',
            args.scenario,
            '--fsm-topic',
            args.fsm_topic,
            '--output',
            str(csv_dir / f'07_fsm_event_counts_{episode}.csv'),
        ])
        event_files.append(csv_dir / f'07_fsm_event_counts_{episode}.csv')

        run_builder([
            sys.executable,
            str(scripts_dir / '09_trajectory_xy.py'),
            '--input',
            bag,
            '--episode',
            episode,
            '--scenario',
            args.scenario,
            '--output',
            str(csv_dir / f'09_trajectory_xy_{episode}.csv'),
        ])
        trajectory_files.append(csv_dir / f'09_trajectory_xy_{episode}.csv')

    run_builder([
        sys.executable,
        str(scripts_dir / '05_goal_success_rate.py'),
        '--input',
        str(output_dir),
        '--output',
        str(csv_dir / '05_goal_success_rate.csv'),
    ])

    combine_csv(latency_files, csv_dir / '01_loop_latency_trials.csv')
    combine_csv(latency_summary_files, csv_dir / '01_loop_latency_summary_trials.csv')
    combine_csv(topic_hz_files, csv_dir / '02_topic_hz_trials.csv')
    combine_csv(ball_control_files, csv_dir / '03_time_to_ball_control_trials.csv')
    combine_csv(time_goal_files, csv_dir / '04_time_to_goal_trials.csv')
    combine_csv(state_time_files, csv_dir / '06_fsm_state_time_trials.csv')
    combine_csv(event_files, csv_dir / '07_fsm_event_counts_trials.csv')
    combine_csv(timeline_files, csv_dir / '06_fsm_state_timeline_trials.csv')
    combine_csv(trajectory_files, csv_dir / '09_trajectory_xy_trials.csv')
    if (csv_dir / '09_trajectory_xy_trials.csv').exists():
        run_builder([
            sys.executable,
            str(scripts_dir / '11_heatmap_xy.py'),
            '--input',
            str(csv_dir / '09_trajectory_xy_trials.csv'),
            '--output',
            str(csv_dir / '11_heatmap_xy_trials.csv'),
        ])


def run_rows_from_existing_bags(output_dir: Path):
    rows = []
    for metadata in sorted(output_dir.glob('episode_*/metadata.yaml')):
        bag_path = metadata.parent
        rows.append({
            'episode': bag_path.name,
            'bag_path': str(bag_path),
            'scored_live': '',
            'stop_reason': 'existing_bag',
            'elapsed_wall_s': '',
        })
    if not rows:
        raise SystemExit(f'error: no existing episode bags found under {output_dir}')
    return rows


def main():
    args = parse_args()
    require_ros_environment()

    if not args.build_only:
        model_path = Path(args.model_path).expanduser()
        if not model_path.exists():
            raise SystemExit(f'error: model weights not found: {model_path}')
        args.model_path = str(model_path)

    output_dir = Path(args.output_dir).expanduser()
    csv_dir = Path(args.csv_dir).expanduser()
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_dir.mkdir(parents=True, exist_ok=True)

    if args.build_only:
        run_rows = run_rows_from_existing_bags(output_dir)
    else:
        import rclpy

        rclpy.init(args=None)
        monitor = GoalMonitor(args.goal_topic)
        run_rows = []
        try:
            for episode_index in range(1, args.episodes + 1):
                run_rows.append(run_episode(args, monitor, output_dir, episode_index))
        finally:
            monitor.destroy()
            if rclpy.ok():
                rclpy.shutdown()

    if not args.skip_csv:
        build_batch_csvs(args, run_rows, csv_dir, output_dir)

    print('\nDone.')
    print(f'Bags: {output_dir}')
    print(f'CSVs: {csv_dir}')


if __name__ == '__main__':
    main()
