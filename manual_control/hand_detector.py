# manual_control/hand_detector.py
import cv2
import mediapipe as mp
from . import config
from .detection_manager_base import DetectionManager

class HandDetector(DetectionManager):
    def __init__(self,
                 static_image_mode=False,
                 max_num_hands=config.MAX_NUM_HANDS,
                 min_detection_confidence=config.MIN_DETECTION_CONFIDENCE,
                 min_tracking_confidence=config.MIN_TRACKING_CONFIDENCE):
        super().__init__() # Call parent constructor if it had one
        self.static_image_mode = static_image_mode
        self.max_num_hands = max_num_hands
        self.min_detection_confidence = min_detection_confidence
        self.min_tracking_confidence = min_tracking_confidence
        self.mp_hands = None
        self.hands_model = None # Renamed from 'hands' to avoid conflict if a variable 'hands' is used
        self.mp_drawing = None
        self.mp_drawing_styles = None

    def initialize(self):
        self.mp_hands = mp.solutions.hands
        self.hands_model = self.mp_hands.Hands(
            static_image_mode=self.static_image_mode,
            max_num_hands=self.max_num_hands,
            min_detection_confidence=self.min_detection_confidence,
            min_tracking_confidence=self.min_tracking_confidence
        )
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        print("MediaPipe Hand Detector initialized.")
        return True # Indicate success

    def process_frame(self, frame, draw=True):
        image_rgb = cv2.cvtColor(cv2.flip(frame, 1), cv2.COLOR_BGR2RGB) # Selfie view
        image_rgb.flags.writeable = False # Performance optimization
        results = self.hands_model.process(image_rgb)
        image_rgb.flags.writeable = True
        output_frame = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR) # Back to BGR

        if draw and results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                self.mp_drawing.draw_landmarks(
                    output_frame,
                    hand_landmarks,
                    self.mp_hands.HAND_CONNECTIONS,
                    self.mp_drawing_styles.get_default_hand_landmarks_style(),
                    self.mp_drawing_styles.get_default_hand_connections_style()
                )
        return output_frame, results

    def get_detection_data(self, results):
        """
        Extracts hand landmarks and handedness if available.
        :param results: The results object from MediaPipe hands.process().
        :return: A tuple (list_of_landmarks, handedness_str) or (None, None)
        """
        if results.multi_hand_landmarks:
            # For simplicity, use the first detected hand
            hand_landmarks_proto = results.multi_hand_landmarks[0]
            landmarks = hand_landmarks_proto.landmark # This is the list of landmark objects

            handedness = "Right" # Default
            if results.multi_handedness:
                handedness = results.multi_handedness[0].classification[0].label
            return landmarks, handedness
        return None, None