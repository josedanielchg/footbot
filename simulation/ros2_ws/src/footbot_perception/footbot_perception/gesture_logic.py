"""Gesture classification helpers adapted from the legacy manual control app."""

import math

from footbot_perception import gesture_config as config


class GestureLogic:
    """Classify hand landmarks into movement directions and speed values."""

    def is_finger_down(self, landmarks, finger_tip_id, finger_mcp_id, handedness):
        """Return true when a single finger appears curled/down."""
        if not landmarks:
            return False

        finger_tip = landmarks[finger_tip_id]
        finger_mcp = landmarks[finger_mcp_id]

        if finger_tip_id == config.FINGER_TIPS['THUMB']:
            if handedness == 'Right':
                return finger_tip.x > finger_mcp.x
            return finger_tip.x < finger_mcp.x

        return finger_tip.y > finger_mcp.y

    def get_fingers_status(self, landmarks, handedness):
        """Return down/up status for thumb, index, middle, ring, and pinky."""
        if not landmarks:
            return None

        return [
            self.is_finger_down(
                landmarks,
                config.FINGER_TIPS['THUMB'],
                config.FINGER_MCP['THUMB'],
                handedness,
            ),
            self.is_finger_down(
                landmarks,
                config.FINGER_TIPS['INDEX'],
                config.FINGER_MCP['INDEX'],
                handedness,
            ),
            self.is_finger_down(
                landmarks,
                config.FINGER_TIPS['MIDDLE'],
                config.FINGER_MCP['MIDDLE'],
                handedness,
            ),
            self.is_finger_down(
                landmarks,
                config.FINGER_TIPS['RING'],
                config.FINGER_MCP['RING'],
                handedness,
            ),
            self.is_finger_down(
                landmarks,
                config.FINGER_TIPS['PINKY'],
                config.FINGER_MCP['PINKY'],
                handedness,
            ),
        ]

    def classify_gesture(self, right_hand_fingers_status):
        """Convert right-hand finger status into a movement direction."""
        if right_hand_fingers_status is None:
            return 'stop'

        thumb, index, middle, ring, pinky = right_hand_fingers_status

        if not thumb and not index and middle and ring and pinky:
            return 'left'
        if not thumb and index and middle and ring and not pinky:
            return 'right'
        if not thumb and index and middle and ring and pinky:
            return 'backward'
        if all(right_hand_fingers_status):
            return 'forward'
        if not any(right_hand_fingers_status):
            return 'stop'

        return None

    def calculate_speed_from_left_hand(self, landmarks, frame_width, frame_height):
        """Return an ESP32-style speed value from left thumb/index distance."""
        if not landmarks:
            return config.DEFAULT_SPEED

        try:
            thumb_tip = landmarks[config.FINGER_TIPS['THUMB']]
            index_tip = landmarks[config.FINGER_TIPS['INDEX']]

            thumb_x = int(thumb_tip.x * frame_width)
            thumb_y = int(thumb_tip.y * frame_height)
            index_x = int(index_tip.x * frame_width)
            index_y = int(index_tip.y * frame_height)
            distance = math.sqrt(
                (thumb_x - index_x) ** 2 + (thumb_y - index_y) ** 2
            )

            clamped_dist = max(
                config.SPEED_CONTROL_MIN_DIST,
                min(distance, config.SPEED_CONTROL_MAX_DIST),
            )
            normalized_dist = (
                (clamped_dist - config.SPEED_CONTROL_MIN_DIST) /
                (config.SPEED_CONTROL_MAX_DIST - config.SPEED_CONTROL_MIN_DIST)
            )
            speed = int(
                config.MIN_SPEED +
                normalized_dist * (config.MAX_SPEED - config.MIN_SPEED)
            )
            return max(config.MIN_SPEED, min(speed, config.MAX_SPEED))
        except (IndexError, AttributeError, TypeError):
            return config.DEFAULT_SPEED


def normalize_speed(speed):
    """Convert an ESP32-style speed value to the normalized 0.0-1.0 range."""
    clamped_speed = max(0, min(int(speed), config.MAX_SPEED))
    return clamped_speed / float(config.MAX_SPEED)
