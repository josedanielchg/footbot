import math
import time

import rclpy
from footbot_common.frames import CAMERA_OPTICAL_FRAME
from footbot_common.geometry import BALL_RADIUS_M
from footbot_common.math_utils import clamp
from footbot_common.topics import BALL_DETECTION, SOCCER_BALL_STATE
from footbot_soccer_msgs.msg import BallState
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from vision_msgs.msg import Detection2D


class BallStateEstimator(Node):
    def __init__(self):
        super().__init__('ball_state_estimator')

        self.declare_parameter('detection_topic', BALL_DETECTION)
        self.declare_parameter('ball_state_topic', SOCCER_BALL_STATE)
        self.declare_parameter('image_width', 640.0)
        self.declare_parameter('camera_horizontal_fov_rad', 1.047)
        self.declare_parameter('ball_radius_m', BALL_RADIUS_M)
        self.declare_parameter('lost_detection_timeout_sec', 0.5)
        self.declare_parameter('center_tolerance', 0.12)
        self.declare_parameter('near_distance_m', 0.45)
        self.declare_parameter('contact_distance_m', 0.24)
        self.declare_parameter('control_distance_m', 0.20)
        self.declare_parameter('control_angle_tolerance_rad', 0.18)
        self.declare_parameter('control_hold_time_sec', 0.35)
        self.declare_parameter('min_confidence', 0.30)
        self.declare_parameter('publish_rate', 30.0)

        self.detection_topic = self.get_parameter('detection_topic').value
        self.ball_state_topic = self.get_parameter('ball_state_topic').value
        self.image_width = float(self.get_parameter('image_width').value)
        self.camera_horizontal_fov_rad = float(
            self.get_parameter('camera_horizontal_fov_rad').value
        )
        self.ball_radius_m = float(self.get_parameter('ball_radius_m').value)
        self.lost_detection_timeout_sec = float(
            self.get_parameter('lost_detection_timeout_sec').value
        )
        self.center_tolerance = float(self.get_parameter('center_tolerance').value)
        self.near_distance_m = float(self.get_parameter('near_distance_m').value)
        self.contact_distance_m = float(
            self.get_parameter('contact_distance_m').value
        )
        self.control_distance_m = float(
            self.get_parameter('control_distance_m').value
        )
        self.control_angle_tolerance_rad = float(
            self.get_parameter('control_angle_tolerance_rad').value
        )
        self.control_hold_time_sec = float(
            self.get_parameter('control_hold_time_sec').value
        )
        self.min_confidence = float(self.get_parameter('min_confidence').value)
        publish_rate = float(self.get_parameter('publish_rate').value)

        self.focal_px = self.image_width / (
            2.0 * math.tan(self.camera_horizontal_fov_rad / 2.0)
        )
        self.latest_detection = None
        self.latest_detection_time = None
        self.control_candidate_since = None

        self.state_publisher = self.create_publisher(BallState, self.ball_state_topic, 10)
        self.detection_subscription = self.create_subscription(
            Detection2D,
            self.detection_topic,
            self.on_detection,
            10,
        )
        self.timer = self.create_timer(
            1.0 / max(publish_rate, 1.0),
            self.publish_state,
        )
        self.get_logger().info(
            f'Estimating ball state from {self.detection_topic} to {self.ball_state_topic}'
        )

    def on_detection(self, message):
        confidence = 0.0
        if message.results:
            confidence = float(message.results[0].hypothesis.score)
        if confidence < self.min_confidence:
            return

        radius = max(float(message.bbox.size_x) / 2.0, 0.0)
        if radius <= 0.0:
            return

        self.latest_detection = message
        self.latest_detection_time = time.monotonic()

    def publish_state(self):
        now = time.monotonic()
        message = BallState()
        message.header.stamp = self.get_clock().now().to_msg()
        message.header.frame_id = CAMERA_OPTICAL_FRAME

        if self.latest_detection is None or self.latest_detection_time is None:
            message.visible = False
            message.stale = True
            self.control_candidate_since = None
            self.state_publisher.publish(message)
            return

        age = now - self.latest_detection_time
        if age > self.lost_detection_timeout_sec:
            message.visible = False
            message.stale = True
            self.control_candidate_since = None
            self.state_publisher.publish(message)
            return

        detection = self.latest_detection
        center_x = float(detection.bbox.center.position.x)
        radius = max(float(detection.bbox.size_x) / 2.0, 1.0)
        confidence = 0.0
        if detection.results:
            confidence = float(detection.results[0].hypothesis.score)

        half_width = max(self.image_width / 2.0, 1.0)
        pixel_offset = center_x - half_width
        center_error = pixel_offset / half_width
        # Approximate the ball bearing and range from image geometry. This is
        # good enough for the current simulated camera and deterministic FSM,
        # but it is not a calibrated 3D pose estimator.
        angle_rad = math.atan(pixel_offset / max(self.focal_px, 1.0))
        distance_m = self.focal_px * self.ball_radius_m / radius
        lateral_m = distance_m * math.sin(angle_rad)

        centered = abs(center_error) <= self.center_tolerance
        near = distance_m <= self.near_distance_m
        contact_ready = centered and distance_m <= self.contact_distance_m
        control_candidate = (
            abs(angle_rad) <= self.control_angle_tolerance_rad
            and distance_m <= self.control_distance_m
        )

        if control_candidate:
            if self.control_candidate_since is None:
                self.control_candidate_since = now
        else:
            self.control_candidate_since = None

        has_control = (
            self.control_candidate_since is not None
            and now - self.control_candidate_since >= self.control_hold_time_sec
        )

        message.visible = True
        message.stale = False
        message.confidence = float(clamp(confidence, 0.0, 1.0))
        message.image_center_x = center_x
        message.image_center_error = float(center_error)
        message.apparent_radius_px = float(radius)
        message.angle_rad = float(angle_rad)
        message.distance_m = float(distance_m)
        message.lateral_m = float(lateral_m)
        message.centered = bool(centered)
        message.near = bool(near)
        message.contact_ready = bool(contact_ready)
        message.has_control = bool(has_control)
        self.state_publisher.publish(message)


def main(args=None):
    rclpy.init(args=args)
    node = None
    try:
        node = BallStateEstimator()
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
