# auto_soccer_bot/config_auto.py

# --- Video Source ---
# Set to 'webcam' or 'esp32_httpx'
VIDEO_SOURCE = 'esp32_httpx' # 'webcam' or 'esp32_httpx'
WEBCAM_INDEX = 0

# --- ESP32 Communication Settings
ESP32_IP_ADDRESS = "192.168.1.9"
ESP32_CONTROL_PORT = 80
ESP32_STREAM_URL = f"http://{ESP32_IP_ADDRESS}:81/stream"
ESP32_MOVE_ENDPOINT = f"http://{ESP32_IP_ADDRESS}:{ESP32_CONTROL_PORT}/move"
HTTP_TIMEOUT_CONNECT = 2.0
HTTP_TIMEOUT_READ = 1.0

# --- Ball Detection Settings (Tennis Ball - Yellow/Green) ---
LOWER_BALL_COLOR = (29, 100, 100) # Lower HSV for tennis ball yellow/green
UPPER_BALL_COLOR = (49, 255, 255) # Upper HSV for tennis ball yellow/green
MIN_BALL_CONTOUR_AREA = 100       # Minimum area to consider a contour as a ball (pixels^2)
YOLO_MODEL_PATH = "auto_soccer_bot/models/yolo11m.pt" 
TARGET_CLASS_NAMES = ["sports ball", "apple", "orange"] 
DETECTION_CONFIDENCE_THRESHOLD = 0.001

# --- Robot Control Logic ---
# Defines a central target area on the screen. Values are proportions of frame width/height (0.0 to 1.0)
TARGET_ZONE_X_MIN = 0.30  # e.g., 20% from the left
TARGET_ZONE_X_MAX = 0.70  # e.g., 80% from the left
TARGET_ZONE_Y_MIN = 0.60  # Consider the lower part of the frame for "close enough"
TARGET_ZONE_Y_MAX = 0.90

DEFAULT_ROBOT_SPEED = 100
TURN_SPEED_FACTOR = 1.0 # Factor to multiply default speed for turning (can be > 1 for faster turns)
APPROACH_SPEED_FACTOR = 0.8 # Factor for moving towards the ball

MIN_SPEED = 50
MAX_SPEED = 255   

# --- Command Sending ---
COMMAND_SEND_INTERVAL_MS = 200
MIN_TIME_BETWEEN_ANY_COMMAND_MS = 100

# --- State Machine & Control Logic ---
BALL_CAPTURED_AREA_THRESHOLD = 15000
BALL_LOST_TIMEOUT_MS = 1000         # If ball is lost for 2s, go back to searching

# Speeds and turn ratios for different states
SEARCH_TURN_SPEED = 100
APPROACH_SPEED = 120
APPROACH_TURN_RATIO = 0.2  # Gentle turn ratio when approaching
DRIBBLE_SPEED = 140
DRIBBLE_TURN_RATIO = 0.5   # Wider turn ratio when dribbling

# --- Frame Processing ---
SATURATION = 3.5  # Increase saturation for better color detection
BRIGHTNESS = 1  # Increase brightness for better visibility
DETECTION_INTERVAL = 6 # Process every N-th frame for detection

# New state parameters
BALL_CONFIRMATION_THRESHOLD = 10           # how many consecutive detections before committing to approach
MAX_ADJUSTMENT_TIMEOUT_MS = 750            # grace period to re-acquire during adjustment
MIN_ADJUSTMENT_SPEED = max(40, MIN_SPEED)  # floor so motors still move