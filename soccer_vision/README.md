# Opponent Detector (YOLO)

Train and run a YOLO model to detect the opposing robot. This doc covers:

1. Environment setup
2. Labeling with Label Studio (local)
3. Training the model
4. Testing on images/videos/webcam


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

# Setup (for `soccer_vision/`)

> You’ll create the virtual environment **inside** `soccer_vision/`, install deps, and set up a Jupyter kernel. Pick **Method A** (normal registered kernel) or **Method B** (bulletproof server from the venv).

## 1) Create & activate the venv

**Windows (PowerShell)**

```powershell
cd soccer_vision/
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install --upgrade pip
```

**macOS / Linux**

```bash
cd soccer_vision/
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

---

## 2) Install dependencies

```bash
pip install -r requirements.txt
```

### (Optional) GPU PyTorch

Install the CUDA build that matches your system. Examples:

* **CUDA 12.1 (Windows/Linux):**

```bash
pip install --index-url https://download.pytorch.org/whl/cu121 torch torchvision torchaudio
```

* **CPU-only (no GPU):**

```bash
pip install --index-url https://download.pytorch.org/whl/cpu torch torchvision torchaudio
```

Make sure Ultralytics is recent (YOLOv11 compatible):

```bash
pip install -U "ultralytics>=8.3.220"
```

> ⚠️ **Tip:** Don’t re-install `torch`/`ultralytics` from inside notebooks. Keep installs in this terminal after activating the venv.

---

## 3) Choose ONE kernel method

### Method A — Normal (registered) kernel

Registers the `soccer_vision\.venv` as a selectable Jupyter kernel.

```bash
python -m ipykernel install --user --name=sv-soccer --display-name "Python (soccer_vision)"
```

Then open your notebook app (Jupyter/VS Code) and switch kernel to **Python (soccer_vision)**.

If needed, verify it’s registered:

```bash
jupyter kernelspec list
```

You should see an entry for `sv-soccer`.

---

### Method B — Last-resort but bulletproof (server from the venv)

Runs the **Jupyter server** with the same venv Python, so the default kernel is already correct.

```bash
# still inside <repo>/soccer_vision and with .venv activated
python -m pip install notebook ipykernel  # only if missing
python -m notebook
```

A browser tab opens. Navigate to `soccer_vision/notebooks/` and open the notebook.

> **VS Code tip:** Command Palette → *Jupyter: Select Interpreter to start Jupyter server* → pick `soccer_vision\.venv\Scripts\python.exe`.

---

## 4) Sanity-check cell (run inside the notebook)

```python
import sys, torch, ultralytics
print("Python:", sys.executable)
print("Torch:", torch.__version__,
      "| CUDA:", torch.version.cuda,
      "| cuda_available:", torch.cuda.is_available())
print("Ultralytics:", ultralytics.__version__)
```

Expected:

* `Python:` path ends with `soccer_vision\.venv\Scripts\python.exe`
* `cuda_available: True` if GPU is set up
* Ultralytics `8.3.22x` (or newer)

---

## 5) Open the retrain notebook

Open: `soccer_vision/notebooks/01_retrain_yolo.ipynb`
The downloader will place `dataset/` under **`soccer_vision/`** (even if you launch from the parent folder), and training will use **YOLOv11** when `MODEL_BACKBONE = "yolo11s.pt"` (or a local `soccer_vision/yolo11s.pt`).

---

### Common gotchas

* If the kernel doesn’t appear (Method A), re-check that the `argv[0]` in the kernel’s `kernel.json` points to:

  ```
  <repo>\soccer_vision\.venv\Scripts\python.exe
  ```
* If training runs on CPU in the notebook but GPU via CLI, you’re likely using a different interpreter/kernel. Use **Method B** or re-select the **Python (soccer_vision)** kernel.
