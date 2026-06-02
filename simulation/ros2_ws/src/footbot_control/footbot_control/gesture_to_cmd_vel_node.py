"""Convert gesture intent topics into ROS velocity commands."""

import time

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node
from std_msgs.msg import Float32, String


VALID_DIRECTIONS = {
    'forward',
    'backward',
    'left',
    'right',
    'soft_left',
    'soft_right',
    'stop',
}


def clamp(value, minimum, maximum):
    """Clamp a numeric value into an inclusive range."""
    return max(minimum, min(maximum, value))


class GestureToCmdVel(Node):
    """Map high-level gesture commands into geometry_msgs/Twist."""

    def __init__(self):
        super().__init__('gesture_to_cmd_vel')
        self.declare_parameter('direction_topic', '/gesture/direction')
        self.declare_parameter('speed_topic', '/gesture/speed')
        self.declare_parameter('cmd_vel_topic', '/cmd_vel')
        self.declare_parameter('max_linear_velocity', 0.25)
        self.declare_parameter('max_angular_velocity', 1.2)
        self.declare_parameter('min_active_speed', 0.2)
        self.declare_parameter('command_timeout_sec', 0.75)
        self.declare_parameter('publish_rate', 20.0)

        self.direction_topic = self.get_parameter('direction_topic').value
        self.speed_topic = self.get_parameter('speed_topic').value
        self.cmd_vel_topic = self.get_parameter('cmd_vel_topic').value
        self.max_linear_velocity = float(
            self.get_parameter('max_linear_velocity').value
        )
        self.max_angular_velocity = float(
            self.get_parameter('max_angular_velocity').value
        )
        self.min_active_speed = float(
            self.get_parameter('min_active_speed').value
        )
        self.command_timeout_sec = float(
            self.get_parameter('command_timeout_sec').value
        )
        self.publish_rate = float(self.get_parameter('publish_rate').value)

        self.current_direction = 'stop'
        self.current_speed = 0.0
        self.last_direction_time = None

        self.cmd_vel_publisher = self.create_publisher(
            Twist,
            self.cmd_vel_topic,
            10,
        )
        self.direction_subscription = self.create_subscription(
            String,
            self.direction_topic,
            self.on_direction,
            10,
        )
        self.speed_subscription = self.create_subscription(
            Float32,
            self.speed_topic,
            self.on_speed,
            10,
        )
        self.timer = self.create_timer(
            1.0 / max(self.publish_rate, 1.0),
            self.publish_command,
        )
        self.get_logger().info(
            'Mapping %s and %s to %s' %
            (self.direction_topic, self.speed_topic, self.cmd_vel_topic)
        )

    def on_direction(self, message):
        """Store the latest gesture direction."""
        direction = message.data.strip().lower()
        if direction not in VALID_DIRECTIONS:
            self.get_logger().warn('Invalid gesture direction: %s' % direction)
            self.current_direction = 'stop'
        else:
            self.current_direction = direction
        self.last_direction_time = time.monotonic()

    def on_speed(self, message):
        """Store the latest normalized speed."""
        self.current_speed = float(clamp(message.data, 0.0, 1.0))

    def publish_command(self):
        """Publish the current command or a timeout stop."""
        twist = self.command_to_twist()
        self.cmd_vel_publisher.publish(twist)

    def command_to_twist(self):
        """Convert the latest gesture state into a Twist message."""
        if self.is_stale():
            return Twist()

        direction = self.current_direction
        if direction == 'stop':
            return Twist()

        speed = max(self.current_speed, self.min_active_speed)
        linear_speed = speed * self.max_linear_velocity
        angular_speed = speed * self.max_angular_velocity
        twist = Twist()

        if direction == 'forward':
            twist.linear.x = linear_speed
        elif direction == 'backward':
            twist.linear.x = -linear_speed
        elif direction == 'left':
            twist.angular.z = angular_speed
        elif direction == 'right':
            twist.angular.z = -angular_speed
        elif direction == 'soft_left':
            twist.linear.x = linear_speed
            twist.angular.z = angular_speed * 0.5
        elif direction == 'soft_right':
            twist.linear.x = linear_speed
            twist.angular.z = -angular_speed * 0.5

        return twist

    def is_stale(self):
        """Return true when no recent direction command has arrived."""
        if self.last_direction_time is None:
            return True
        return (
            time.monotonic() - self.last_direction_time
        ) > self.command_timeout_sec

    def shutdown(self):
        """Publish a stop command before the node exits."""
        self.cmd_vel_publisher.publish(Twist())


def main(args=None):
    """Run the gesture-to-cmd_vel node."""
    rclpy.init(args=args)
    node = None
    try:
        node = GestureToCmdVel()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if node is not None:
            node.shutdown()
            node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
