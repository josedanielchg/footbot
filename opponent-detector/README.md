# Opponent Detector (YOLO)

Train and run a YOLO model to detect the opposing robot. This doc covers:

1. Environment setup
2. Labeling with Label Studio (local)
3. Training the model
4. Testing on images/videos/webcam

---

## 1) Install (from repo root)

> Requires Python ≥ 3.9. A virtual environment is recommended.

```bash
# From repo root (parent of opponent-detector)
python -m venv venv_opponent_detector
# Windows
.\venv_opponent_detector\Scripts\activate
# macOS/Linux
source venv_opponent_detector/bin/activate

# Install deps
pip install --upgrade pip
pip install -r opponent-detector/requirements.txt
```

> **Optional (GPU / NVIDIA):** install a CUDA build of PyTorch if desired (check your CUDA version):

```bash
# Example for CUDA 12.4 wheels:
pip install --upgrade torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
```

---

## 2) Label Studio (local)

Start Label Studio:

```bash
label-studio
```

Open [http://localhost:8080](http://localhost:8080), then:

1. **Create a project** (e.g., “Opponent Detector”).
2. **Labeling interface**: add a **Bounding Box** tool and a single class, e.g., `opponent`.
3. **Import images** (drag/drop or choose a folder).
4. **Annotate** your images.
5. **Export** → choose **YOLO (v5/v8/v11)** format. You’ll get:

   * `images/`
   * `labels/` (YOLO text annotations)
   * `classes.txt`
   * (optional) `notes.json`

Place them under:

```
opponent-detector/
  dataset/
    train/
      images/   # all labeled training images
      labels/   # YOLO *.txt files
    # (optional) val/
    classes.txt
```

> If you only have `train/` right now, the training script can make a validation split for you.

---

## 3) Train the model

Run the training script **from repo root**:

```bash
python opponent-detector/main.py --project-root --model yolo11s.pt --epochs 60 --imgsz 640
```

**Flags (common):**

* `--data-root` : root that contains `train/` (and optional `validation/`) + `classes.txt`
* `--model`     : YOLO base (e.g., `yolo11n.pt`, `yolo11s.pt`, `yolo11m.pt`…)
* `--epochs`    : recommended 40–80 depending on dataset size
* `--imgsz`     : 640 is standard; smaller is faster, larger may improve accuracy
* `--val-split` : if no `validation/` exists, auto-split this fraction from `train/`
* `--device`    : `0` for first GPU, or `cpu`

**Outputs:**

* Best weights at
  `opponent-detector/models/<base_model_name>/opponent_yolo.pt`
  e.g. `opponent-detector/models/yolo11s/opponent_yolo.pt`
* Ultralytics training artifacts under `runs/detect/train*` (loss curves, mAP, etc.)

---

## 4) Test / Inference

Run **from repo root**:

```bash
python opponent-detector/test_infer.py \
  --model opponent-detector/models/yolo11s/opponent_yolo.pt \
  --source path/to/image_or_folder_or_video_or_camIndex \
  --conf 0.35 \
  --imgsz 640 \
  --save
```

**Examples:**

```bash
# Single image
python opponent-detector/test_infer.py --model opponent-detector/models/yolo11s/opponent_yolo.pt --source samples/img.jpg --save

# Folder
python opponent-detector/test_infer.py --model opponent-detector/models/yolo11s/opponent_yolo.pt --source samples/ --save

# Video
python opponent-detector/test_infer.py --model opponent-detector/models/yolo11s/opponent_yolo.pt --source samples/video.mp4 --save

# Webcam
python opponent-detector/test_infer.py --model opponent-detector/models/yolo11s/opponent_yolo.pt --source 0 --show
```

Outputs are saved under `opponent-detector/results/<name>`.