# manual_control/gesture_classifier.py
from . import config
import math

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

    def classify_gesture(self, right_hand_fingers_status):
        """
        Classifies the directional gesture based on the RIGHT hand's finger statuses.
        :param right_hand_fingers_status: List of 5 booleans for the right hand.
        :return: A command string (e.g., "forward", "stop", "left", "right", "backward") or None.
        """
        if right_hand_fingers_status is None:
            return "stop" # Default to stop if no fingers detected/valid status

        elif not right_hand_fingers_status[0] and not right_hand_fingers_status[1] and right_hand_fingers_status[2] and right_hand_fingers_status[3] and right_hand_fingers_status[4]:
            return "right"
        if not right_hand_fingers_status[0] and right_hand_fingers_status[1] and right_hand_fingers_status[2] and right_hand_fingers_status[3] and not right_hand_fingers_status[4]:
            return "left"
        if not right_hand_fingers_status[0] and  right_hand_fingers_status[1] and right_hand_fingers_status[2] and right_hand_fingers_status[3] and right_hand_fingers_status[4]:
            return "backward"
        # Gesture: All five fingers "down" (curled) means "forward"
        elif all(right_hand_fingers_status):
            return "forward"
        # Gesture: All five fingers "up" (extended) means "stop"
        elif not any(right_hand_fingers_status):
            return "stop"

        return None # No specific gesture matched, could also default to "stop"
    
    def calculate_speed_from_left_hand(self, left_hand_landmarks, frame_width, frame_height):
        """
        Calculates speed based on the distance between thumb tip and index finger tip of the LEFT hand.
        :param left_hand_landmarks: List of landmark objects for the left hand.
        :param frame_width: Width of the camera frame for normalization.
        :param frame_height: Height of the camera frame for normalization.
        :return: Speed value (e.g., 0-255) or config.DEFAULT_SPEED if no left hand or invalid.
        """
        if not left_hand_landmarks:
            return config.DEFAULT_SPEED

        try:
            thumb_tip = left_hand_landmarks[config.FINGER_TIPS["THUMB"]]
            index_tip = left_hand_landmarks[config.FINGER_TIPS["INDEX"]]

            # Get pixel coordinates (landmarks are normalized 0.0-1.0)
            thumb_x, thumb_y = int(thumb_tip.x * frame_width), int(thumb_tip.y * frame_height)
            index_x, index_y = int(index_tip.x * frame_width), int(index_tip.y * frame_height)

            # Calculate Euclidean distance in pixels
            distance = math.sqrt((thumb_x - index_x)**2 + (thumb_y - index_y)**2)
            # print(f"Left hand T-I dist: {distance:.2f}") # For debugging

            # Map distance to speed (linear interpolation)
            # Clamp distance to defined min/max
            clamped_dist = max(config.SPEED_CONTROL_MIN_DIST, min(distance, config.SPEED_CONTROL_MAX_DIST))

            # Normalize distance to 0-1 range
            normalized_dist = (clamped_dist - config.SPEED_CONTROL_MIN_DIST) / \
                              (config.SPEED_CONTROL_MAX_DIST - config.SPEED_CONTROL_MIN_DIST)

            # Map normalized distance to speed range
            speed = int(config.MIN_SPEED + normalized_dist * (config.MAX_SPEED - config.MIN_SPEED))
            
            return max(config.MIN_SPEED, min(speed, config.MAX_SPEED)) # Ensure speed is within bounds

        except IndexError: # Should not happen if landmarks are correctly passed
            print("Error: Could not access thumb/index landmarks for speed control.")
            return config.DEFAULT_SPEED
        except Exception as e:
            print(f"Error in speed calculation: {e}")
            return config.DEFAULT_SPEED
