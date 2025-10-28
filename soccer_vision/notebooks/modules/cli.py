# soccer_vision/notebooks/modules/cli.py
from __future__ import annotations
import argparse
from pathlib import Path

from .paths import find_repo_root
from .logging_utils import get_logger
from .train import train_yolo

def main():
    ap = argparse.ArgumentParser(description="Train YOLO using dataset under soccer_vision/")
    ap.add_argument("--project-root", action="store_true", help="Run from repo root (auto-detected).")
    ap.add_argument("--model", default="yolo11s.pt")
    ap.add_argument("--epochs", type=int, default=60)
    ap.add_argument("--imgsz", type=int, default=640)
    ap.add_argument("--batch", type=int, default=16)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--patience", type=int, default=20)
    ap.add_argument("--train_pct", type=float, default=0.9)
    ap.add_argument("--copy_split", action="store_true")
    ap.add_argument("--no-split", action="store_true")
    ap.add_argument("--device", default=None)
    ap.add_argument("--final-name", default="soccer_yolo.pt")
    ap.add_argument("--conf", type=float, default=0.25)
    ap.add_argument("--run-name", default=None)
    ap.add_argument("--out-subdir", default=None)
    args = ap.parse_args()

    base_dir = find_repo_root() if args.project_root else find_repo_root()
    logger = get_logger()

    result = train_yolo(
        base_dir=base_dir,
        model=args.model,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device,
        workers=args.workers,
        seed=args.seed,
        patience=args.patience,
        train_pct=args.train_pct,
        copy_split=args.copy_split,
        final_name=args.final_name,
        conf_for_valprev=args.conf,
        run_name=args.run_name,
        out_subdir=args.out_subdir,
        no_split=args.no_split,
        logger=logger,
    )

    print("\n--- RESULT ---")
    print("Best Weights :", result.best_weights)
    print("Run Dir      :", result.run_dir)
    print("Artifacts    :", result.artifacts_dir)
    print("Val Predicts :", result.val_pred_dir)
    print("Device Used  :", result.device_used)

if __name__ == "__main__":
    main()
