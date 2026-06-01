#!/usr/bin/env python3
"""Create simple unlabeled image augmentations for FootBot soccer vision.

This script is intentionally conservative because the images come from a
simulation dataset. It does not read, transform, or generate YOLO labels.
Generated images must still be labeled manually before training.
"""

from __future__ import annotations

import argparse
import json
import shutil
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import cv2
import numpy as np


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
LETTERBOX_COLOR = (114, 114, 114)


@dataclass
class GeneratedRecord:
    output_file: str
    source_file: str
    kind: str
    transformation: dict[str, Any]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate simple rotated and mildly darkened images for later "
            "manual YOLO labeling."
        )
    )
    parser.add_argument(
        "--input-dir",
        default=(
            "simulation/ros2_ws/src/footbot_soccer_vision/datasets/"
            "raw/soccer_v1/images"
        ),
        help="Directory containing original images.",
    )
    parser.add_argument(
        "--output-dir",
        default=(
            "simulation/ros2_ws/src/footbot_soccer_vision/datasets/"
            "raw/soccer_v1/augmented_images"
        ),
        help="Directory where generated images and metadata will be written.",
    )
    parser.add_argument(
        "--output-size",
        nargs=2,
        type=int,
        metavar=("WIDTH", "HEIGHT"),
        default=[640, 640],
        help="Output image size. Use 640 640 for YOLO training.",
    )
    parser.add_argument(
        "--rotation-angles",
        nargs="+",
        type=float,
        default=[90.0, 180.0, 270.0],
        help="Rotation angles in degrees. Default creates 3 augmentations per image.",
    )
    parser.add_argument(
        "--brightness-factor",
        type=float,
        default=0.85,
        help="Mild brightness multiplier applied to rotated images.",
    )
    parser.add_argument(
        "--copy-originals",
        action="store_true",
        help="Also write resized/letterboxed copies of the original images.",
    )
    parser.add_argument(
        "--clean-output",
        action="store_true",
        help="Remove previous image outputs and metadata before generating.",
    )
    return parser.parse_args()


def list_images(input_dir: Path) -> list[Path]:
    if not input_dir.exists():
        return []
    return sorted(
        path
        for path in input_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    )


def read_image(path: Path) -> np.ndarray | None:
    image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if image is None:
        print(f"warning: could not read image: {path}")
    return image


def clean_output_dir(output_dir: Path) -> None:
    if not output_dir.exists():
        return
    for child in output_dir.iterdir():
        if child.is_file() and (
            child.suffix.lower() in IMAGE_EXTENSIONS
            or child.name == "augmentation_metadata.json"
        ):
            child.unlink()
        elif child.is_dir():
            shutil.rmtree(child)


def safe_stem(path: Path) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in path.stem)
    return cleaned.strip("_") or "image"


def format_angle(angle: float) -> str:
    if angle.is_integer():
        return f"{int(angle):03d}"
    return f"{angle:.1f}".replace("-", "m").replace(".", "p")


def format_brightness(factor: float) -> str:
    return f"{int(round(factor * 100)):03d}"


def letterbox(image: np.ndarray, output_size: tuple[int, int]) -> np.ndarray:
    out_w, out_h = output_size
    height, width = image.shape[:2]
    scale = min(out_w / width, out_h / height)
    resized_w = max(1, int(round(width * scale)))
    resized_h = max(1, int(round(height * scale)))
    resized = cv2.resize(image, (resized_w, resized_h), interpolation=cv2.INTER_AREA)

    canvas = np.full((out_h, out_w, 3), LETTERBOX_COLOR, dtype=np.uint8)
    x0 = (out_w - resized_w) // 2
    y0 = (out_h - resized_h) // 2
    canvas[y0 : y0 + resized_h, x0 : x0 + resized_w] = resized
    return canvas


def rotate_without_crop(image: np.ndarray, angle: float) -> np.ndarray:
    """Rotate an image while expanding the canvas so content is preserved."""
    normalized = angle % 360.0
    if normalized == 0.0:
        return image.copy()
    if normalized == 90.0:
        return cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
    if normalized == 180.0:
        return cv2.rotate(image, cv2.ROTATE_180)
    if normalized == 270.0:
        return cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)

    height, width = image.shape[:2]
    center = (width / 2.0, height / 2.0)
    matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    cos = abs(matrix[0, 0])
    sin = abs(matrix[0, 1])
    new_w = int((height * sin) + (width * cos))
    new_h = int((height * cos) + (width * sin))
    matrix[0, 2] += (new_w / 2.0) - center[0]
    matrix[1, 2] += (new_h / 2.0) - center[1]
    return cv2.warpAffine(
        image,
        matrix,
        (new_w, new_h),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=LETTERBOX_COLOR,
    )


def apply_brightness(image: np.ndarray, factor: float) -> np.ndarray:
    adjusted = image.astype(np.float32) * factor
    return np.clip(adjusted, 0, 255).astype(np.uint8)


def write_image(path: Path, image: np.ndarray) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    ok = cv2.imwrite(str(path), image)
    if not ok:
        print(f"warning: failed to write image: {path}")
    return ok


def copy_original(
    image_path: Path,
    image: np.ndarray,
    output_dir: Path,
    output_size: tuple[int, int],
) -> GeneratedRecord | None:
    output_name = f"{safe_stem(image_path)}_original.jpg"
    output_path = output_dir / output_name
    output_image = letterbox(image, output_size)
    if not write_image(output_path, output_image):
        return None
    return GeneratedRecord(
        output_file=str(output_path),
        source_file=str(image_path),
        kind="original_copy",
        transformation={
            "name": "copy_original",
            "letterbox": True,
            "output_width": output_size[0],
            "output_height": output_size[1],
        },
    )


def create_rotation(
    image_path: Path,
    image: np.ndarray,
    output_dir: Path,
    output_size: tuple[int, int],
    angle: float,
    brightness_factor: float,
) -> GeneratedRecord | None:
    rotated = rotate_without_crop(image, angle)
    darkened = apply_brightness(rotated, brightness_factor)
    output_image = letterbox(darkened, output_size)
    output_name = (
        f"{safe_stem(image_path)}_rot{format_angle(angle)}_"
        f"brightness{format_brightness(brightness_factor)}.jpg"
    )
    output_path = output_dir / output_name
    if not write_image(output_path, output_image):
        return None
    return GeneratedRecord(
        output_file=str(output_path),
        source_file=str(image_path),
        kind="rotation_brightness",
        transformation={
            "name": "rotation_brightness",
            "angle_degrees": angle,
            "brightness_factor": brightness_factor,
            "letterbox": True,
            "output_width": output_size[0],
            "output_height": output_size[1],
        },
    )


def write_metadata(
    output_dir: Path,
    input_dir: Path,
    output_size: tuple[int, int],
    rotation_angles: list[float],
    brightness_factor: float,
    copy_originals: bool,
    input_count: int,
    records: list[GeneratedRecord],
) -> None:
    copied_count = sum(1 for record in records if record.kind == "original_copy")
    augmented_count = sum(
        1 for record in records if record.kind == "rotation_brightness"
    )
    metadata = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "script": "augment_dataset.py",
        "input_dir": str(input_dir),
        "output_dir": str(output_dir),
        "output_size": {"width": output_size[0], "height": output_size[1]},
        "rotation_angles": rotation_angles,
        "brightness_factor": brightness_factor,
        "copy_originals": copy_originals,
        "input_image_count": input_count,
        "copied_original_image_count": copied_count,
        "augmented_image_count": augmented_count,
        "total_output_image_count": len(records),
        "generated_files": [asdict(record) for record in records],
        "label_note": (
            "Generated images are unlabeled and must be manually labeled before "
            "YOLO training."
        ),
    }
    metadata_path = output_dir / "augmentation_metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")


def validate_args(args: argparse.Namespace) -> None:
    if args.output_size[0] <= 0 or args.output_size[1] <= 0:
        raise ValueError("--output-size values must be positive")
    if not args.rotation_angles:
        raise ValueError("--rotation-angles must contain at least one angle")
    if args.brightness_factor <= 0:
        raise ValueError("--brightness-factor must be positive")
    if args.brightness_factor > 1.0:
        raise ValueError(
            "--brightness-factor should be <= 1.0 for this conservative workflow"
        )


def main() -> int:
    args = parse_args()
    validate_args(args)

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    output_size = (args.output_size[0], args.output_size[1])
    rotation_angles = [float(angle) for angle in args.rotation_angles]

    if args.clean_output:
        clean_output_dir(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    image_paths = list_images(input_dir)
    if not image_paths:
        print(f"warning: no input images found in {input_dir}")

    records: list[GeneratedRecord] = []
    for image_path in image_paths:
        image = read_image(image_path)
        if image is None:
            continue

        if args.copy_originals:
            original_record = copy_original(image_path, image, output_dir, output_size)
            if original_record:
                records.append(original_record)

        for angle in rotation_angles:
            augmented_record = create_rotation(
                image_path,
                image,
                output_dir,
                output_size,
                angle,
                args.brightness_factor,
            )
            if augmented_record:
                records.append(augmented_record)

    write_metadata(
        output_dir=output_dir,
        input_dir=input_dir,
        output_size=output_size,
        rotation_angles=rotation_angles,
        brightness_factor=args.brightness_factor,
        copy_originals=args.copy_originals,
        input_count=len(image_paths),
        records=records,
    )

    copied_count = sum(1 for record in records if record.kind == "original_copy")
    augmented_count = sum(
        1 for record in records if record.kind == "rotation_brightness"
    )

    print("augmentation summary")
    print(f"  input images found:      {len(image_paths)}")
    print(f"  copied originals:        {copied_count}")
    print(f"  augmented images:        {augmented_count}")
    print(f"  total output images:     {len(records)}")
    print(f"  output directory:        {output_dir}")
    print("  labels generated:        0 (manual YOLO labeling still required)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
