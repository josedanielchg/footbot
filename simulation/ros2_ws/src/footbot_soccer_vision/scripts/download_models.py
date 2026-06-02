#!/usr/bin/env python3
from pathlib import Path


def main():
    try:
        from ultralytics import YOLO
    except ImportError as exc:
        raise SystemExit(
            'Ultralytics is not installed. Run: '
            'python3 -m pip install --user -r simulation/requirements-yolo.txt'
        ) from exc

    package_root = Path(__file__).resolve().parents[1]
    weights_dir = package_root / 'models' / 'weights'
    weights_dir.mkdir(parents=True, exist_ok=True)
    output_path = weights_dir / 'yolo11n.pt'

    model = YOLO('yolo11n.pt')
    source_path = Path(model.ckpt_path).expanduser()
    if source_path.resolve() != output_path.resolve():
        output_path.write_bytes(source_path.read_bytes())

    print(f'Saved {output_path}')


if __name__ == '__main__':
    main()
