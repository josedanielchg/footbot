"""Small CSV and CLI helpers shared by metric scripts."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Mapping


def metrics_root() -> Path:
    return Path(__file__).resolve().parents[1]


def default_csv_path(name: str) -> Path:
    return metrics_root() / 'csv' / name


def write_csv(rows: Iterable[Mapping], output: str | Path, columns=None) -> Path:
    try:
        import pandas as pd
    except ImportError as exc:
        raise SystemExit(
            'error: pandas is required to write CSV files. Install '
            '`reports/footbot-simulation-es/metrics/requirements.txt`.'
        ) from exc

    path = Path(output).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame(list(rows), columns=columns)
    frame.to_csv(path, index=False)
    print(path)
    return path


def add_common_args(parser, *, default_name: str, input_help: str = 'rosbag2 directory'):
    parser.add_argument('--input', required=True, help=input_help)
    parser.add_argument(
        '--output',
        default=str(default_csv_path(default_name)),
        help='CSV output path.',
    )
    parser.add_argument('--episode', default='episode_001', help='Episode label.')
    parser.add_argument('--scenario', default='', help='Scenario label.')


def fail(message: str) -> None:
    raise SystemExit(f'error: {message}')
