# --- Video Source ---
# Set to 'webcam' or 'esp32_httpx'
VIDEO_SOURCE = 'webcam' # 'webcam' or 'esp32_httpx'
WEBCAM_INDEX = 0

# --- ESP32 Communication Settings
ESP32_IP_ADDRESS = "192.168.1.9"
ESP32_CONTROL_PORT = 80
ESP32_STREAM_URL = f"http://{ESP32_IP_ADDRESS}:81/stream"
ESP32_MOVE_ENDPOINT = f"http://{ESP32_IP_ADDRESS}:{ESP32_CONTROL_PORT}/move"
HTTP_TIMEOUT_CONNECT = 2.0
HTTP_TIMEOUT_READ = 1.0

# --- Ball Detection Settings (initial seeds) ---
LOWER_BALL_COLOR = (29, 100, 100)     # HSV lower
UPPER_BALL_COLOR = (49, 255, 255)     # HSV upper
MIN_BALL_CONTOUR_AREA = 2000
YOLO_MODEL_PATH = "auto_soccer_bot/models/yolo11m.pt"
TARGET_CLASS_NAMES = ["sports ball", "apple", "orange"]
DETECTION_CONFIDENCE_THRESHOLD = 0.001

# --- Robot Control Logic ---
TARGET_ZONE_X_MIN = 0.30
TARGET_ZONE_X_MAX = 0.70
TARGET_ZONE_Y_MIN = 0.60
TARGET_ZONE_Y_MAX = 0.90

DEFAULT_ROBOT_SPEED = 100
TURN_SPEED_FACTOR = 1.0
APPROACH_SPEED_FACTOR = 0.8

MIN_SPEED = 50
MAX_SPEED = 255

# --- Command Sending ---
COMMAND_SEND_INTERVAL_MS = 200
MIN_TIME_BETWEEN_ANY_COMMAND_MS = 100

# --- State Machine & Control Logic ---
BALL_CAPTURED_AREA_THRESHOLD = 1500000
BALL_LOST_TIMEOUT_MS = 1000

SEARCH_TURN_SPEED = 100
APPROACH_SPEED = 120
APPROACH_TURN_RATIO = 0.2
DRIBBLE_SPEED = 140
DRIBBLE_TURN_RATIO = 0.5

# New state parameters
BALL_CONFIRMATION_THRESHOLD = 10           # how many consecutive detections before committing to approach
MAX_ADJUSTMENT_TIMEOUT_MS = 750            # grace period to re-acquire during adjustment
MIN_ADJUSTMENT_SPEED = max(40, MIN_SPEED)  # floor so motors still move

# --- Frame / Detection cadence ---
DETECTION_INTERVAL = 6  # YOLO cadence; color runs every frame

# --- Color enhancement (initial) ---
SATURATION = 1.5   # multiplicative on S
BRIGHTNESS = 1.2   # multiplicative on V

# --- Tuner toggle (easy to disable later) ---
COLOR_TUNER_ENABLED = True  # set False to disable the tuner entirely

# --- Color Tuner settings ---
TUNER_TARGET_CONSISTENT = 100
TUNER_POSITION_TOL_PX = 20
TUNER_WINDOW = 150
TUNER_LERP_ALPHA = 0.2
TUNER_PERCENTILES = (5, 95)
TUNER_S_GAIN_STEP = 0.05
TUNER_V_GAIN_STEP = 0.05
SAT_MIN, SAT_MAX = 0.8, 3.0
VAL_MIN, VAL_MAX = 0.6, 2.0

CORRECT_DUMP_CONSECUTIVE = 50
TUNER_DUMP_PATH = "auto_soccer_bot/calibrated_hsv.txt"

# --- Color refinement gates (relative to YOLO) ---
ROI_EXPAND_FRAC = 0.35          # expand YOLO box by this fraction on each side for color search
COLOR_AREA_MIN_RATIO = 0.35     # min color area / YOLO bbox area
COLOR_AREA_MAX_RATIO = 1.40     # max color area / YOLO bbox area
COLOR_CIRCULARITY_MIN = 0.55    # 4*pi*A / P^2; closer to 1 is more circular
COLOR_IOU_MIN = 0.15            # min IoU between color bbox and YOLO bbox

# --- HSV target margins (tighten around YOLO ROI)
H_MARGIN = 5                    # degrees of hue (0..179)
S_MARGIN = 20                   # on 0..255
V_MARGIN = 20                   # on 0..255

# Clamp color circle to YOLO box (for drawing only)
COLOR_RADIUS_CLAMP_FRAC = 0.95  # cap radius to 95% of 0.5*min(w,h) of YOLO box
COLOR_CENTER_LERP = 0.30        # pull color center 30% toward YOLO center for stability
