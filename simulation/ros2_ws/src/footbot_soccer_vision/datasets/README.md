# Datasets

This directory documents the dataset layout for future opponent-detector
fine-tuning.

Recommended layout:

```text
raw/session_YYYYMMDD_HHMMSS/images/*.jpg
raw/session_YYYYMMDD_HHMMSS/metadata.csv
raw/soccer_v1/images/*.jpg
raw/soccer_v1/augmented_images/*.jpg
raw/soccer_v1/augmented_images/augmentation_metadata.json
labels/session_name/*.txt
splits/data.yaml
```

Label files should use YOLO text format:

```text
class_id x_center y_center width height
```

Bounding-box values are normalized from `0.0` to `1.0`.

Generated images and labels are ignored by Git by default. Keep only small
documentation and configuration files in the repository unless Git LFS is added
later.

## Unlabeled Augmentation Workflow

Use `augment_dataset.py` when you have a small unlabeled simulation dataset and
want a manageable number of images before manual YOLO labeling. The script does
not transform or generate label files.

Recommended folder structure for this workflow:

```text
datasets/
  augment_dataset.py
  raw/soccer_v1/
    images/
      img001.jpg
      img002.jpg
    augmented_images/
      img001_original.jpg
      img001_rot090_brightness085.jpg
      img001_rot180_brightness085.jpg
      img001_rot270_brightness085.jpg
      augmentation_metadata.json
```

For the current 40-image soccer dataset, this command creates exactly three
augmented images per original image. With `--copy-originals`, the output folder
contains 40 copied originals plus 120 augmented images, for 160 images total:

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

Useful arguments:

```text
--rotation-angles 90 180 270
--brightness-factor 0.85
--copy-originals
--clean-output
```

The script intentionally avoids aggressive augmentation. It does not create
mosaics, random crops, cutouts, blur, noise, perspective warps, or dramatic
lighting changes. That keeps the dataset closer to the simulated camera domain
and keeps manual labeling work bounded.

After augmentation, all generated images still need to be manually labeled for
YOLO. The metadata file only records how each image was produced; it is not a
label file.
