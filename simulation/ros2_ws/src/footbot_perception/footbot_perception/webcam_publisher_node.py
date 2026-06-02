"""Publish a local computer webcam as a ROS image topic."""

import cv2
import rclpy
from cv_bridge import CvBridge
from rclpy.node import Node
from sensor_msgs.msg import Image


class WebcamPublisher(Node):
    """Read frames from OpenCV VideoCapture and publish them as Image messages."""

    def __init__(self):
        super().__init__('webcam_publisher')
        self.declare_parameter('camera_index', 0)
        self.declare_parameter('image_topic', '/webcam/image_raw')
        self.declare_parameter('frame_id', 'webcam_frame')
        self.declare_parameter('publish_rate', 30.0)
        self.declare_parameter('width', 0)
        self.declare_parameter('height', 0)

        self.camera_index = int(self.get_parameter('camera_index').value)
        self.image_topic = self.get_parameter('image_topic').value
        self.frame_id = self.get_parameter('frame_id').value
        self.publish_rate = float(self.get_parameter('publish_rate').value)
        self.width = int(self.get_parameter('width').value)
        self.height = int(self.get_parameter('height').value)

        self.bridge = CvBridge()
        self.publisher = self.create_publisher(Image, self.image_topic, 10)

        self.capture = cv2.VideoCapture(self.camera_index)
        if self.width > 0:
            self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        if self.height > 0:
            self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)

        if not self.capture.isOpened():
            raise RuntimeError(
                'Could not open webcam at index %d' % self.camera_index
            )

        timer_period = 1.0 / max(self.publish_rate, 1.0)
        self.timer = self.create_timer(timer_period, self.publish_frame)
        self.get_logger().info(
            'Publishing webcam %d to %s' %
            (self.camera_index, self.image_topic)
        )

    def publish_frame(self):
        """Read and publish one webcam frame."""
        success, frame = self.capture.read()
        if not success:
            self.get_logger().warn('Failed to read webcam frame')
            return

        message = self.bridge.cv2_to_imgmsg(frame, encoding='bgr8')
        message.header.stamp = self.get_clock().now().to_msg()
        message.header.frame_id = self.frame_id
        self.publisher.publish(message)

    def shutdown(self):
        """Release the webcam device."""
        if self.capture is not None:
            self.capture.release()


def main(args=None):
    """Run the webcam publisher node."""
    rclpy.init(args=args)
    node = None
    try:
        node = WebcamPublisher()
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
