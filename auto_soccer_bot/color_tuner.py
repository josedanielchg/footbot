import numpy as np
import cv2
from collections import deque
from pathlib import Path
from . import config_auto as config

class ColorTuner:
    """Adjusts ColorManager using YOLO as teacher; tracks 'correct' detections and dumps HSV when stable."""

    def __init__(self, color_manager):
        self.cm = color_manager

        # Rolling window of recent comparisons (near_yolo flag and centers)
        self.hist = deque(maxlen=config.TUNER_WINDOW)

        # Counters
        self.same_place_count = 0           # rolling sum of near_yolo within window
        self.consecutive_correct = 0        # consecutive frames satisfying 'correct'

        # Anchor / smoothing for HSV targets
        self.p_lo, self.p_hi = config.TUNER_PERCENTILES
        self.alpha = config.TUNER_LERP_ALPHA

        # Distance tolerance (pixels)
        self.pos_tol = config.TUNER_POSITION_TOL_PX
        self.pos_tol_sq = self.pos_tol ** 2

        # S/V gain nudges
        self.s_step = config.TUNER_S_GAIN_STEP
        self.v_step = config.TUNER_V_GAIN_STEP

        # Dump control
        self.target_same_place = config.TUNER_TARGET_CONSISTENT  # ≥100
        self.target_consec = config.CORRECT_DUMP_CONSECUTIVE     # ≥50
        self.dump_path = Path(config.TUNER_DUMP_PATH)
        self._dumped = False

    # -------- public API --------
    def update(self, frame_bgr, yolo_det, color_det):
        """
        - Update rolling 'near YOLO' metrics.
        - If YOLO present: steer HSV bounds and S/V gains softly toward YOLO ROI statistics.
        - Check 'correct' condition and maybe dump bounds to file.
        """
        # 1) Compare color vs YOLO (near_yolo)
        near_yolo = self._near_yolo(color_det, yolo_det)
        self._push_hist(near_yolo, color_det, yolo_det)

        # 2) If YOLO exists, guide HSV & gains toward robust ROI percentiles
        if yolo_det is not None:
            lo_tgt, hi_tgt, s_mean, v_mean = self._hsv_targets_from_yolo(frame_bgr, yolo_det["bbox"])
            lo_cur, hi_cur = self.cm.get_hsv_bounds()
            lo_new = self._lerp_u8(lo_cur, lo_tgt, self.alpha)
            hi_new = self._lerp_u8(hi_cur, hi_tgt, self.alpha)
            self.cm.set_hsv_bounds(lo_new, hi_new)
            self._nudge_gains(s_mean, v_mean)

        # 3) Correct detection = near_yolo AND same_place_count >= 100
        is_correct = bool(near_yolo and (self.same_place_count >= self.target_same_place))
        self.consecutive_correct = self.consecutive_correct + 1 if is_correct else 0

        # 4) Maybe dump when 50 consecutive correct detections reached
        if (not self._dumped) and (self.consecutive_correct >= self.target_consec):
            self._dump_current_bounds()

    def is_tuned(self):
        """We consider 'tuned' once same_place_count >= target (100 by default)."""
        return self.same_place_count >= self.target_same_place

    def get_status(self):
        """
        Returns a dict useful for UI/debug overlays:
        - same_place_count: rolling number of near-YOLO matches
        - consecutive_correct: consecutive frames meeting 'correct'
        - correct_needed: threshold for 'correct' dump (50)
        - same_place_needed: threshold for 'same-place' consistency (100)
        - dumped: whether file has been written
        """
        return {
            "same_place_count": int(self.same_place_count),
            "same_place_needed": int(self.target_same_place),
            "consecutive_correct": int(self.consecutive_correct),
            "correct_needed": int(self.target_consec),
            "dumped": bool(self._dumped),
        }

    # -------- internals --------
    def _near_yolo(self, color_det, yolo_det):
        """True if both detections exist and centers are within pos_tol."""
        if color_det is None or yolo_det is None:
            return False
        cx, cy = color_det["center"]
        x, y, w, h = yolo_det["bbox"]
        yx = int(x + w // 2)
        yy = int(y + h // 2)
        dx, dy = (cx - yx), (cy - yy)
        return (dx * dx + dy * dy) <= self.pos_tol_sq

    def _push_hist(self, near_yolo, color_det, yolo_det):
        """Append current comparison; recompute rolling same_place_count."""
        self.hist.append({
            "near": bool(near_yolo),
            "color_center": None if color_det is None else tuple(map(int, color_det["center"])),
            "yolo_center": None if yolo_det is None else self._bbox_center(yolo_det["bbox"]),
        })
        # Rolling sum of 'near' flags inside the window
        self.same_place_count = sum(1 for e in self.hist if e["near"])

    def _bbox_center(self, bbox):
        x, y, w, h = bbox
        return (int(x + w // 2), int(y + h // 2))

    def _hsv_targets_from_yolo(self, frame_bgr, bbox):
        x, y, w, h = bbox
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(frame_bgr.shape[1], x + w), min(frame_bgr.shape[0], y + h)
        if x1 <= x0 or y1 <= y0:
            lo, hi = self.cm.get_hsv_bounds()
            return lo, hi, 128.0, 128.0

        roi = frame_bgr[y0:y1, x0:x1]
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        H, S, V = [c.reshape(-1) for c in cv2.split(hsv)]

        p_lo, p_hi = self.p_lo, self.p_hi
        h_lo, h_hi = np.percentile(H, [p_lo, p_hi])
        s_lo, s_hi = np.percentile(S, [p_lo, p_hi])
        v_lo, v_hi = np.percentile(V, [p_lo, p_hi])

        # Apply small margins to tighten around the object
        h_lo = max(0,   h_lo - config.H_MARGIN)
        h_hi = min(179, h_hi + config.H_MARGIN)
        s_lo = max(0,   s_lo - config.S_MARGIN)
        s_hi = min(255, s_hi + config.S_MARGIN)
        v_lo = max(0,   v_lo - config.V_MARGIN)
        v_hi = min(255, v_hi + config.V_MARGIN)

        lo = np.array([h_lo, s_lo, v_lo], dtype=np.uint8)
        hi = np.array([h_hi, s_hi, v_hi], dtype=np.uint8)
        return lo, hi, float(S.mean()), float(V.mean())

    def _nudge_gains(self, s_mean, v_mean):
        s, v = self.cm.get_sv_gains()
        if s_mean < 110:
            s = min(config.SAT_MAX, s + self.s_step)
        elif s_mean > 170:
            s = max(config.SAT_MIN, s - self.s_step)
        if v_mean < 110:
            v = min(config.VAL_MAX, v + self.v_step)
        elif v_mean > 210:
            v = max(config.VAL_MIN, v - self.v_step)
        self.cm.set_sv_gains(s, v)

    def _lerp_u8(self, src, tgt, a):
        return (src.astype(np.float32) * (1.0 - a) + tgt.astype(np.float32) * a).clip(0, 255).astype(np.uint8)

    def _dump_current_bounds(self):
        """Write current LOWER/UPPER and the applied filter/gates to file once; idempotent."""
        lo, hi = self.cm.get_hsv_bounds()
        s_gain, v_gain = self.cm.get_sv_gains()

        content = (
            "# Generated by ColorTuner\n"
            "# --- Filter pipeline applied ---\n"
            f"# enhance_frame_colors: S_gain={s_gain:.2f}, V_gain={v_gain:.2f}\n"
            "# mask: HSV -> inRange(LOWER_BALL_COLOR, UPPER_BALL_COLOR)\n"
            "# post: GaussianBlur(5x5) -> MorphOpen(ellipse 5x5, it=1) -> MorphClose(ellipse 5x5, it=1)\n"
            "# selection gates (relative to YOLO):\n"
            f"#   ROI_EXPAND_FRAC={getattr(config, 'ROI_EXPAND_FRAC', 'n/a')}, "
            f"COLOR_IOU_MIN={getattr(config, 'COLOR_IOU_MIN', 'n/a')}, "
            f"COLOR_AREA_RATIO=[{getattr(config, 'COLOR_AREA_MIN_RATIO', 'n/a')}, "
            f"{getattr(config, 'COLOR_AREA_MAX_RATIO', 'n/a')}], "
            f"COLOR_CIRCULARITY_MIN={getattr(config, 'COLOR_CIRCULARITY_MIN', 'n/a')}\n"
            "# HSV target margins used while tuning:\n"
            f"#   H_MARGIN={getattr(config, 'H_MARGIN', 'n/a')}, "
            f"S_MARGIN={getattr(config, 'S_MARGIN', 'n/a')}, "
            f"V_MARGIN={getattr(config, 'V_MARGIN', 'n/a')}\n"
            "\n"
            f"LOWER_BALL_COLOR = ({int(lo[0])}, {int(lo[1])}, {int(lo[2])})\n"
            f"UPPER_BALL_COLOR = ({int(hi[0])}, {int(hi[1])}, {int(hi[2])})\n"
        )

        try:
            self.dump_path.parent.mkdir(parents=True, exist_ok=True)
            self.dump_path.write_text(content, encoding="utf-8")
            print(f"[ColorTuner] Wrote HSV bounds to: {self.dump_path}")
            print(content, end="")
            self._dumped = True
        except Exception as e:
            print(f"[ColorTuner] Failed to write {self.dump_path}: {e}")