import argparse
import random
import shutil
from pathlib import Path
import yaml
import sys
import os

IMG_EXT = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}

# ---------- helpers ----------
def ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)

def has_any_files(p: Path):
    return p.exists() and any(p.iterdir())

def paired_label_for(img_path: Path, labels_dir: Path):
    return labels_dir / (img_path.stem + ".txt")

def read_classes(classes_file: Path):
    if not classes_file.exists():
        sys.exit(f"[ERR] classes.txt not found at: {classes_file}")
    with classes_file.open("r", encoding="utf-8") as f:
        classes = [ln.strip() for ln in f if ln.strip()]
    if not classes:
        sys.exit("[ERR] classes.txt is empty.")
    return classes

def verify_dataset_or_exit(dataset_root: Path):
    """Validate fixed structure under opponent-detector/dataset/"""
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

def split_if_needed(dataset_root: Path, train_pct: float = 0.9, move_files: bool = True):
    """Create val split only if val/ is empty; keeps image/label pairs aligned."""
    t_img = dataset_root / "train" / "images"
    t_lbl = dataset_root / "train" / "labels"
    v_img = dataset_root / "val" / "images"
    v_lbl = dataset_root / "val" / "labels"

    for p in [v_img, v_lbl]:
        ensure_dir(p)

    if has_any_files(v_img) and has_any_files(v_lbl):
        print("[INFO] Validation split already present. Skipping split.")
        return

    all_imgs = sorted([p for p in t_img.glob("*") if p.suffix.lower() in IMG_EXT])
    pairs = [(im, paired_label_for(im, t_lbl)) for im in all_imgs]
    pairs = [(im, lb) for im, lb in pairs if lb.exists()]
    if not pairs:
        sys.exit("[ERR] No image/label pairs found in train/. Check your labels.")

    random.seed(0)
    random.shuffle(pairs)
    n_train = int(len(pairs) * train_pct)
    train_pairs = pairs[:n_train]
    val_pairs = pairs[n_train:]
    if not val_pairs:
        val_pairs = train_pairs[-1:]
        train_pairs = train_pairs[:-1]

    def mv(src: Path, dst: Path):
        if move_files:
            ensure_dir(dst.parent)
            shutil.move(str(src), str(dst))
        else:
            ensure_dir(dst.parent)
            shutil.copy2(str(src), str(dst))

    for im, lb in val_pairs:
        mv(im, v_img / im.name)
        mv(lb, v_lbl / lb.name)

    print(f"[SPLIT] Train pairs: {len(train_pairs)} | Val pairs: {len(val_pairs)} "
          f"({'moved' if move_files else 'copied'})")

def write_data_yaml(dataset_root: Path, classes, yaml_path: Path):
    data = {
        "path": str(dataset_root.resolve()),
        "train": "train/images",
        "val": "val/images",
        "nc": len(classes),
        "names": classes,
    }
    with yaml_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False)
    print(f"[OK] Wrote {yaml_path}")

def resolve_base_dir(project_root_flag: bool) -> Path:
    """
    If --project-root is passed, treat CWD/‘opponent-detector’ as base.
    Otherwise use the script directory (works even if run from elsewhere).
    """
    if project_root_flag:
        base = (Path.cwd() / "opponent-detector").resolve()
        if not base.exists():
            sys.exit(f"[ERR] --project-root set but folder not found: {base}")
        return base
    return Path(__file__).resolve().parent

def resolve_model_path(model_arg: str, base_dir: Path) -> str:
    """
    If the user provided just 'yolo11s.pt' and it exists locally under
    opponent-detector/, prefer that to avoid re-downloading.
    Search order:
      1) as given (absolute/relative) if exists
      2) base_dir / <name>
      3) base_dir / models / <name>
      4) base_dir / models / backbones / <name>
    Otherwise, return the raw string (Ultralytics may download it).
    """
    cand = Path(model_arg)
    if cand.exists():
        return str(cand.resolve())
    for p in [
        base_dir / model_arg,
        base_dir / "models" / model_arg,
        base_dir / "models" / "backbones" / model_arg,
    ]:
        if p.exists():
            return str(p.resolve())
    return model_arg  # let Ultralytics handle (may download)

# ---------- main ----------
def main():
    ap = argparse.ArgumentParser(description="Train opponent YOLO model (fixed dataset layout).")
    ap.add_argument("--project-root", action="store_true",
                    help="Treat CWD/opponent-detector as base_dir (run from repo root).")
    ap.add_argument("--model", default="yolo11s.pt", help="Base model or local path (e.g., yolo11n.pt)")
    ap.add_argument("--epochs", type=int, default=60)
    ap.add_argument("--imgsz", type=int, default=640)
    ap.add_argument("--batch", type=int, default=16)
    ap.add_argument("--train_pct", type=float, default=0.9, help="Train split if val/ is empty")
    ap.add_argument("--copy_split", action="store_true", help="Copy instead of move when creating val/")
    ap.add_argument("--device", default=None, help="e.g. '0' for GPU, or 'cpu'")
    args = ap.parse_args()

    base_dir = resolve_base_dir(args.project_root)
    dataset_root = base_dir / "dataset"
    classes_file = dataset_root / "classes.txt"
    models_dir = base_dir / "models"
    data_yaml = base_dir / "data.yaml"
    runs_root = base_dir / "runs"

    verify_dataset_or_exit(dataset_root)
    ensure_dir(models_dir)
    ensure_dir(runs_root)

    classes = read_classes(classes_file)
    split_if_needed(dataset_root, train_pct=args.train_pct, move_files=not args.copy_split)
    write_data_yaml(dataset_root, classes, data_yaml)

    # >>> Force all Ultralytics caches/downloads under opponent-detector/
    os.environ.setdefault("ULTRALYTICS_HOME", str(base_dir))
    print(f"[INFO] ULTRALYTICS_HOME={os.environ['ULTRALYTICS_HOME']}")

    try:
        from ultralytics import YOLO
        import torch
    except Exception as e:
        sys.exit(f"[ERR] Ultralytics/Torch not available: {e}\nInstall with: pip install ultralytics")

    device = args.device if args.device is not None else (0 if torch.cuda.is_available() else "cpu")
    model_path = resolve_model_path(args.model, base_dir)

    print(f"[TRAIN] model={model_path} epochs={args.epochs} imgsz={args.imgsz} batch={args.batch} device={device}")

    # >>> Temporarily chdir into opponent-detector/ so any implicit downloads land here
    prev_cwd = Path.cwd()
    os.chdir(base_dir)
    try:
        model = YOLO(model_path)
        results = model.train(
            data=str(data_yaml),
            epochs=args.epochs,
            imgsz=args.imgsz,
            batch=args.batch,
            patience=20,
            device=device,
            project=str(runs_root),                  # runs stay inside opponent-detector/
            name=f"{Path(model_path).stem}_train",
            exist_ok=True,
        )
    finally:
        os.chdir(prev_cwd)

    run_dir = Path(results.save_dir)
    best = run_dir / "weights" / "best.pt"
    out_dir = models_dir / Path(model_path).stem
    ensure_dir(out_dir)
    if best.exists():
        dst = out_dir / "opponent_yolo.pt"
        shutil.copy2(best, dst)
        print(f"[OK] Saved best weights to {dst}")
        art_dir = out_dir / "train_artifacts"
        if art_dir.exists():
            shutil.rmtree(art_dir)
        shutil.copytree(run_dir, art_dir)
        print(f"[OK] Copied training artifacts to {art_dir}")
    else:
        print("[WARN] best.pt not found; check the run folder:", run_dir)

    val_imgs = dataset_root / "val" / "images"
    if val_imgs.exists() and has_any_files(val_imgs):
        print("[PREDICT] Running quick predictions on val images…")
        # >>> ensure predictions also write under opponent-detector/runs
        prev_cwd = Path.cwd()
        os.chdir(base_dir)
        try:
            model.predict(
                source=str(val_imgs),
                save=True,
                conf=0.25,
                project=str(runs_root),
                name=f"{Path(model_path).stem}_val_predict",
                exist_ok=True
            )
        finally:
            os.chdir(prev_cwd)

if __name__ == "__main__":
    main()