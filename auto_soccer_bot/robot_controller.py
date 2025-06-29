import cv2
from . import config_auto as config

class RobotController:
    def __init__(self):
        self.default_speed = config.DEFAULT_ROBOT_SPEED
        self.turn_speed = int(self.default_speed * config.TURN_SPEED_FACTOR)
        self.approach_speed = int(self.default_speed * config.APPROACH_SPEED_FACTOR)

    def decide_action(self, ball_data, frame_width, frame_height):
        """
        Decides the robot's command based on ball position.
        :param ball_data: Tuple (center_x, center_y, radius, area) or None.
        :param frame_width: Width of the video frame.
        :param frame_height: Height of the video frame.
        :return: Tuple (direction_command_str, speed_int)
        """
        if ball_data is None:
            return "stop", 0 # Stop if no ball is detected

        ball_x, ball_y, radius, area = ball_data

        # Define target zone in pixel coordinates
        target_x_min_px = int(config.TARGET_ZONE_X_MIN * frame_width)
        target_x_max_px = int(config.TARGET_ZONE_X_MAX * frame_width)
        target_y_min_px = int(config.TARGET_ZONE_Y_MIN * frame_height) # Not used yet but good for future
        target_y_max_px = int(config.TARGET_ZONE_Y_MAX * frame_height) # Not used yet

        command = "stop"
        current_speed = 0

        if ball_x < target_x_min_px:
            command = "right"
            current_speed = self.turn_speed
        elif ball_x > target_x_max_px:
            command = "left"
            current_speed = self.turn_speed
        else: # Ball is horizontally centered (or close enough)
            # For now, if centered, move forward to approach
            # Later, you'll use ball size/distance to decide if to stop or kick
            command = "forward"
            current_speed = self.approach_speed
            
            # Example for future: if ball is large enough (close), then stop or kick
            # if radius > some_threshold_for_closeness:
            #     command = "stop" # or "kick"
            #     current_speed = 0


        # Ensure speed is within bounds
        current_speed = max(0, min(current_speed, config.MAX_SPEED))

        return command, current_speed

    def draw_target_zone(self, frame, frame_width, frame_height):
        """Draws the target zone on the frame for visualization."""
        target_x_min_px = int(config.TARGET_ZONE_X_MIN * frame_width)
        target_x_max_px = int(config.TARGET_ZONE_X_MAX * frame_width)
        target_y_min_px = int(config.TARGET_ZONE_Y_MIN * frame_height)
        target_y_max_px = int(config.TARGET_ZONE_Y_MAX * frame_height)

        # Draw vertical lines for horizontal target zone
        cv2.line(frame, (target_x_min_px, 0), (target_x_min_px, frame_height), (255, 255, 0), 1)
        cv2.line(frame, (target_x_max_px, 0), (target_x_max_px, frame_height), (255, 255, 0), 1)
        # Draw horizontal lines for y-zone (optional visualization)
        # cv2.line(frame, (0, target_y_min_px), (frame_width, target_y_min_px), (255, 100, 0), 1)
        # cv2.line(frame, (0, target_y_max_px), (frame_width, target_y_max_px), (255, 100, 0), 1)