from __future__ import annotations
import os, shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .paths import base_paths, find_repo_root
from .logging_utils import get_logger, log
from .data_utils import (
    ensure_dir, has_any_files, read_classes,
    verify_dataset_or_exit, split_if_needed, write_data_yaml
)

@dataclass
class TrainResult:
    best_weights: Path
    run_dir: Path
    artifacts_dir: Path
    val_pred_dir: Optional[Path]
    device_used: str

def _select_device_str(requested: Optional[str]) -> str:
    try:
        import torch
        if requested is None:
            return "0" if torch.cuda.is_available() else "cpu"
        if requested != "cpu" and not torch.cuda.is_available():
            log.warning("[WARN] CUDA not available but device was set to '%s'. Falling back to CPU.", requested)
            return "cpu"
        return requested
    except Exception:
        return "cpu"

def resolve_model_path(model_arg: str | Path, base_dir: Path) -> str:
    p = Path(model_arg)
    if p.exists():
        return str(p.resolve())
    for cand in [
        base_dir / str(model_arg),
        base_dir / "models" / str(model_arg),
        base_dir / "models" / "backbones" / str(model_arg),
    ]:
        if cand.exists():
            return str(cand.resolve())
    return str(model_arg)  # Ultralytics may download it

def train_yolo(
    *,
    base_dir: Path | None = None,   # if None, auto-detect repo root/soccer_vision
    model: str | Path = "yolo11s.pt",
    epochs: int = 60,
    imgsz: int = 640,
    batch: int = 16,
    device: Optional[str] = None,   # "0" or "cpu"
    workers: int = 8,
    seed: int = 0,
    patience: int = 20,
    train_pct: float = 0.9,
    copy_split: bool = False,
    final_name: str = "soccer_yolo.pt",
    conf_for_valprev: float = 0.25,
    run_name: Optional[str] = None,
    out_subdir: Optional[str] = None,   # models/<out_subdir>
    no_split: bool = False,
    logger=None,
) -> TrainResult:

    lg = logger or log
    base_dir = (base_dir or find_repo_root()).resolve()
    paths = base_paths(base_dir)
    BASE, DATASET, MODELS, RUNS, DATA_YAML = paths["BASE"], paths["DATASET"], paths["MODELS"], paths["RUNS"], paths["DATA_YAML"]

    verify_dataset_or_exit(DATASET)
    ensure_dir(MODELS); ensure_dir(RUNS)

    classes = read_classes(DATASET / "classes.txt")
    if not no_split:
        split_if_needed(DATASET, train_pct=train_pct, move_files=not copy_split, logger=lg)
    else:
        lg.info("[INFO] --no-split set: leaving existing train/val as-is")

    write_data_yaml(DATASET, classes, DATA_YAML, logger=lg)

    # Keep Ultralytics downloads/caches inside repo
    os.environ.setdefault("ULTRALYTICS_HOME", str(BASE))
    lg.info("[INFO] ULTRALYTICS_HOME=%s", os.environ["ULTRALYTICS_HOME"])

    from ultralytics import YOLO  # import after ULTRALYTICS_HOME

    dev = _select_device_str(device)
    model_path = resolve_model_path(model, BASE)

    lg.info("[TRAIN] model=%s epochs=%d imgsz=%d batch=%d device=%s workers=%d seed=%d patience=%d",
            model_path, epochs, imgsz, batch, dev, workers, seed, patience)

    results = YOLO(model_path).train(
        data=str(DATA_YAML),
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        patience=patience,
        device=dev,
        workers=workers,
        seed=seed,
        project=str(RUNS),
        name=(run_name or f"{Path(model_path).stem}_train"),
        exist_ok=True,
        deterministic=True,
        plots=True,
    )

    run_dir = Path(results.save_dir)
    best = run_dir / "weights" / "best.pt"
    if not best.exists():
        raise RuntimeError(f"[ERR] best.pt not found; run folder: {run_dir}")

    out_dir = (MODELS / out_subdir) if out_subdir else (MODELS / Path(model_path).stem)
    ensure_dir(out_dir)

    dst = out_dir / final_name
    shutil.copy2(best, dst)
    lg.info("[OK] Saved best weights to %s", dst)

    art_dir = out_dir / "train_artifacts"
    if art_dir.exists():
        shutil.rmtree(art_dir)
    shutil.copytree(run_dir, art_dir)
    lg.info("[OK] Copied training artifacts to %s", art_dir)

    # Quick predictions on val images
    val_pred_dir = None
    val_imgs = DATASET / "val" / "images"
    if val_imgs.exists() and has_any_files(val_imgs):
        lg.info("[PREDICT] Running quick predictions on val images…")
        pred_run = YOLO(dst).predict(
            source=str(val_imgs),
            save=True,
            conf=conf_for_valprev,
            project=str(RUNS),
            name=f"{Path(model_path).stem}_val_predict",
            exist_ok=True
        )
        val_pred_dir = Path(pred_run[0].save_dir) if isinstance(pred_run, list) else Path(pred_run.save_dir)

    return TrainResult(
        best_weights=dst,
        run_dir=run_dir,
        artifacts_dir=art_dir,
        val_pred_dir=val_pred_dir,
        device_used=dev,
    )
