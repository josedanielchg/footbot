import cv2
import time
from . import config_auto as config

class RobotController:
    # New state parameters

    def __init__(self):
        self.state = "SEARCHING_FOR_BALL"
        self.ball_last_seen_data = None
        self.ball_lost_timer = None
        self.last_known_ball_side = None

        self.default_speed = config.DEFAULT_ROBOT_SPEED
        self.turn_speed = int(self.default_speed * config.TURN_SPEED_FACTOR)
        self.approach_speed = int(self.default_speed * config.APPROACH_SPEED_FACTOR)

        # BALL_DETECTED state bookkeeping
        self.ball_detected_counter = 0                                          # consecutive detections
        self.last_search_direction = 'right'                                    # direction used while searching
        self.initial_adjustment_speed = config.SEARCH_TURN_SPEED
        self.adjustment_lost_timer = None                                       # grace period timer
        self.ball_confirmation_threshold =  config.BALL_CONFIRMATION_THRESHOLD  # how many consecutive detections before committing to approach
        self.max_adjustment_timeout_ms = config.MAX_ADJUSTMENT_TIMEOUT_MS       # grace period to re-acquire during adjustment
        self.min_adjustment_speed = config.MIN_ADJUSTMENT_SPEED                 # floor so motors still move

    def update_ball_memory(self, ball_data, frame_width):
        """Cache last sighting and side; start lost timer on first miss."""
        if ball_data:
            self.ball_last_seen_data = ball_data
            self.ball_lost_timer = None
            self.last_known_ball_side = 'left' if ball_data[0] < frame_width / 2 else 'right'
        else:
            if self.ball_lost_timer is None:
                self.ball_lost_timer = time.time() * 1000.0

    def decide_action(self, ball_data, frame_width):
        """Finite-state controller for ball pursuit."""
        self.update_ball_memory(ball_data, frame_width)

        # --- SEARCHING_FOR_BALL ---
        if self.state == "SEARCHING_FOR_BALL":
            if ball_data:
                # Enter adjustment phase to confirm stable, front-facing alignment
                self.state = "BALL_DETECTED"
                self.ball_detected_counter = 0
                self.adjustment_lost_timer = None
                print("State Change: SEARCHING_FOR_BALL -> BALL_DETECTED")
                return "stop", 0, 1.0

            # keep searching toward last known side
            if self.last_known_ball_side == 'left':
                self.last_search_direction = 'left'
                return "left", config.SEARCH_TURN_SPEED, 1.0
            else:
                self.last_search_direction = 'right'
                return "right", config.SEARCH_TURN_SPEED, 1.0

        # --- BALL_DETECTED ---
        elif self.state == "BALL_DETECTED":
            if ball_data:
                # seeing ball: increase confidence and slowly reduce adjustment magnitude
                self.adjustment_lost_timer = None
                self.ball_detected_counter += 1

                if self.ball_detected_counter >= self.ball_confirmation_threshold:
                    # commit to approach once stable enough
                    self.state = "APPROACHING_BALL"
                    print("State Change: BALL_DETECTED -> APPROACHING_BALL")
                    return "forward", self.approach_speed, 0.0

                # invert the previous search direction and decay speed linearly
                adjustment_direction = 'right' if self.last_search_direction == 'left' else 'left'
                speed_factor = 1.0 - (self.ball_detected_counter / self.ball_confirmation_threshold)
                adjustment_speed = max(self.min_adjustment_speed,
                                       int(self.initial_adjustment_speed * speed_factor))
                return adjustment_direction, adjustment_speed, 1.0

            else:
                # brief grace period to re-acquire before aborting adjustment
                now_ms = time.time() * 1000.0
                if self.adjustment_lost_timer is None:
                    self.adjustment_lost_timer = now_ms

                # dynamic timeout shrinks as confidence grows; keep a small floor
                shrink = (1.0 - (self.ball_detected_counter / self.ball_confirmation_threshold))
                timeout = max(100.0, self.max_adjustment_timeout_ms * shrink)

                if (now_ms - self.adjustment_lost_timer) > timeout:
                    # give up, resume global search
                    self.state = "SEARCHING_FOR_BALL"
                    self.ball_detected_counter = 0
                    self.adjustment_lost_timer = None
                    print("State Change: Adjustment timeout. BALL_DETECTED -> SEARCHING_FOR_BALL")
                    return "stop", 0, 1.0
                else:
                    # within grace: turn back toward the original search direction
                    return self.last_search_direction, self.initial_adjustment_speed, 1.0

        # --- APPROACHING_BALL ---
        elif self.state == "APPROACHING_BALL":
            if ball_data is None:
                # brief stop; if lost too long, revert to searching
                if self.ball_lost_timer and (time.time() * 1000.0 - self.ball_lost_timer > config.BALL_LOST_TIMEOUT_MS):
                    self.state = "SEARCHING_FOR_BALL"
                    print("State Change: Lost too long. APPROACHING_BALL -> SEARCHING_FOR_BALL")
                return "stop", 0, 1.0

            # unpack: (center_x, center_y, area)  <-- matches BallDetector
            ball_x, _, area = ball_data
            target_x_min_px = int(config.TARGET_ZONE_X_MIN * frame_width)
            target_x_max_px = int(config.TARGET_ZONE_X_MAX * frame_width)

            if area > config.BALL_CAPTURED_AREA_THRESHOLD:
                self.state = "CAPTURED_BALL"
                print("State Change: Very close. APPROACHING_BALL -> CAPTURED_BALL")
                return "forward", int(self.approach_speed * 0.5), 0.0

            if ball_x < target_x_min_px:
                return "soft_left", self.approach_speed, config.APPROACH_TURN_RATIO
            elif ball_x > target_x_max_px:
                return "soft_right", self.approach_speed, config.APPROACH_TURN_RATIO
            else:
                return "forward", self.approach_speed, 0.0

        # --- CAPTURED_BALL ---
        elif self.state == "CAPTURED_BALL":
            if self.ball_lost_timer and (time.time() * 1000.0 - self.ball_lost_timer > config.BALL_LOST_TIMEOUT_MS):
                self.state = "SEARCHING_FOR_BALL"
                print("State Change: Lost contact. CAPTURED_BALL -> SEARCHING_FOR_BALL")
                return "stop", 0, 1.0

            # placeholder: hold or pivot to simulate goal search
            print("State: CAPTURED_BALL -> pivot_right")
            return "pivot_right", config.SEARCH_TURN_SPEED, 1.0

        # Fallback safety
        return "stop", 0, 1.0

    def draw_target_zone(self, frame, frame_width, frame_height):
        """Visualize the horizontal target corridor."""
        x_min = int(config.TARGET_ZONE_X_MIN * frame_width)
        x_max = int(config.TARGET_ZONE_X_MAX * frame_width)
        cv2.line(frame, (x_min, 0), (x_min, frame_height), (255, 255, 0), 1)
        cv2.line(frame, (x_max, 0), (x_max, frame_height), (255, 255, 0), 1)

    def draw_state_info(self, frame):
        """Overlay current FSM state."""
        cv2.putText(frame, f"State: {self.state}", (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)