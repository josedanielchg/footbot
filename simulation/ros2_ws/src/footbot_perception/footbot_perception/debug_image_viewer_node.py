"""Display annotated gesture debug images in an OpenCV window."""

import cv2
import rclpy
from cv_bridge import CvBridge
from rclpy.node import Node
from sensor_msgs.msg import Image


class DebugImageViewer(Node):
    """Subscribe to a ROS image topic and show it with OpenCV."""

    def __init__(self):
        super().__init__('debug_image_viewer')
        self.declare_parameter('image_topic', '/gesture/debug_image')
        self.declare_parameter('window_name', 'FootBot Gesture Debug')

        self.image_topic = self.get_parameter('image_topic').value
        self.window_name = self.get_parameter('window_name').value
        self.bridge = CvBridge()
        self.subscription = self.create_subscription(
            Image,
            self.image_topic,
            self.show_image,
            10,
        )
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        self.get_logger().info(
            'Showing gesture debug images from %s' % self.image_topic
        )

    def show_image(self, image_msg):
        """Convert and display one debug image."""
        try:
            frame = self.bridge.imgmsg_to_cv2(image_msg, desired_encoding='bgr8')
        except Exception as exc:
            self.get_logger().warn('cv_bridge conversion failed: %s' % exc)
            return

        cv2.imshow(self.window_name, frame)
        cv2.waitKey(1)

    def shutdown(self):
        """Close the OpenCV window."""
        cv2.destroyWindow(self.window_name)


def main(args=None):
    """Run the debug image viewer node."""
    rclpy.init(args=args)
    node = None
    try:
        node = DebugImageViewer()
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
