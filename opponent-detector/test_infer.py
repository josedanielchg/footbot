from ultralytics import YOLO

MODEL_PATH = "opponent-detector/models/yolo11s/opponent_yolo.pt"
CONF=0.35
model = YOLO(MODEL_PATH)

# --- Single image ---
model.predict(
    source="opponent-detector/dataset/val/images/06ea8a9a-_4.jpeg",
    conf=CONF, imgsz=640, save=True, project="opponent-detector/results", name="image_test"
)

# --- Folder of images ---
model.predict(
    source="path/to/images_folder",
    conf=CONF, imgsz=640, save=True, project="opponent-detector/results", name="folder_test"
)

# --- Video file ---
model.predict(
    source="path/to/video.mp4",
    conf=CONF, imgsz=640, save=True, project="opponent-detector/results", name="video_test"
)

# --- Webcam (0) ---
# Set show=True to open a preview window
model.predict(
    source=0,
    conf=CONF, imgsz=640, show=True, project="opponent-detector/results", name="webcam_test"
)