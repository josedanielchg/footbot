"""Follow a detected ball using proportional visual servoing."""

import time

import rclpy
from geometry_msgs.msg import Twist
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from vision_msgs.msg import Detection2D


def clamp(value, minimum, maximum):
    """Clamp a numeric value into an inclusive range."""
    return max(minimum, min(maximum, value))


class BallFollower(Node):
    """Convert ball detections into safe differential-drive velocity commands."""

    def __init__(self):
        super().__init__('ball_follower')
        self.declare_parameter('detection_topic', '/ball_detection')
        self.declare_parameter('cmd_vel_topic', '/cmd_vel')
        self.declare_parameter('image_width', 640.0)
        self.declare_parameter('max_linear_velocity', 0.16)
        self.declare_parameter('max_angular_velocity', 1.0)
        self.declare_parameter('angular_kp', 0.9)
        self.declare_parameter('linear_kp', 0.18)
        self.declare_parameter('center_tolerance', 0.14)
        self.declare_parameter('target_radius_px', 150.0)
        self.declare_parameter('slowdown_radius_px', 100.0)
        self.declare_parameter('lost_detection_timeout_sec', 0.6)
        self.declare_parameter('publish_rate', 20.0)
        self.declare_parameter('search_when_lost', False)
        self.declare_parameter('search_angular_velocity', 0.25)

        self.detection_topic = self.get_parameter('detection_topic').value
        self.cmd_vel_topic = self.get_parameter('cmd_vel_topic').value
        self.image_width = float(self.get_parameter('image_width').value)
        self.max_linear_velocity = float(
            self.get_parameter('max_linear_velocity').value
        )
        self.max_angular_velocity = float(
            self.get_parameter('max_angular_velocity').value
        )
        self.angular_kp = float(self.get_parameter('angular_kp').value)
        self.linear_kp = float(self.get_parameter('linear_kp').value)
        self.center_tolerance = float(
            self.get_parameter('center_tolerance').value
        )
        self.target_radius_px = float(
            self.get_parameter('target_radius_px').value
        )
        self.slowdown_radius_px = float(
            self.get_parameter('slowdown_radius_px').value
        )
        self.lost_detection_timeout_sec = float(
            self.get_parameter('lost_detection_timeout_sec').value
        )
        self.publish_rate = float(self.get_parameter('publish_rate').value)
        self.search_when_lost = bool(
            self.get_parameter('search_when_lost').value
        )
        self.search_angular_velocity = float(
            self.get_parameter('search_angular_velocity').value
        )

        self.last_center_x = None
        self.last_radius = None
        self.last_detection_time = None

        self.cmd_vel_publisher = self.create_publisher(
            Twist,
            self.cmd_vel_topic,
            10,
        )
        self.subscription = self.create_subscription(
            Detection2D,
            self.detection_topic,
            self.on_detection,
            10,
        )
        self.timer = self.create_timer(
            1.0 / max(self.publish_rate, 1.0),
            self.publish_command,
        )
        self.get_logger().info(
            'Following ball detections from %s and publishing %s' %
            (self.detection_topic, self.cmd_vel_topic)
        )

    def on_detection(self, message):
        """Store the latest ball detection."""
        self.last_center_x = float(message.bbox.center.position.x)
        self.last_radius = float(message.bbox.size_x) / 2.0
        self.last_detection_time = time.monotonic()

    def publish_command(self):
        """Publish the current ball-following command."""
        self.cmd_vel_publisher.publish(self.detection_to_twist())

    def detection_to_twist(self):
        """Convert the latest detection into a Twist command."""
        if self.is_stale():
            return self.lost_ball_twist()

        twist = Twist()
        radius = max(float(self.last_radius), 0.0)
        if radius >= self.target_radius_px:
            return twist

        half_width = max(self.image_width / 2.0, 1.0)
        error = (float(self.last_center_x) - half_width) / half_width
        angular = -self.angular_kp * error
        twist.angular.z = clamp(
            angular,
            -self.max_angular_velocity,
            self.max_angular_velocity,
        )

        if abs(error) > self.center_tolerance:
            return twist

        remaining = max(self.target_radius_px - radius, 0.0)
        slowdown_span = max(self.target_radius_px - self.slowdown_radius_px, 1.0)
        scale = clamp(remaining / slowdown_span, 0.0, 1.0)
        linear = self.linear_kp * scale
        twist.linear.x = clamp(linear, 0.0, self.max_linear_velocity)
        return twist

    def lost_ball_twist(self):
        """Return the safe lost-ball behavior."""
        twist = Twist()
        if self.search_when_lost:
            twist.angular.z = clamp(
                self.search_angular_velocity,
                -self.max_angular_velocity,
                self.max_angular_velocity,
            )
        return twist

    def is_stale(self):
        """Return true when no recent detection exists."""
        if self.last_detection_time is None:
            return True
        return (
            time.monotonic() - self.last_detection_time
        ) > self.lost_detection_timeout_sec

    def shutdown(self):
        """Publish a stop command before the node exits."""
        try:
            if rclpy.ok():
                self.cmd_vel_publisher.publish(Twist())
        except Exception:
            pass


def main(args=None):
    """Run the ball follower node."""
    rclpy.init(args=args)
    node = None
    try:
        node = BallFollower()
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        if node is not None:
            node.shutdown()
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
