# --- ESP32 Communication Settings ---
ESP32_IP_ADDRESS = "192.168.43.2"
ESP32_CONTROL_PORT = 80
ESP32_MOVE_ENDPOINT = f"http://{ESP32_IP_ADDRESS}:{ESP32_CONTROL_PORT}/move"

# --- Hand Detection Settings ---
MIN_DETECTION_CONFIDENCE = 0.6 # Higher value = more strict detection, less false positives
MIN_TRACKING_CONFIDENCE = 0.6  # Higher value = more strict tracking
MAX_NUM_HANDS = 1              # Control with one hand for simplicity, can be 2

# --- Gesture Definitions ---
# These are based on the MediaPipe landmark indices
# (Refer to https://ai.google.dev/edge/mediapipe/solutions/vision/hand_landmarker?hl=es-419)
FINGER_TIPS = {
    "THUMB": 4,
    "INDEX": 8,
    "MIDDLE": 12,
    "RING": 16,
    "PINKY": 20
}

# Using MCP (Metacarpophalangeal) joints as the base for finger up/down detection
FINGER_MCP = {
    "THUMB": 2,     # Thumb MCP
    "INDEX": 5,     # Index finger MCP
    "MIDDLE": 9,    # Middle finger MCP
    "RING": 13,     # Ring finger MCP
    "PINKY": 17     # Pinky MCP
}