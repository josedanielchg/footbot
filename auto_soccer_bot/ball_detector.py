import cv2
import numpy as np
from ultralytics import YOLO
import torch
from . import config_auto as config
from .detection_manager_base import DetectionManager

class BallDetector(DetectionManager):
    def __init__(self, color_manager):
        super().__init__()
        self.cm = color_manager
        self.model = None
        self.class_names = []
        self.target_class_ids = set()
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        self.frame_count = 0
        self.yolo_interval = max(1, config.DETECTION_INTERVAL)
        self.yolo_ttl_frames = max(self.yolo_interval * 2, 3)
        self.last_yolo_detection = None
        self.last_yolo_frame_idx = -10_000

        self.last_color_detection = None
        self.last_used = "none"

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
                print(f"Error: none of {config.TARGET_CLASS_NAMES} found in model classes.")
                return False
            print(f"YOLO initialized. Target IDs: {self.target_class_ids}")
            return True
        except Exception as e:
            print(f"Error loading YOLO model from {config.YOLO_MODEL_PATH}: {e}")
            return False

    def _run_yolo(self, frame_bgr):
        best = None
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
                det = {"type": "yolo", "bbox": (x1, y1, w, h),
                       "confidence": conf, "area": max(0, w * h),
                       "class_name": self.class_names[cls]}
                if best is None or conf > best["confidence"]:
                    best = det
        return best

    def _run_color(self, frame_bgr, yolo_hint=None):
        """
        Color detection guided by YOLO ROI.
        Returns the best accepted candidate if any; otherwise returns the best visual candidate
        marked as accepted=False so UI can draw it but control logic can ignore it.
        """
        lower, upper = self.cm.get_hsv_bounds()
        H, W = frame_bgr.shape[:2]

        # ROI from YOLO (expanded) or whole frame
        if yolo_hint is not None:
            x, y, w, h = yolo_hint["bbox"]
            expand = config.ROI_EXPAND_FRAC
            rx0 = max(0, int(x - w * expand))
            ry0 = max(0, int(y - h * expand))
            rx1 = min(W, int(x + w * (1 + expand)))
            ry1 = min(H, int(y + h * (1 + expand)))
        else:
            rx0, ry0, rx1, ry1 = 0, 0, W, H

        roi = frame_bgr[ry0:ry1, rx0:rx1]
        if roi.size == 0:
            return None

        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, lower, upper)
        mask = cv2.GaussianBlur(mask, (5, 5), 0)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=1)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return None

        # Optional YOLO info
        yolo_bbox = yolo_hint["bbox"] if yolo_hint is not None else None
        yolo_area = float(yolo_bbox[2] * yolo_bbox[3]) if yolo_bbox is not None else None
        ycx = ycy = None
        if yolo_bbox is not None:
            # Build a local-ROI rectangle mask for YOLO box (convert to ROI coords)
            yx0 = max(0, int(yolo_bbox[0] - rx0))
            yy0 = max(0, int(yolo_bbox[1] - ry0))
            yx1 = min(roi.shape[1], int(yolo_bbox[0] - rx0 + yolo_bbox[2]))
            yy1 = min(roi.shape[0], int(yolo_bbox[1] - ry0 + yolo_bbox[3]))

            rect_mask = np.zeros(mask.shape, dtype=np.uint8)
            rect_mask[yy0:yy1, yx0:yx1] = 255

            # Restrict color mask to YOLO rect
            mask_in = cv2.bitwise_and(mask, rect_mask)

            # Largest inscribed circle in the mask (distance transform)
            dt = cv2.distanceTransform((mask_in > 0).astype(np.uint8), cv2.DIST_L2, 5)
            minVal, maxVal, minLoc, maxLoc = cv2.minMaxLoc(dt)
            if maxVal > 1.0:
                cx_local, cy_local = maxLoc  # (x,y) in ROI
                cx, cy = int(cx_local + rx0), int(cy_local + ry0)
                rad = int(maxVal)  # already in pixels

        # Track both: best that PASSES gates, and best ANY (for drawing)
        best_pass, best_pass_score = None, -1e9
        best_any,  best_any_score  = None, -1e9

        for c in contours:
            area = float(cv2.contourArea(c))
            if area <= config.MIN_BALL_CONTOUR_AREA:
                continue
            per = cv2.arcLength(c, True)
            if per <= 1.0:
                continue
            circularity = float(4.0 * np.pi * area / (per * per))

            x, y, w, h = cv2.boundingRect(c)
            gx, gy = x + rx0, y + ry0
            bbox_global = (gx, gy, w, h)
            (cx_f, cy_f), radius_f = cv2.minEnclosingCircle(c)
            cx, cy, rad = int(cx_f) + rx0, int(cy_f) + ry0, int(radius_f)

            # Default gates when no YOLO
            iou = 0.0
            iou_ok = True
            size_ok = True
            circ_ok = circularity >= config.COLOR_CIRCULARITY_MIN

            # If YOLO exists, use stricter gates
            if yolo_bbox is not None and yolo_area and yolo_area > 0:
                iou = self._bbox_iou(bbox_global, yolo_bbox)
                iou_ok = iou >= config.COLOR_IOU_MIN
                size_ratio = area / yolo_area
                size_ok = (config.COLOR_AREA_MIN_RATIO <= size_ratio <= config.COLOR_AREA_MAX_RATIO)

            # Scores
            if yolo_bbox is not None:
                d = 0.0
                if ycx is not None:
                    dx, dy = (cx - ycx), (cy - ycy)
                    d = (dx * dx + dy * dy) ** 0.5
                score = (0.7 * iou) + (0.25 * circularity) - (0.05 * (d / max(w, h, 1)))
            else:
                dx, dy = (cx - W // 2), (cy - H // 2)
                d = (dx * dx + dy * dy) ** 0.5
                score = (0.8 * circularity) - (0.2 * (d / max(w, h, 1)))

            candidate = {
                "type": "color",
                "bbox": bbox_global,
                "center": (cx, cy),
                "radius": rad,
                "confidence": 1.0,
                "area": area,
                "class_name": "color_ball",
                "iou": iou,
                "circularity": circularity,
                # filled below:
                # "accepted": bool
            }

            # Update best-any (for drawing)
            if score > best_any_score:
                best_any_score = score
                best_any = candidate.copy()

            # Update best-pass if gates satisfied
            passed = (iou_ok and size_ok and circ_ok)
            if (yolo_bbox is None and circ_ok) or (yolo_bbox is not None and passed):
                if score > best_pass_score:
                    best_pass_score = score
                    best_pass = candidate.copy()

        # Prefer a passing candidate; otherwise return best-any as "rejected" for drawing
        if best_pass is not None:
            best_pass["accepted"] = True
            return best_pass
        if best_any is not None:
            best_any["accepted"] = False  # draw only; not for control
            return best_any
        return None


    def process_frame(self, frame):
        if frame is None or self.model is None:
            return None
        self.frame_count += 1

        # YOLO (cadenced)
        if (self.frame_count % self.yolo_interval) == 0:
            yolo = self._run_yolo(frame)
            if yolo is not None:
                self.last_yolo_detection = yolo
                self.last_yolo_frame_idx = self.frame_count

        # Fresh YOLO?
        y_age = self.frame_count - self.last_yolo_frame_idx
        y_valid = (self.last_yolo_detection is not None) and (y_age <= self.yolo_ttl_frames)
        yolo_hint = self.last_yolo_detection if y_valid else None

        # Color (always computed for overlay; may be accepted/rejected)
        color_det = self._run_color(frame, yolo_hint=yolo_hint)
        self.last_color_detection = color_det  # keep for overlay regardless

        # Selection (YOLO priority; fall back to color only if accepted)
        if y_valid:
            self.last_used = "yolo"
            return self.last_yolo_detection

        if color_det is not None and color_det.get("accepted", True):
            self.last_used = "color"
            return color_det

        # Nothing suitable for control
        self.last_used = "none"
        return None

    def draw_detection(self, frame, det):
        if frame is None or not det:
            return frame
        t = det.get("type", "yolo")
        if t == "yolo":
            x, y, w, h = det["bbox"]
            label = f'{det.get("class_name","ball")} {det.get("confidence",0):.2f}'
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(frame, label, (x, max(0, y - 10)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        else:
            cx, cy = det.get("center", (None, None))
            r = det.get("radius", 0)
            if cx is not None:
                cv2.circle(frame, (cx, cy), max(2, r), (0, 255, 0), 2)
                cv2.circle(frame, (cx, cy), 4, (0, 0, 255), -1)
                cv2.putText(frame, "color", (cx - r, max(0, cy - r - 10)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        return frame

    def get_detection_data(self, det):
        if not det:
            return None
        if det.get("type") == "color":
            cx, cy = det["center"]
            return (int(cx), int(cy), float(det["area"]))
        x, y, w, h = det["bbox"]
        return (int(x + w // 2), int(y + h // 2), float(det["area"]))

    def get_last_components(self, allow_stale=False):
        """Return YOLO (fresh or stale), color, and which one was used."""
        yolo_det = None
        if self.last_yolo_detection is not None:
            age = self.frame_count - self.last_yolo_frame_idx
            fresh = (age <= self.yolo_ttl_frames)
            yolo_det = self.last_yolo_detection if (fresh or allow_stale) else None
        return {"yolo": yolo_det, "color": self.last_color_detection, "used": self.last_used}

    def draw_both_detections(self, frame, yolo_det=None, color_det=None, tol_px=20):
        if frame is None:
            return frame
        out = frame

        # YOLO box + center (green)
        ycx = ycy = None
        yw = yh = None
        if yolo_det:
            x, y, w, h = yolo_det["bbox"]
            ycx, ycy = x + w // 2, y + h // 2
            yw, yh = w, h
            cv2.rectangle(out, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.circle(out, (ycx, ycy), 3, (0, 255, 0), -1)
            cv2.putText(out, "YOLO", (x, max(0, y - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        # Color circle + center (magenta), clamped to YOLO if present
        if color_det:
            ccx, ccy = color_det.get("center", (None, None))
            r = int(color_det.get("radius", 6))
            bx, by, bw, bh = color_det.get("bbox", (0, 0, 0, 0))

            # If YOLO is present, limit radius and gently pull center toward YOLO center
            if ycx is not None and yw is not None:
                r_cap = int(0.5 * min(yw, yh) * getattr(config, "COLOR_RADIUS_CLAMP_FRAC", 0.95))
                r = min(r, max(2, r_cap))

                a = float(getattr(config, "COLOR_CENTER_LERP", 0.3))
                ccx = int((1.0 - a) * ccx + a * ycx)
                ccy = int((1.0 - a) * ccy + a * ycy)

            # Darker magenta if this color candidate wasn’t accepted for control
            rejected = not color_det.get("accepted", True)
            col = (180, 0, 180) if rejected else (255, 0, 255)

            cv2.circle(out, (ccx, ccy), max(2, r), col, 2)
            cv2.circle(out, (ccx, ccy), 3, col, -1)
            cv2.rectangle(out, (bx, by), (bx + bw, by + bh), col, 1)
            cv2.putText(out, "COLOR", (bx, max(0, by - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, col, 1)

        # Distance label
        if (ycx is not None) and color_det:
            dx, dy = (ccx - ycx), (ccy - ycy)
            dist = int((dx * dx + dy * dy) ** 0.5)
            near = dist <= tol_px
            cv2.putText(out, f"dist:{dist}px near:{near}", (10, 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        elif (ycx is None) and (color_det is None):
            cv2.putText(out, "YOLO: none   COLOR: none", (10, 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        elif ycx is None:
            cv2.putText(out, "YOLO: none", (10, 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        else:
            cv2.putText(out, "COLOR: none", (10, 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        return out
    
    @staticmethod
    def _bbox_iou(a, b):
        ax, ay, aw, ah = a
        bx, by, bw, bh = b
        ax2, ay2 = ax + aw, ay + ah
        bx2, by2 = bx + bw, by + bh
        inter_x1, inter_y1 = max(ax, bx), max(ay, by)
        inter_x2, inter_y2 = min(ax2, bx2), min(ay2, by2)
        iw, ih = max(0, inter_x2 - inter_x1), max(0, inter_y2 - inter_y1)
        inter = iw * ih
        if inter == 0:
            return 0.0
        union = aw * ah + bw * bh - inter
        return float(inter) / float(union + 1e-6)