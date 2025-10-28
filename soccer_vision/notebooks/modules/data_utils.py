from __future__ import annotations
import random, shutil, sys
from pathlib import Path
from typing import Iterable, Optional
import yaml

IMG_EXT = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}

def _emit(logger, msg: str):
    # Accept logging.Logger, or a callable (e.g. print), or None
    if hasattr(logger, "info"):
        try:
            logger.info(msg)
            return
        except Exception:
            pass
    if callable(logger):
        try:
            logger(msg)
            return
        except Exception:
            pass
    # Fallback
    print(msg)

def ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)

def has_any_files(p: Path) -> bool:
    return p.exists() and any(p.iterdir())

def paired_label_for(img_path: Path, labels_dir: Path) -> Path:
    return labels_dir / (img_path.stem + ".txt")

def read_classes(classes_file: Path) -> list[str]:
    if not classes_file.exists():
        sys.exit(f"[ERR] classes.txt not found at: {classes_file}")
    with classes_file.open("r", encoding="utf-8") as f:
        classes = [ln.strip() for ln in f if ln.strip()]
    if not classes:
        sys.exit("[ERR] classes.txt is empty.")
    return classes

def verify_dataset_or_exit(dataset_root: Path):
    t_img = dataset_root / "train" / "images"
    t_lbl = dataset_root / "train" / "labels"
    classes_file = dataset_root / "classes.txt"

    if not t_img.exists() or not t_lbl.exists():
        sys.exit(f"[ERR] Missing train folders. Expected:\n  {t_img}\n  {t_lbl}")

    imgs = [p for p in t_img.glob("*") if p.suffix.lower() in IMG_EXT]
    if not imgs:
        sys.exit(f"[ERR] No training images found in: {t_img}")

    pairs = [(im, paired_label_for(im, t_lbl)) for im in imgs]
    if not any(lb.exists() for _, lb in pairs):
        sys.exit(f"[ERR] No matching label files (*.txt) found in: {t_lbl}")

    if not classes_file.exists():
        sys.exit(f"[ERR] classes.txt missing at: {classes_file}")

def split_if_needed(dataset_root: Path, train_pct: float = 0.9, move_files: bool = True, logger=None):
    t_img = dataset_root / "train" / "images"
    t_lbl = dataset_root / "train" / "labels"
    v_img = dataset_root / "val" / "images"
    v_lbl = dataset_root / "val" / "labels"

    ensure_dir(v_img); ensure_dir(v_lbl)

    if has_any_files(v_img) and has_any_files(v_lbl):
        _emit(logger, "[INFO] Validation split already present. Skipping split.")
        return

    all_imgs = sorted([p for p in t_img.glob("*") if p.suffix.lower() in IMG_EXT])
    pairs = [(im, paired_label_for(im, t_lbl)) for im in all_imgs]
    pairs = [(im, lb) for im, lb in pairs if lb.exists()]
    if not pairs:
        sys.exit("[ERR] No image/label pairs found in train/. Check your labels.")

    import random, shutil
    random.seed(0)
    random.shuffle(pairs)
    n_train = int(len(pairs) * train_pct)
    train_pairs = pairs[:n_train]
    val_pairs   = pairs[n_train:]
    if not val_pairs:
        val_pairs = train_pairs[-1:]
        train_pairs = train_pairs[:-1]

    def mv(src: Path, dst: Path):
        ensure_dir(dst.parent)
        if move_files:
            shutil.move(str(src), str(dst))
        else:
            shutil.copy2(str(src), str(dst))

    for im, lb in val_pairs:
        mv(im, v_img / im.name)
        mv(lb, v_lbl / lb.name)

    _emit(logger, f"[SPLIT] Train pairs: {len(train_pairs)} | Val pairs: {len(val_pairs)} "
                  f"({'moved' if move_files else 'copied'})")

def write_data_yaml(dataset_root: Path, classes: Iterable[str], yaml_path: Path, logger=None):
    data = {
        "path": str(dataset_root.resolve()),
        "train": "train/images",
        "val": "val/images",
        "nc": len(list(classes)),
        "names": list(classes),
    }
    with yaml_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False)
    _emit(logger, f"[OK] Wrote {yaml_path}")