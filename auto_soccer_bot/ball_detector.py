import cv2
import numpy as np
from . import config_auto as config
from .detection_manager_base import DetectionManager

class BallDetector(DetectionManager):
    def __init__(self):
        super().__init__()
        self.lower_color = np.array(config.LOWER_BALL_COLOR)
        self.upper_color = np.array(config.UPPER_BALL_COLOR)
        self.min_contour_area = config.MIN_BALL_CONTOUR_AREA

    def initialize(self):
        print("Ball Detector (Color-based) initialized.")
        print(f"  Lower HSV: {self.lower_color}")
        print(f"  Upper HSV: {self.upper_color}")
        print(f"  Min Contour Area: {self.min_contour_area}")
        return True

    def process_frame(self, frame, draw=True):
        if frame is None:
            return None, None

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, self.lower_color, self.upper_color)
        
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        ball_data = None # Will store (center_x, center_y, radius, contour_area)

        if contours:
            # Find the largest contour by area
            largest_contour = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(largest_contour)

            if area > self.min_contour_area:
                ((x, y), radius) = cv2.minEnclosingCircle(largest_contour)
                center_x, center_y, radius = int(x), int(y), int(radius)
                
                ball_data = (center_x, center_y, radius, area)

                if draw:
                    cv2.circle(frame, (center_x, center_y), radius, (0, 255, 0), 2)
                    cv2.circle(frame, (center_x, center_y), 5, (0, 0, 255), -1)
                    cv2.putText(frame, f"Ball ({center_x},{center_y}) R:{radius}", 
                                (center_x - radius, center_y - radius - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        return frame, ball_data # Return processed frame and ball data

    def get_detection_data(self, ball_data_from_process):
        """
        Simply returns the ball data obtained from process_frame.
        :param ball_data_from_process: Tuple (center_x, center_y, radius, area) or None
        :return: Same as input.
        """
        return ball_data_from_process