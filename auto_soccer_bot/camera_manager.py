import cv2
from . import config_auto as config

class CameraManager:
    def __init__(self):
        self.source_type = config.VIDEO_SOURCE
        self.source_path = config.WEBCAM_INDEX if self.source_type == 'webcam' else config.ESP32_STREAM_URL
        self.cap = None
        self.frame_width = 0
        self.frame_height = 0

    def initialize(self):
        print(f"Initializing camera source: {self.source_type} at {self.source_path}")
        self.cap = cv2.VideoCapture(self.source_path)

        if not self.cap.isOpened():
            print(f"Error: Could not open video source: {self.source_path}")
            return False

        # Try to get frame dimensions (might not work immediately for network streams)
        self.frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        if self.frame_width == 0 or self.frame_height == 0 and self.source_type == 'esp32_stream':
            print("Warning: Could not get frame dimensions from ESP32 stream immediately. Will try on first frame.")
        
        print(f"Video source initialized. Initial dimensions: {self.frame_width}x{self.frame_height}")
        return True

    def get_frame(self):
        if self.cap and self.cap.isOpened():
            success, frame = self.cap.read()
            if success:
                # Update frame dimensions if not set yet (for network streams)
                if self.frame_width == 0 or self.frame_height == 0:
                    self.frame_height, self.frame_width, _ = frame.shape
                    print(f"Frame dimensions set: {self.frame_width}x{self.frame_height}")
                return frame
        return None

    def get_frame_dimensions(self):
        return self.frame_height, self.frame_width

    def release(self):
        if self.cap:
            self.cap.release()
            print("Video source released.")

    def is_opened(self):
        return self.cap is not None and self.cap.isOpened()