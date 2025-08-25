import cv2
import time
from . import config_auto as config

class RobotController:
    def __init__(self):
        self.state = "SEARCHING_FOR_BALL"
        self.ball_last_seen_data = None
        self.ball_lost_timer = None
        self.last_known_ball_side = None
        self.default_speed = config.DEFAULT_ROBOT_SPEED
        self.turn_speed = int(self.default_speed * config.TURN_SPEED_FACTOR)
        self.approach_speed = int(self.default_speed * config.APPROACH_SPEED_FACTOR)

    def update_ball_memory(self, ball_data, frame_width):
        """Updates memory of the ball's last known position."""
        if ball_data:
            self.ball_last_seen_data = ball_data
            self.ball_lost_timer = None
            # Determine which side of center the ball was on
            if ball_data[0] < frame_width / 2:
                self.last_known_ball_side = 'left'
            else:
                self.last_known_ball_side = 'right'
        else:
            if self.ball_lost_timer is None:
                self.ball_lost_timer = time.time() * 1000 # Start timer when ball is first lost

    def decide_action(self, ball_data, frame_width):
        """
        Main state machine logic to decide the robot's action.
        :param ball_data: Tuple (center_x, center_y, radius, area) or None.
        :param frame_width: Width of the video frame.
        :return: Tuple (direction_command_str, speed_int, turn_ratio_float)
        """
        self.update_ball_memory(ball_data, frame_width)

        # --- State: SEARCHING_FOR_BALL ---
        if self.state == "SEARCHING_FOR_BALL":
            if ball_data:
                self.state = "APPROACHING_BALL"
                print("State Change: SEARCHING_FOR_BALL -> APPROACHING_BALL")
                return "stop", 0, 1.0 # Stop briefly before approaching

            # If no ball, pivot turn to find it. Turn towards last known side if available.
            if self.last_known_ball_side == 'left':
                return "left", config.SEARCH_TURN_SPEED, 1.0
            else: # Default to right or last known right
                return "right", config.SEARCH_TURN_SPEED, 1.0

        # --- State: APPROACHING_BALL ---
        elif self.state == "APPROACHING_BALL":
            if ball_data is None:
                # If ball is lost, check timeout
                if self.ball_lost_timer and (time.time() * 1000 - self.ball_lost_timer > config.BALL_LOST_TIMEOUT_MS):
                    self.state = "SEARCHING_FOR_BALL"
                    print("State Change: Ball lost for too long. APPROACHING_BALL -> SEARCHING_FOR_BALL")
                return "stop", 0, 1.0

            ball_x, _, area = ball_data
            target_x_min_px = int(config.TARGET_ZONE_X_MIN * frame_width)
            target_x_max_px = int(config.TARGET_ZONE_X_MAX * frame_width)

            # Check if ball is captured (too close to see properly)
            if area > config.BALL_CAPTURED_AREA_THRESHOLD:
                self.state = "CAPTURED_BALL"
                print("State Change: Ball is very close. APPROACHING_BALL -> CAPTURED_BALL")
                return "forward", int(config.APPROACH_SPEED * 0.5), 0.0

            # Control logic for approaching
            if ball_x < target_x_min_px:
                return "soft_left", config.APPROACH_SPEED, config.APPROACH_TURN_RATIO
            elif ball_x > target_x_max_px:
                return "soft_right", config.APPROACH_SPEED, config.APPROACH_TURN_RATIO
            else: # Ball is centered, move forward
                return "forward", config.APPROACH_SPEED, 0.0

        # --- State: CAPTURED_BALL (placeholder for goal seeking) ---
        elif self.state == "CAPTURED_BALL":
            if self.ball_lost_timer and (time.time() * 1000 - self.ball_lost_timer > config.BALL_LOST_TIMEOUT_MS):
                self.state = "SEARCHING_FOR_BALL"
                print("State Change: Lost contact. CAPTURED_BALL -> SEARCHING_FOR_BALL")
                return "stop", 0, 1.0
            
            # Placeholder logic: Turn to find the goal
            # In the future, this is where you'd use a goal detector
            print("State: CAPTURED_BALL. (Simulating GOAL SEARCH by turning right)")
            return "pivot_right", config.SEARCH_TURN_SPEED, 1.0
                
        # Fallback case
        return "stop", 0, 1.0

    def draw_target_zone(self, frame, frame_width, frame_height):
        """Draws the target zone on the frame for visualization."""
        target_x_min_px = int(config.TARGET_ZONE_X_MIN * frame_width)
        target_x_max_px = int(config.TARGET_ZONE_X_MAX * frame_width)

        # Draw vertical lines for horizontal target zone
        cv2.line(frame, (target_x_min_px, 0), (target_x_min_px, frame_height), (255, 255, 0), 1)
        cv2.line(frame, (target_x_max_px, 0), (target_x_max_px, frame_height), (255, 255, 0), 1)

    def draw_state_info(self, frame):
        """Draws the current state on the frame."""
        cv2.putText(frame, f"State: {self.state}", (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)