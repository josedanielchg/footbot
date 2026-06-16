"""Offline rosbag2 helpers for the FootBot simulation report metrics.

The metric scripts intentionally avoid a live ROS graph where possible. This
module wraps ``rosbag2_py.SequentialReader`` and deserializes messages by using
the recorded topic type metadata from the bag.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional, Sequence, Tuple

import yaml


class BagReadError(RuntimeError):
    """Raised when a bag cannot be opened or does not contain required data."""


@dataclass(frozen=True)
class BagMessage:
    """A deserialized message with its recorded rosbag timestamp."""

    topic: str
    msg: object
    timestamp_ns: int
    type_name: str

    @property
    def timestamp_s(self) -> float:
        return self.timestamp_ns / 1_000_000_000.0


def resolve_bag_uri(path: str | Path) -> Path:
    """Return the URI that rosbag2 should open.

    Most ROS 2 bags are directories containing ``metadata.yaml``. If a user
    passes the metadata file or an SQLite file inside the directory, normalize
    back to the bag directory.
    """

    bag_path = Path(path).expanduser()
    if not bag_path.exists():
        raise BagReadError(f'bag path does not exist: {bag_path}')

    if bag_path.is_file() and bag_path.name == 'metadata.yaml':
        return bag_path.parent
    if bag_path.is_file() and bag_path.suffix in {'.db3', '.sqlite3'}:
        return bag_path.parent
    return bag_path


def metadata_path(path: str | Path) -> Path:
    uri = resolve_bag_uri(path)
    meta = uri / 'metadata.yaml'
    if not meta.exists():
        raise BagReadError(f'rosbag2 metadata.yaml not found under: {uri}')
    return meta


def load_metadata(path: str | Path) -> dict:
    with metadata_path(path).open('r', encoding='utf-8') as handle:
        data = yaml.safe_load(handle) or {}
    return data.get('rosbag2_bagfile_information', data)


def storage_id(path: str | Path) -> str:
    info = load_metadata(path)
    storage = info.get('storage_identifier')
    if storage:
        return str(storage)

    files = info.get('relative_file_paths') or []
    if any(str(name).endswith('.mcap') for name in files):
        return 'mcap'
    return 'sqlite3'


def bag_duration_s(path: str | Path) -> Optional[float]:
    info = load_metadata(path)
    duration = info.get('duration')
    if isinstance(duration, dict) and 'nanoseconds' in duration:
        return float(duration['nanoseconds']) / 1_000_000_000.0
    if isinstance(duration, (int, float)):
        # Some rosbag2 versions store this directly as nanoseconds.
        return float(duration) / 1_000_000_000.0
    return None


def _open_reader(path: str | Path):
    try:
        import rosbag2_py
    except ImportError as exc:
        raise BagReadError(
            'rosbag2_py is not importable. Source ROS 2 first, e.g. '
            '`source /opt/ros/humble/setup.bash`.'
        ) from exc

    uri = resolve_bag_uri(path)
    reader = rosbag2_py.SequentialReader()
    storage_options = rosbag2_py.StorageOptions(
        uri=str(uri),
        storage_id=storage_id(uri),
    )
    converter_options = rosbag2_py.ConverterOptions(
        input_serialization_format='cdr',
        output_serialization_format='cdr',
    )
    reader.open(storage_options, converter_options)
    return reader


def topic_types(path: str | Path) -> Dict[str, str]:
    reader = _open_reader(path)
    return {
        item.name: item.type
        for item in reader.get_all_topics_and_types()
    }


def require_topics(
    path: str | Path,
    topics: Sequence[str],
    *,
    allow_empty: bool = False,
) -> Dict[str, str]:
    available = topic_types(path)
    missing = [topic for topic in topics if topic not in available]
    if missing and not allow_empty:
        formatted = '\n  '.join(sorted(available))
        raise BagReadError(
            f'missing required topic(s): {", ".join(missing)}\n'
            f'available topics:\n  {formatted}'
        )
    return available


def read_messages(
    path: str | Path,
    topics: Optional[Iterable[str]] = None,
) -> Iterator[BagMessage]:
    """Yield deserialized messages from a rosbag2 directory."""

    try:
        from rclpy.serialization import deserialize_message
        from rosidl_runtime_py.utilities import get_message
    except ImportError as exc:
        raise BagReadError(
            'ROS Python message utilities are not importable. Source ROS 2 and '
            'the FootBot workspace before running this script.'
        ) from exc

    wanted = set(topics) if topics is not None else None
    reader = _open_reader(path)
    type_map = {
        item.name: item.type
        for item in reader.get_all_topics_and_types()
    }
    message_classes = {}

    while reader.has_next():
        topic, data, timestamp_ns = reader.read_next()
        if wanted is not None and topic not in wanted:
            continue
        type_name = type_map.get(topic)
        if type_name is None:
            continue
        if type_name not in message_classes:
            message_classes[type_name] = get_message(type_name)
        msg = deserialize_message(data, message_classes[type_name])
        yield BagMessage(topic=topic, msg=msg, timestamp_ns=int(timestamp_ns), type_name=type_name)


def bag_time_bounds(path: str | Path, topics: Optional[Iterable[str]] = None) -> Tuple[Optional[float], Optional[float]]:
    start_ns = None
    end_ns = None
    for item in read_messages(path, topics=topics):
        start_ns = item.timestamp_ns if start_ns is None else min(start_ns, item.timestamp_ns)
        end_ns = item.timestamp_ns if end_ns is None else max(end_ns, item.timestamp_ns)
    if start_ns is None or end_ns is None:
        return None, None
    return start_ns / 1_000_000_000.0, end_ns / 1_000_000_000.0


def stamp_to_seconds(stamp) -> float:
    return float(stamp.sec) + float(stamp.nanosec) / 1_000_000_000.0


def message_stamp_s(message: object, fallback_s: float) -> float:
    header = getattr(message, 'header', None)
    stamp = getattr(header, 'stamp', None)
    if stamp is None:
        return fallback_s
    value = stamp_to_seconds(stamp)
    return value if value > 0.0 else fallback_s


def string_data(message: object) -> str:
    return str(getattr(message, 'data', ''))


def bool_data(message: object) -> bool:
    return bool(getattr(message, 'data', False))


def discover_bags(path: str | Path) -> List[Path]:
    """Find rosbag2 directories under ``path``."""

    root = Path(path).expanduser()
    if not root.exists():
        raise BagReadError(f'input path does not exist: {root}')
    if root.is_file():
        return [resolve_bag_uri(root)]
    if (root / 'metadata.yaml').exists():
        return [root]
    return sorted({meta.parent for meta in root.rglob('metadata.yaml')})

