"""Detect an orange ball in ROS camera images using OpenCV HSV segmentation."""

import math

import cv2
import numpy as np
import rclpy
from cv_bridge import CvBridge
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from sensor_msgs.msg import Image
from vision_msgs.msg import Detection2D, ObjectHypothesisWithPose


def clamp(value, minimum, maximum):
    """Clamp a numeric value into an inclusive range."""
    return max(minimum, min(maximum, value))


class BallDetector(Node):
    """Publish a 2D detection for the largest valid orange circular contour."""

    def __init__(self):
        super().__init__('ball_detector')
        self.declare_parameter('image_topic', '/camera/image_raw')
        self.declare_parameter('detection_topic', '/ball_detection')
        self.declare_parameter('debug_image_topic', '/ball/debug_image')
        self.declare_parameter('publish_debug_image', True)
        self.declare_parameter('hsv_lower_h', 5)
        self.declare_parameter('hsv_lower_s', 120)
        self.declare_parameter('hsv_lower_v', 120)
        self.declare_parameter('hsv_upper_h', 25)
        self.declare_parameter('hsv_upper_s', 255)
        self.declare_parameter('hsv_upper_v', 255)
        self.declare_parameter('min_contour_area', 80.0)
        self.declare_parameter('max_contour_area', 50000.0)
        self.declare_parameter('min_circularity', 0.30)
        self.declare_parameter('min_confidence', 0.30)

        self.image_topic = self.get_parameter('image_topic').value
        self.detection_topic = self.get_parameter('detection_topic').value
        self.debug_image_topic = self.get_parameter('debug_image_topic').value
        self.should_publish_debug_image = bool(
            self.get_parameter('publish_debug_image').value
        )
        self.lower_hsv = np.array([
            int(self.get_parameter('hsv_lower_h').value),
            int(self.get_parameter('hsv_lower_s').value),
            int(self.get_parameter('hsv_lower_v').value),
        ], dtype=np.uint8)
        self.upper_hsv = np.array([
            int(self.get_parameter('hsv_upper_h').value),
            int(self.get_parameter('hsv_upper_s').value),
            int(self.get_parameter('hsv_upper_v').value),
        ], dtype=np.uint8)
        self.min_contour_area = float(
            self.get_parameter('min_contour_area').value
        )
        self.max_contour_area = float(
            self.get_parameter('max_contour_area').value
        )
        self.min_circularity = float(
            self.get_parameter('min_circularity').value
        )
        self.min_confidence = float(self.get_parameter('min_confidence').value)

        self.bridge = CvBridge()
        self.detection_publisher = self.create_publisher(
            Detection2D,
            self.detection_topic,
            10,
        )
        self.debug_publisher = None
        if self.should_publish_debug_image:
            self.debug_publisher = self.create_publisher(
                Image,
                self.debug_image_topic,
                10,
            )
        self.subscription = self.create_subscription(
            Image,
            self.image_topic,
            self.process_image,
            10,
        )
        self.get_logger().info(
            'Detecting orange ball from %s and publishing %s' %
            (self.image_topic, self.detection_topic)
        )

    def process_image(self, image_msg):
        """Process one camera frame."""
        try:
            frame = self.bridge.imgmsg_to_cv2(image_msg, desired_encoding='bgr8')
        except Exception as exc:
            self.get_logger().warn('cv_bridge conversion failed: %s' % exc)
            return

        detection = self.detect_ball(frame)
        debug_frame = frame.copy()
        if detection is not None:
            self.publish_detection(image_msg, detection)
            self.draw_detection(debug_frame, detection)
        else:
            self.draw_no_detection(debug_frame)

        if self.debug_publisher is not None:
            self.publish_debug_image(debug_frame, image_msg.header)

    def detect_ball(self, frame):
        """Return the best ball detection data, or None."""
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, self.lower_hsv, self.upper_hsv)
        mask = cv2.GaussianBlur(mask, (5, 5), 0)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=1)

        contours, _ = cv2.findContours(
            mask,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE,
        )
        best = None
        for contour in contours:
            candidate = self.contour_to_detection(contour)
            if candidate is None:
                continue
            if best is None or candidate['area'] > best['area']:
                best = candidate
        return best

    def contour_to_detection(self, contour):
        """Convert a contour to detection data if it passes all filters."""
        area = float(cv2.contourArea(contour))
        if area < self.min_contour_area or area > self.max_contour_area:
            return None

        perimeter = float(cv2.arcLength(contour, True))
        if perimeter <= 0.0:
            return None

        circularity = 4.0 * math.pi * area / (perimeter * perimeter)
        confidence = clamp(circularity, 0.0, 1.0)
        if circularity < self.min_circularity or confidence < self.min_confidence:
            return None

        (center_x, center_y), radius = cv2.minEnclosingCircle(contour)
        if radius <= 0.0:
            return None

        return {
            'center_x': float(center_x),
            'center_y': float(center_y),
            'radius': float(radius),
            'area': area,
            'confidence': float(confidence),
        }

    def publish_detection(self, image_msg, detection):
        """Publish the ball detection as vision_msgs/Detection2D."""
        message = Detection2D()
        message.header = image_msg.header
        message.id = 'orange_ball'
        message.bbox.center.position.x = detection['center_x']
        message.bbox.center.position.y = detection['center_y']
        message.bbox.center.theta = 0.0
        message.bbox.size_x = detection['radius'] * 2.0
        message.bbox.size_y = detection['radius'] * 2.0

        result = ObjectHypothesisWithPose()
        result.hypothesis.class_id = 'ball'
        result.hypothesis.score = detection['confidence']
        message.results.append(result)
        self.detection_publisher.publish(message)

    @staticmethod
    def draw_detection(frame, detection):
        """Draw detection overlay on a debug frame."""
        center = (
            int(round(detection['center_x'])),
            int(round(detection['center_y'])),
        )
        radius = int(round(detection['radius']))
        cv2.circle(frame, center, max(radius, 2), (0, 255, 0), 2)
        cv2.circle(frame, center, 4, (0, 0, 255), -1)
        label = 'ball %.2f r=%.1f' % (
            detection['confidence'],
            detection['radius'],
        )
        cv2.putText(
            frame,
            label,
            (max(5, center[0] - radius), max(24, center[1] - radius - 10)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (0, 255, 255),
            2,
            cv2.LINE_AA,
        )

    @staticmethod
    def draw_no_detection(frame):
        """Draw a no-detection label on a debug frame."""
        cv2.putText(
            frame,
            'ball: not visible',
            (12, 34),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.75,
            (0, 255, 255),
            2,
            cv2.LINE_AA,
        )

    def publish_debug_image(self, frame, input_header):
        """Publish an annotated debug image."""
        message = self.bridge.cv2_to_imgmsg(frame, encoding='bgr8')
        message.header.stamp = self.get_clock().now().to_msg()
        message.header.frame_id = input_header.frame_id
        self.debug_publisher.publish(message)


def main(args=None):
    """Run the ball detector node."""
    rclpy.init(args=args)
    node = None
    try:
        node = BallDetector()
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
