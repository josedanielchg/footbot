import cv2
import numpy as np
from ultralytics import YOLO
import torch
from . import config_auto as config
from .detection_manager_base import DetectionManager

class BallDetector(DetectionManager):
    def __init__(self):
        super().__init__()
        # Model
        self.model = None
        self.class_names = []
        self.target_class_ids = set()
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        # YOLO scheduling / TTL
        self.frame_count = 0
        self.yolo_interval = max(1, getattr(config, "DETECTION_INTERVAL", 1))
        self.yolo_ttl_frames = max(self.yolo_interval * 2, 3)  # keep last YOLO result briefly
        self.last_yolo_detection = None
        self.last_yolo_frame_idx = -10_000

        # Color thresholds and minimal area
        self.lower_color = np.array(config.LOWER_BALL_COLOR, dtype=np.uint8)
        self.upper_color = np.array(config.UPPER_BALL_COLOR, dtype=np.uint8)
        self.min_contour_area = int(config.MIN_BALL_CONTOUR_AREA)

        # Optional HSV pre-processing
        self.sat_gain = float(getattr(config, "SATURATION", 1.0))    # multiplicative on S
        self.brightness_add = float(getattr(config, "BRIGHTNESS", 0))  # additive on V

    def initialize(self):
        print(f"Initializing YOLO model. Using device: {self.device}")
        if self.device == "cuda":
            print(f"GPU: {torch.cuda.get_device_name(0)}")
        try:
            self.model = YOLO(config.YOLO_MODEL_PATH)
            self.class_names = self.model.names
            print(f"Searching for target classes: {config.TARGET_CLASS_NAMES}")
            for i, name in self.class_names.items():
                if name in config.TARGET_CLASS_NAMES:
                    self.target_class_ids.add(i)
            if not self.target_class_ids:
                print(f"Error: none of {config.TARGET_CLASS_NAMES} are in model class list.")
                return False
            print(f"YOLO initialized. Target class IDs: {self.target_class_ids}")
            print(f"Color fallback: lower={tuple(self.lower_color)}, upper={tuple(self.upper_color)}, min_area={self.min_contour_area}")
            return True
        except Exception as e:
            print(f"Error loading YOLO model from {config.YOLO_MODEL_PATH}: {e}")
            return False

    # -----------------------------
    # Internal helpers (YOLO / Color)
    # -----------------------------
    def _run_yolo(self, frame_bgr):
        """Return best YOLO detection dict or None."""
        best = None
        # You can add imgsz=320 for speed if desired: self.model(frame_bgr, imgsz=320, ...)
        results = self.model(frame_bgr, stream=True, device=self.device, verbose=False)
        for r in results:
            for box in r.boxes:
                cls = int(box.cls[0])
                if cls not in self.target_class_ids:
                    continue
                conf = float(box.conf[0])
                if conf <= config.DETECTION_CONFIDENCE_THRESHOLD:
                    continue
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                w, h = x2 - x1, y2 - y1
                det = {
                    "type": "yolo",
                    "bbox": (x1, y1, w, h),
                    "confidence": conf,
                    "area": max(0, w * h),
                    "class_name": self.class_names[cls],
                }
                if best is None or conf > best["confidence"]:
                    best = det
        return best

    def _run_color(self, frame_bgr):
        """Return color-based detection dict or None (largest contour in HSV range)."""
        hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)

        # Optional S/V adjustment
        if self.sat_gain != 1.0 or self.brightness_add != 0.0:
            h, s, v = cv2.split(hsv)
            if self.sat_gain != 1.0:
                s = np.clip(s.astype(np.float32) * self.sat_gain, 0, 255).astype(np.uint8)
            if self.brightness_add != 0.0:
                v = np.clip(v.astype(np.float32) + self.brightness_add, 0, 255).astype(np.uint8)
            hsv = cv2.merge([h, s, v])

        mask = cv2.inRange(hsv, self.lower_color, self.upper_color)

        # Mild denoise / morphology
        mask = cv2.GaussianBlur(mask, (5, 5), 0)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=1)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return None

        c = max(contours, key=cv2.contourArea)
        area = float(cv2.contourArea(c))
        if area <= self.min_contour_area:
            return None

        (x, y), radius = cv2.minEnclosingCircle(c)
        center_x, center_y, radius = int(x), int(y), int(radius)
        # Provide a bbox too (unified interface for drawing if needed)
        bbox = (center_x - radius, center_y - radius, radius * 2, radius * 2)

        return {
            "type": "color",
            "bbox": bbox,
            "center": (center_x, center_y),
            "radius": radius,
            "confidence": 1.0,  # pseudo-score for ordering if ever needed
            "area": area,
            "class_name": "color_ball",
        }

    # -----------------------------
    # Public API used by the app
    # -----------------------------
    def process_frame(self, frame):
        """
        Run prioritized hybrid detection:
        - YOLO every N frames; cache result with short TTL.
        - Color detection every frame as fallback.
        Returns a detection dict or None (no drawing here).
        """
        if frame is None or self.model is None:
            return None

        self.frame_count += 1

        # Throttled YOLO
        new_yolo = None
        if (self.frame_count % self.yolo_interval) == 0:
            new_yolo = self._run_yolo(frame)
            if new_yolo is not None:
                self.last_yolo_detection = new_yolo
                self.last_yolo_frame_idx = self.frame_count

        # Pick valid YOLO (respect TTL to avoid stale boxes)
        yolo_age = self.frame_count - self.last_yolo_frame_idx
        yolo_valid = (self.last_yolo_detection is not None) and (yolo_age <= self.yolo_ttl_frames)

        # Fast color fallback this frame
        color_det = self._run_color(frame)

        # Priority rule: YOLO first if valid; otherwise color; otherwise None
        if yolo_valid:
            return self.last_yolo_detection
        return color_det

    def draw_detection(self, frame, detection_result):
        """Lightweight overlay for whichever detector produced the result."""
        if frame is None or not detection_result:
            return frame

        t = detection_result.get("type", "yolo")
        if t == "yolo":
            x, y, w, h = detection_result["bbox"]
            label = f'{detection_result.get("class_name","ball")} {detection_result.get("confidence",0):.2f}'
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(frame, label, (x, max(0, y - 10)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        else:
            # color
            cx, cy = detection_result.get("center", (None, None))
            radius = detection_result.get("radius", 0)
            if cx is not None:
                cv2.circle(frame, (cx, cy), max(2, radius), (0, 255, 0), 2)
                cv2.circle(frame, (cx, cy), 4, (0, 0, 255), -1)
                cv2.putText(frame, "color", (cx - radius, max(0, cy - radius - 10)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        return frame

    def get_detection_data(self, detection_result):
        """
        Return (center_x, center_y, area) for controller consumption.
        Works for both 'yolo' and 'color' detections.
        """
        if not detection_result:
            return None

        if detection_result.get("type") == "color":
            cx, cy = detection_result["center"]
            area = detection_result["area"]
            return (int(cx), int(cy), float(area))
        else:
            x, y, w, h = detection_result["bbox"]
            cx = x + w // 2
            cy = y + h // 2
            area = detection_result["area"]
            return (int(cx), int(cy), float(area))