# manual_control/camera_manager.py
import cv2
from . import config

class CameraManager:
    def __init__(self, camera_index=config.WEBCAM_INDEX):
        self.camera_index = camera_index
        self.cap = None

    def initialize(self):
        self.cap = cv2.VideoCapture(self.camera_index)
        if not self.cap.isOpened():
            print(f"Error: Could not open webcam at index {self.camera_index}.")
            return False
        print(f"Webcam {self.camera_index} initialized successfully.")
        return True

    def get_frame(self):
        if self.cap and self.cap.isOpened():
            success, frame = self.cap.read()
            if success:
                return frame
        return None

    def release(self):
        if self.cap:
            self.cap.release()
            print("Webcam released.")

    def is_opened(self):
        return self.cap is not None and self.cap.isOpened()