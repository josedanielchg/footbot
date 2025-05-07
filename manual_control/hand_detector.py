import cv2
import mediapipe as mp
from . import config

class HandDetector:
    def __init__(self,
                 static_image_mode=False,
                 max_num_hands=config.MAX_NUM_HANDS,
                 min_detection_confidence=config.MIN_DETECTION_CONFIDENCE,
                 min_tracking_confidence=config.MIN_TRACKING_CONFIDENCE):
        self.static_image_mode = static_image_mode
        self.max_num_hands = max_num_hands
        self.min_detection_confidence = min_detection_confidence
        self.min_tracking_confidence = min_tracking_confidence

        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=self.static_image_mode,
            max_num_hands=self.max_num_hands,
            min_detection_confidence=self.min_detection_confidence,
            min_tracking_confidence=self.min_tracking_confidence
        )
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles

    def find_hands(self, image, draw=True):
        """
        Processes an image to find hand landmarks.
        :param image: The input image (NumPy array).
        :param draw: Boolean, whether to draw landmarks on the image.
        :return: The image with drawn landmarks (if draw=True) and the results object.
        """
        # Flip the image horizontally for a later selfie-view display
        # and convert the BGR image to RGB.
        image_rgb = cv2.cvtColor(cv2.flip(image, 1), cv2.COLOR_BGR2RGB)

        results = self.hands.process(image_rgb)

        # Convert the image color back so it can be displayed
        output_image = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)

        if draw and results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                self.mp_drawing.draw_landmarks(
                    output_image,
                    hand_landmarks,
                    self.mp_hands.HAND_CONNECTIONS,
                    self.mp_drawing_styles.get_default_hand_landmarks_style(),
                    self.mp_drawing_styles.get_default_hand_connections_style()
                )
        return output_image, results

    def is_finger_down(self, landmarks, finger_tip_id, finger_mcp_id, handedness="Right"):
        """
        Checks if a specific finger is considered "down".
        For most fingers: tip_y > mcp_y means finger is down (assuming origin is top-left).
        For the thumb, it's more complex. For simplicity, we'll use a heuristic based on x-coordinates
        for a "thumbs down" like position relative to the index finger's base.

        :param landmarks: List of landmark objects for a single hand.
        :param finger_tip_id: MediaPipe ID for the finger tip.
        :param finger_mcp_id: MediaPipe ID for the finger's MCP joint.
        :param handedness: String, "Left" or "Right".
        :return: True if finger is down, False otherwise.
        """
        if not landmarks:
            return False

        finger_tip = landmarks[finger_tip_id]
        finger_mcp = landmarks[finger_mcp_id]

        if finger_tip_id == config.FINGER_TIPS["THUMB"]:
            # Thumb logic: "down" if tip is to the right of MCP for a Right hand (tucked in)
            # or to the left of MCP for a Left hand.
            # This is a simplification and might need refinement.
            # A more robust way is often comparing thumb tip y to index finger pip y.
            # For "all fingers down", we usually mean thumb is also curled.
            if handedness == "Right":
                return finger_tip.x > finger_mcp.x
            else: # Left hand
                return finger_tip.x < finger_mcp.x
        else:
            # Other fingers: "down" if tip_y is below mcp_y
            return finger_tip.y > finger_mcp.y

    def get_fingers_status(self, hand_landmarks_result):
        """
        Determines the up/down status of all five fingers for the first detected hand.
        :param hand_landmarks_result: The 'results.multi_hand_landmarks' object from MediaPipe.
                                      Or 'results.multi_handedness' to get hand type
        :return: A list of 5 booleans [thumb_down, index_down, middle_down, ring_down, pinky_down]
                 or None if no hand is detected.
        """
        if not hand_landmarks_result or not hand_landmarks_result.multi_hand_landmarks:
            return None

        # For simplicity, use the first detected hand
        hand_landmarks = hand_landmarks_result.multi_hand_landmarks[0].landmark
        handedness = "Right" # Default, can be improved if needed by checking results.multi_handedness

        if hand_landmarks_result.multi_handedness:
            handedness = hand_landmarks_result.multi_handedness[0].classification[0].label


        fingers_down_status = [
            self.is_finger_down(hand_landmarks, config.FINGER_TIPS["THUMB"],  config.FINGER_MCP["THUMB"], handedness),
            self.is_finger_down(hand_landmarks, config.FINGER_TIPS["INDEX"],  config.FINGER_MCP["INDEX"], handedness),
            self.is_finger_down(hand_landmarks, config.FINGER_TIPS["MIDDLE"], config.FINGER_MCP["MIDDLE"], handedness),
            self.is_finger_down(hand_landmarks, config.FINGER_TIPS["RING"],   config.FINGER_MCP["RING"], handedness),
            self.is_finger_down(hand_landmarks, config.FINGER_TIPS["PINKY"],  config.FINGER_MCP["PINKY"], handedness)
        ]
        return fingers_down_status