"""Canonical ROS topic names used by the simulation."""

CMD_VEL = '/cmd_vel'
ODOM = '/odom'
ROBOT_DESCRIPTION = '/robot_description'

CAMERA_IMAGE_RAW = '/camera/image_raw'
CAMERA_INFO = '/camera/camera_info'
WEBCAM_IMAGE_RAW = '/webcam/image_raw'

GESTURE_DIRECTION = '/gesture/direction'
GESTURE_SPEED = '/gesture/speed'
GESTURE_DEBUG_IMAGE = '/gesture/debug_image'

BALL_DETECTION = '/ball_detection'
BALL_DEBUG_IMAGE = '/ball/debug_image'
SOCCER_BALL_STATE = '/soccer/ball_state'
SOCCER_FSM_STATE = '/soccer/fsm_state'

OPPONENT_DETECTIONS = '/opponent_detections'
OPPONENT_DEBUG_IMAGE = '/opponent_detection/debug_image'
GOAL_DETECTIONS = '/goal_detections'
GOAL_DEBUG_IMAGE = '/goal_detection/debug_image'

# Reach-goal: YOLO ball+goal detections and derived behavior topics.
SOCCER_DETECTIONS = '/soccer/detections'
SOCCER_DETECTIONS_DEBUG_IMAGE = '/soccer/detections/debug_image'
SOCCER_BALL_GOAL_STATE = '/soccer/ball_goal_state'
SOCCER_REACH_GOAL_FSM_STATE = '/soccer/reach_goal_fsm_state'
SOCCER_GOAL_SCORED = '/soccer/goal_scored'
REACH_GOAL_BALL_POSE = '/reach_goal/ball_pose'

SOCCER_CAMERA_IMAGE_RAW = '/soccer/camera/image_raw'
SOCCER_CAMERA_INFO = '/soccer/camera/camera_info'
