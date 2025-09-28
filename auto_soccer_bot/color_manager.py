import numpy as np
import cv2
from . import config_auto as config

class ColorManager:
    """Stores HSV bounds and S/V gains; applies enhancement."""

    def __init__(self):
        self.lower = np.array(config.LOWER_BALL_COLOR, dtype=np.uint8)
        self.upper = np.array(config.UPPER_BALL_COLOR, dtype=np.uint8)
        self.s_gain = float(config.SATURATION)   # multiplicative on S
        self.v_gain = float(config.BRIGHTNESS)   # multiplicative on V

    # --- enhancement ---
    def enhance_frame_colors(self, bgr):
        if bgr is None:
            return None
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv)
        if self.s_gain != 1.0:
            s = np.clip(s.astype(np.float32) * self.s_gain, 0, 255).astype(np.uint8)
        if self.v_gain != 1.0:
            v = np.clip(v.astype(np.float32) * self.v_gain, 0, 255).astype(np.uint8)
        return cv2.cvtColor(cv2.merge([h, s, v]), cv2.COLOR_HSV2BGR)

    # --- getters/setters for tuner ---
    def get_hsv_bounds(self):
        return self.lower.copy(), self.upper.copy()

    def set_hsv_bounds(self, lower_u8, upper_u8):
        self.lower = lower_u8.astype(np.uint8).copy()
        self.upper = upper_u8.astype(np.uint8).copy()

    def get_sv_gains(self):
        return float(self.s_gain), float(self.v_gain)

    def set_sv_gains(self, s_gain, v_gain):
        self.s_gain = float(s_gain)
        self.v_gain = float(v_gain)
