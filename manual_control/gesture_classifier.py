# manual_control/gesture_classifier.py
from . import config

class GestureClassifier:
    def __init__(self):
        pass

    def _is_finger_down(self, landmarks, finger_tip_id, finger_mcp_id, handedness="Right"):
        """Internal helper to check individual finger state."""
        if not landmarks:
            return False

        finger_tip = landmarks[finger_tip_id]
        finger_mcp = landmarks[finger_mcp_id]

        # Thumb logic (same as before, adjust if needed)
        if finger_tip_id == config.FINGER_TIPS["THUMB"]:
            if handedness == "Right":
                return finger_tip.x > finger_mcp.x # Thumb tucked for right hand
            else: # Left hand
                return finger_tip.x < finger_mcp.x # Thumb tucked for left hand
        else:
            # Other fingers: "down" if tip_y is below (greater Y) mcp_y
            return finger_tip.y > finger_mcp.y

    def get_fingers_status(self, landmarks, handedness):
        """
        Determines the up/down status of all five fingers.
        :param landmarks: List of landmark objects for a single hand.
        :param handedness: String "Left" or "Right".
        :return: A list of 5 booleans [thumb_down, index_down, ...] or None if no landmarks.
        """
        if not landmarks:
            return None

        status = [
            self._is_finger_down(landmarks, config.FINGER_TIPS["THUMB"],  config.FINGER_MCP["THUMB"], handedness),
            self._is_finger_down(landmarks, config.FINGER_TIPS["INDEX"],  config.FINGER_MCP["INDEX"], handedness),
            self._is_finger_down(landmarks, config.FINGER_TIPS["MIDDLE"], config.FINGER_MCP["MIDDLE"], handedness),
            self._is_finger_down(landmarks, config.FINGER_TIPS["RING"],   config.FINGER_MCP["RING"], handedness),
            self._is_finger_down(landmarks, config.FINGER_TIPS["PINKY"],  config.FINGER_MCP["PINKY"], handedness)
        ]
        return status

    def classify_gesture(self, fingers_status):
        """
        Classifies the overall gesture based on finger statuses.
        :param fingers_status: List of 5 booleans [thumb_down, index_down, ...]
        :return: A command string (e.g., "forward", "stop") or None.
        """
        if fingers_status is None:
            return "stop" # Default to stop if no fingers detected/valid status

        elif not fingers_status[0] and fingers_status[1] and fingers_status[2] and fingers_status[3] and not fingers_status[4]:
            return "left"
        if not fingers_status[0] and not fingers_status[1] and fingers_status[2] and fingers_status[3] and fingers_status[4]:
            return "right"
        # Gesture: All five fingers "down" (curled) means "forward"
        elif all(fingers_status):
            return "forward"
        # Gesture: All five fingers "up" (extended) means "stop"
        elif not any(fingers_status):
            return "stop"

        return None # No specific gesture matched, could also default to "stop"