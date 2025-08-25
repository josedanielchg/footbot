import cv2
from ultralytics import YOLO
import torch
from . import config_auto as config
from .detection_manager_base import DetectionManager

class BallDetector(DetectionManager):
    def __init__(self):
        super().__init__()
        self.model = None
        self.class_names = []
        self.target_class_ids = set() 
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

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
                print(f"Error: None of the target classes {config.TARGET_CLASS_NAMES} were found in the model's class list.")
                return False
            
            print(f"YOLO Detector initialized. Target class IDs: {self.target_class_ids}")
            return True
        except Exception as e:
            print(f"Error loading YOLO model from {config.YOLO_MODEL_PATH}: {e}")
            return False

    def process_frame(self, frame, draw=True):
        if frame is None or self.model is None:
            return frame, None

        # Perform detection
        results = self.model(frame, stream=True, device=self.device, verbose=False)
        
        best_ball_detection = None

        for r in results:
            boxes = r.boxes
            for box in boxes:
                cls = int(box.cls[0])
                if cls in self.target_class_ids:
                    # Check if confidence is above our threshold
                    conf = float(box.conf[0])
                    if conf > config.DETECTION_CONFIDENCE_THRESHOLD:
                        # Get bounding box coordinates
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        w, h = x2 - x1, y2 - y1
                        area = w * h
                        
                        # Store this detection's data
                        current_detection = {
                            "bbox": (x1, y1, w, h),
                            "confidence": conf,
                            "area": area,
                            "class_name": self.class_names[cls]
                        }
                        
                        # We only care about the most confident "sports ball" detection
                        if best_ball_detection is None or conf > best_ball_detection["confidence"]:
                            best_ball_detection = current_detection

        # Drawing is done after finding the best detection
        if draw and best_ball_detection:
            x, y, w, h = best_ball_detection["bbox"]
            conf = best_ball_detection["confidence"]
            class_name = best_ball_detection["class_name"] # Get the detected class name
            label = f'{class_name} {conf:.2f}'

            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(frame, label,
                        (x, y - 10 if y > 20 else y + 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        return frame, best_ball_detection


    def get_detection_data(self, yolo_result):
        """
        Extracts ball center and area from the YOLO result.
        :param yolo_result: A dictionary containing 'bbox', 'confidence', 'area' or None.
        :return: Tuple (center_x, center_y, area) or None.
        """
        if yolo_result:
            x, y, w, h = yolo_result["bbox"]
            center_x = x + w // 2
            center_y = y + h // 2
            area = yolo_result["area"]
            
            # The 'radius' concept is less direct with a bbox, so we return area
            # which is better for estimating distance/closeness.
            return (center_x, center_y, area)
        return None