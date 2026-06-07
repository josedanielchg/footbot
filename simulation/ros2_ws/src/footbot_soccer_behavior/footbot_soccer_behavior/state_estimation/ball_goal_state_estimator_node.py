"""Reach-goal state estimator.

Converts YOLO ``vision_msgs/msg/Detection2DArray`` ball+goal detections into an
image-derived ``footbot_soccer_msgs/msg/BallGoalState``. This node never reads
Gazebo ground-truth poses; every field is computed from the camera image so the
behavior stays perception-driven.
"""

import math
import time

import rclpy
from footbot_common.frames import CAMERA_OPTICAL_FRAME
from footbot_common.geometry import BALL_RADIUS_M
from footbot_common.math_utils import clamp
from footbot_common.topics import SOCCER_BALL_GOAL_STATE, SOCCER_DETECTIONS
from footbot_soccer_msgs.msg import BallGoalState
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from vision_msgs.msg import Detection2DArray


def focal_length_px(image_width, horizontal_fov_rad):
    """Pinhole focal length in pixels for an image width and horizontal FOV."""
    return float(image_width) / (2.0 * math.tan(float(horizontal_fov_rad) / 2.0))


def horizontal_geometry(center_x, image_width, focal_px):
    """Return ``(center_error, angle_rad)`` for a bbox horizontal center.

    ``center_error`` is normalized to roughly [-1, 1] (positive = right of the
    image center) and ``angle_rad`` is the bearing in radians (positive = right
    of the optical axis). This is image geometry only, not a calibrated pose.
    """
    half_width = max(float(image_width) / 2.0, 1.0)
    pixel_offset = float(center_x) - half_width
    center_error = pixel_offset / half_width
    angle_rad = math.atan(pixel_offset / max(float(focal_px), 1.0))
    return center_error, angle_rad


def detection_score(detection):
    """Confidence of the first hypothesis of a ``Detection2D`` (0.0 if absent)."""
    if detection.results:
        return float(detection.results[0].hypothesis.score)
    return 0.0


def best_detection(detections, class_name, min_confidence):
    """Highest-confidence detection of ``class_name`` at or above the threshold."""
    best = None
    best_score = -1.0
    for detection in detections:
        if not detection.results:
            continue
        if str(detection.results[0].hypothesis.class_id).lower() != class_name:
            continue
        score = detection_score(detection)
        if score < min_confidence:
            continue
        if score > best_score:
            best_score = score
            best = detection
    return best


class BallGoalStateEstimator(Node):
    def __init__(self):
        super().__init__('ball_goal_state_estimator')

        self.declare_parameter('detections_topic', SOCCER_DETECTIONS)
        self.declare_parameter('ball_goal_state_topic', SOCCER_BALL_GOAL_STATE)
        self.declare_parameter('image_width', 640.0)
        self.declare_parameter('camera_horizontal_fov_rad', 1.047)
        self.declare_parameter('ball_radius_m', BALL_RADIUS_M)
        self.declare_parameter('lost_detection_timeout_sec', 0.5)
        self.declare_parameter('min_ball_confidence', 0.25)
        self.declare_parameter('min_goal_confidence', 0.25)
        self.declare_parameter('control_min_radius_px', 85.0)
        self.declare_parameter('control_center_tolerance', 0.20)
        self.declare_parameter('control_hold_time_sec', 0.25)
        self.declare_parameter('alignment_tolerance', 0.12)
        self.declare_parameter('goal_memory_timeout_sec', 2.5)
        self.declare_parameter('goal_memory_requires_ball_control', True)
        self.declare_parameter('publish_rate', 30.0)

        self.detections_topic = self.get_parameter('detections_topic').value
        self.ball_goal_state_topic = self.get_parameter('ball_goal_state_topic').value
        self.image_width = float(self.get_parameter('image_width').value)
        self.camera_horizontal_fov_rad = float(
            self.get_parameter('camera_horizontal_fov_rad').value
        )
        self.ball_radius_m = float(self.get_parameter('ball_radius_m').value)
        self.lost_detection_timeout_sec = float(
            self.get_parameter('lost_detection_timeout_sec').value
        )
        self.min_ball_confidence = float(
            self.get_parameter('min_ball_confidence').value
        )
        self.min_goal_confidence = float(
            self.get_parameter('min_goal_confidence').value
        )
        self.control_min_radius_px = float(
            self.get_parameter('control_min_radius_px').value
        )
        self.control_center_tolerance = float(
            self.get_parameter('control_center_tolerance').value
        )
        self.control_hold_time_sec = float(
            self.get_parameter('control_hold_time_sec').value
        )
        self.alignment_tolerance = float(
            self.get_parameter('alignment_tolerance').value
        )
        self.goal_memory_timeout_sec = float(
            self.get_parameter('goal_memory_timeout_sec').value
        )
        self.goal_memory_requires_ball_control = bool(
            self.get_parameter('goal_memory_requires_ball_control').value
        )
        publish_rate = float(self.get_parameter('publish_rate').value)

        self.focal_px = focal_length_px(
            self.image_width, self.camera_horizontal_fov_rad
        )
        self.latest_array_time = None
        self.latest_ball = None
        self.latest_ball_time = None
        self.latest_goal = None
        self.latest_goal_time = None
        self.latest_array_had_goal = False
        self.control_candidate_since = None

        self.state_publisher = self.create_publisher(
            BallGoalState, self.ball_goal_state_topic, 10
        )
        self.detections_subscription = self.create_subscription(
            Detection2DArray,
            self.detections_topic,
            self.on_detections,
            10,
        )
        self.timer = self.create_timer(
            1.0 / max(publish_rate, 1.0),
            self.publish_state,
        )
        self.get_logger().info(
            f'Estimating ball+goal state from {self.detections_topic} '
            f'to {self.ball_goal_state_topic}'
        )

    def on_detections(self, message):
        # The detector publishes a (possibly empty) array every processed frame,
        # so a fresh array means the perception pipeline is alive even when it
        # currently sees neither object.
        now = time.monotonic()
        self.latest_array_time = now

        ball = best_detection(message.detections, 'ball', self.min_ball_confidence)
        if ball is not None:
            self.latest_ball = ball
            self.latest_ball_time = now

        goal = best_detection(message.detections, 'goal', self.min_goal_confidence)
        self.latest_array_had_goal = goal is not None
        if goal is not None:
            self.latest_goal = goal
            self.latest_goal_time = now

    def build_state(self, now):
        message = BallGoalState()
        message.header.stamp = self.get_clock().now().to_msg()
        message.header.frame_id = CAMERA_OPTICAL_FRAME

        pipeline_stale = (
            self.latest_array_time is None
            or now - self.latest_array_time > self.lost_detection_timeout_sec
        )
        message.stale = bool(pipeline_stale)

        ball_fresh = (
            not pipeline_stale
            and self.latest_ball is not None
            and self.latest_ball_time is not None
            and now - self.latest_ball_time <= self.lost_detection_timeout_sec
        )
        goal_fresh = (
            not pipeline_stale
            and self.latest_array_had_goal
            and self.latest_goal is not None
            and self.latest_goal_time is not None
            and now - self.latest_goal_time <= self.lost_detection_timeout_sec
        )
        message.ball_visible = bool(ball_fresh)
        message.goal_visible = bool(goal_fresh)

        if ball_fresh:
            center_x = float(self.latest_ball.bbox.center.position.x)
            radius_px = max(float(self.latest_ball.bbox.size_x) / 2.0, 0.0)
            center_error, angle_rad = horizontal_geometry(
                center_x, self.image_width, self.focal_px
            )
            message.ball_confidence = float(
                clamp(detection_score(self.latest_ball), 0.0, 1.0)
            )
            message.ball_center_error = float(center_error)
            message.ball_angle_rad = float(angle_rad)
            message.ball_radius_px = float(radius_px)

        message.has_ball_control = self._update_has_control(message, now)
        self._apply_goal_state(message, goal_fresh, pipeline_stale, now)
        message.ball_goal_aligned = bool(
            message.ball_visible
            and (message.goal_visible or message.goal_memory_active)
            and abs(message.ball_center_error - message.goal_center_error)
            <= self.alignment_tolerance
        )
        return message

    def _apply_goal_state(self, message, goal_fresh, pipeline_stale, now):
        if goal_fresh:
            self._copy_goal_detection_to_state(message, self.latest_goal)
            return

        if pipeline_stale or self.latest_goal is None or self.latest_goal_time is None:
            self._clear_goal_memory_if_needed()
            return

        if self.goal_memory_requires_ball_control and not message.has_ball_control:
            self._clear_goal_memory_if_needed()
            return

        memory_age = now - self.latest_goal_time
        if memory_age > self.goal_memory_timeout_sec:
            self._clear_goal_memory_if_needed()
            return

        self._copy_goal_detection_to_state(message, self.latest_goal)
        message.goal_visible = False
        message.goal_memory_active = True
        message.goal_memory_age_sec = float(memory_age)

    def _copy_goal_detection_to_state(self, message, detection):
        center_x = float(detection.bbox.center.position.x)
        width_px = max(float(detection.bbox.size_x), 0.0)
        center_error, angle_rad = horizontal_geometry(
            center_x, self.image_width, self.focal_px
        )
        message.goal_confidence = float(clamp(detection_score(detection), 0.0, 1.0))
        message.goal_center_error = float(center_error)
        message.goal_angle_rad = float(angle_rad)
        message.goal_width_px = float(width_px)

    def _clear_goal_memory_if_needed(self):
        # A remembered goal is only useful while the robot still controls the
        # ball and the detector is alive. Once that premise breaks, force the
        # next goal-aware phase to rely on a fresh YOLO observation.
        self.latest_goal = None
        self.latest_goal_time = None

    def _update_has_control(self, message, now):
        # Conservative: only claim control when the ball looks close (large
        # apparent radius) and is well centered, held for a short time so a
        # single noisy frame cannot trigger it.
        control_candidate = (
            message.ball_visible
            and message.ball_radius_px >= self.control_min_radius_px
            and abs(message.ball_center_error) <= self.control_center_tolerance
        )
        if control_candidate:
            if self.control_candidate_since is None:
                self.control_candidate_since = now
        else:
            self.control_candidate_since = None
        return bool(
            self.control_candidate_since is not None
            and now - self.control_candidate_since >= self.control_hold_time_sec
        )

    def publish_state(self):
        self.state_publisher.publish(self.build_state(time.monotonic()))


def main(args=None):
    rclpy.init(args=args)
    node = None
    try:
        node = BallGoalStateEstimator()
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        if node is not None:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
