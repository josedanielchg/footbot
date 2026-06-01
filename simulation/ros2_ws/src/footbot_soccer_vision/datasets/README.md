# Datasets

This directory documents the dataset layout for future opponent-detector
fine-tuning.

Recommended layout:

```text
raw/session_YYYYMMDD_HHMMSS/images/*.jpg
raw/session_YYYYMMDD_HHMMSS/metadata.csv
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
