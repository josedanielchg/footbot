# --- ESP32 Communication Settings ---
ESP32_IP_ADDRESS = "192.168.43.2" # Make sure this is correct
ESP32_CONTROL_PORT = 80
ESP32_MOVE_ENDPOINT = f"http://{ESP32_IP_ADDRESS}:{ESP32_CONTROL_PORT}/move"
HTTP_TIMEOUT_CONNECT = 2.0 # Seconds
HTTP_TIMEOUT_READ = 1.0    # Seconds

# --- Hand Detection Settings ---
MIN_DETECTION_CONFIDENCE = 0.6 # Higher value = more strict detection, less false positives
MIN_TRACKING_CONFIDENCE = 0.6  # Higher value = more strict tracking
MAX_NUM_HANDS = 2              # Control with one hand for simplicity, can be 2

# --- Gesture Definitions ---
# These are based on the MediaPipe landmark indices
# (Refer to https://ai.google.dev/edge/mediapipe/solutions/vision/hand_landmarker)
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

# --- Robot Command Settings ---
COMMAND_SEND_INTERVAL_MS = 200  # Min interval to resend the *same* command
MIN_TIME_BETWEEN_ANY_COMMAND_MS = 100 # Min interval between *any* two commands'
DEFAULT_SPEED = 150  # Speed value from 0-255 (assuming 8-bit PWM on ESP32)
MIN_SPEED = 50
MAX_SPEED = 255
SPEED_CONTROL_MIN_DIST = 20  # Min pixel distance between thumb and index for min speed
SPEED_CONTROL_MAX_DIST = 200 # Max pixel distance for max speed (adjust these based on your camera/hand size)

# --- Camera Settings ---
WEBCAM_INDEX = 0