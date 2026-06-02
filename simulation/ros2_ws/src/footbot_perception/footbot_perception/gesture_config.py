"""Gesture-control constants adapted from the legacy manual control app."""

MIN_DETECTION_CONFIDENCE = 0.6
MIN_TRACKING_CONFIDENCE = 0.6
MAX_NUM_HANDS = 2

FINGER_TIPS = {
    'THUMB': 4,
    'INDEX': 8,
    'MIDDLE': 12,
    'RING': 16,
    'PINKY': 20,
}

FINGER_MCP = {
    'THUMB': 2,
    'INDEX': 5,
    'MIDDLE': 9,
    'RING': 13,
    'PINKY': 17,
}

DEFAULT_SPEED = 150
MIN_SPEED = 50
MAX_SPEED = 255
SPEED_CONTROL_MIN_DIST = 20
SPEED_CONTROL_MAX_DIST = 200
