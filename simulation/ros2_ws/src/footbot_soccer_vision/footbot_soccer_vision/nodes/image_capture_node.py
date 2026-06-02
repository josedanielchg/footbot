import csv
from datetime import datetime
from pathlib import Path

import rclpy
from cv_bridge import CvBridge, CvBridgeError
from rclpy.node import Node
from sensor_msgs.msg import Image


class ImageCaptureNode(Node):
    def __init__(self):
        super().__init__('soccer_image_capture')

        self.declare_parameter('image_topic', '/camera/image_raw')
        self.declare_parameter('output_dir', '')
        self.declare_parameter('session_name', '')
        self.declare_parameter('capture_rate', 1.0)
        self.declare_parameter('enabled', True)
        self.declare_parameter('source_world', '')

        self.image_topic = self.get_parameter('image_topic').value
        self.enabled = bool(self.get_parameter('enabled').value)
        self.capture_rate = float(self.get_parameter('capture_rate').value)
        self.min_period = 0.0 if self.capture_rate <= 0.0 else 1.0 / self.capture_rate
        self.last_capture_time = None
        self.frame_count = 0

        session_name = self.get_parameter('session_name').value
        if not session_name:
            session_name = datetime.now().strftime('session_%Y%m%d_%H%M%S')

        output_dir = self.get_parameter('output_dir').value
        if output_dir:
            self.output_dir = Path(output_dir).expanduser()
        else:
            self.output_dir = Path(__file__).resolve().parents[2] / 'datasets' / 'raw'
        self.session_dir = self.output_dir / session_name
        self.images_dir = self.session_dir / 'images'
        self.images_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_path = self.session_dir / 'metadata.csv'

        self.bridge = CvBridge()
        self.metadata_file = self.metadata_path.open('a', newline='')
        self.metadata_writer = csv.writer(self.metadata_file)
        if self.metadata_path.stat().st_size == 0:
            self.metadata_writer.writerow([
                'filename',
                'stamp_sec',
                'stamp_nanosec',
                'frame_id',
                'image_topic',
                'width',
                'height',
                'source_world',
            ])
            self.metadata_file.flush()

        self.image_sub = self.create_subscription(Image, self.image_topic, self._on_image, 10)
        self.get_logger().info(f'Capturing from {self.image_topic} into {self.session_dir}')

    def _on_image(self, msg):
        if not self.enabled:
            return

        now = self.get_clock().now().nanoseconds / 1e9
        if self.last_capture_time is not None and now - self.last_capture_time < self.min_period:
            return
        self.last_capture_time = now

        try:
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except CvBridgeError as exc:
            self.get_logger().warning(f'Failed to convert image: {exc}')
            return

        filename = f'frame_{self.frame_count:06d}.jpg'
        output_path = self.images_dir / filename

        import cv2
        cv2.imwrite(str(output_path), frame)

        self.metadata_writer.writerow([
            filename,
            msg.header.stamp.sec,
            msg.header.stamp.nanosec,
            msg.header.frame_id,
            self.image_topic,
            msg.width,
            msg.height,
            self.get_parameter('source_world').value,
        ])
        self.metadata_file.flush()
        self.frame_count += 1

    def destroy_node(self):
        if hasattr(self, 'metadata_file') and not self.metadata_file.closed:
            self.metadata_file.close()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = ImageCaptureNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
