"""Detect hand gestures from ROS images and publish movement intent."""

import cv2
import rclpy
from cv_bridge import CvBridge
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import Float32, String

from footbot_perception import gesture_config as config
from footbot_perception.gesture_logic import GestureLogic, normalize_speed


class HandDetectorNode(Node):
    """Run MediaPipe Hands on an image topic and publish gesture commands."""

    def __init__(self):
        super().__init__('hand_detector')
        self.declare_parameter('image_topic', '/webcam/image_raw')
        self.declare_parameter('debug_image_topic', '/gesture/debug_image')
        self.declare_parameter('direction_topic', '/gesture/direction')
        self.declare_parameter('speed_topic', '/gesture/speed')
        self.declare_parameter('publish_debug_image', True)
        self.declare_parameter('max_num_hands', config.MAX_NUM_HANDS)
        self.declare_parameter(
            'min_detection_confidence',
            config.MIN_DETECTION_CONFIDENCE,
        )
        self.declare_parameter(
            'min_tracking_confidence',
            config.MIN_TRACKING_CONFIDENCE,
        )
        self.declare_parameter('selfie_view', True)
        self.declare_parameter('lost_hand_direction', 'stop')
        self.declare_parameter('default_speed', config.DEFAULT_SPEED)

        self.image_topic = self.get_parameter('image_topic').value
        self.debug_image_topic = self.get_parameter('debug_image_topic').value
        self.direction_topic = self.get_parameter('direction_topic').value
        self.speed_topic = self.get_parameter('speed_topic').value
        self.should_publish_debug_image = bool(
            self.get_parameter('publish_debug_image').value
        )
        self.selfie_view = bool(self.get_parameter('selfie_view').value)
        self.lost_hand_direction = self.get_parameter('lost_hand_direction').value
        self.default_speed = int(self.get_parameter('default_speed').value)

        self.bridge = CvBridge()
        self.gesture_logic = GestureLogic()
        self.mp_hands = None
        self.hands_model = None
        self.mp_drawing = None
        self.mp_drawing_styles = None
        self.initialize_mediapipe()

        self.direction_publisher = self.create_publisher(
            String,
            self.direction_topic,
            10,
        )
        self.speed_publisher = self.create_publisher(Float32, self.speed_topic, 10)
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
            'Detecting hand gestures from %s' % self.image_topic
        )

    def initialize_mediapipe(self):
        """Initialize MediaPipe Hands and drawing helpers."""
        try:
            import mediapipe as mp
        except ImportError as exc:
            raise RuntimeError(
                'mediapipe is required. Install it with: '
                'python3 -m pip install --user mediapipe'
            ) from exc

        self.mp_hands = mp.solutions.hands
        self.hands_model = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=int(self.get_parameter('max_num_hands').value),
            min_detection_confidence=float(
                self.get_parameter('min_detection_confidence').value
            ),
            min_tracking_confidence=float(
                self.get_parameter('min_tracking_confidence').value
            ),
        )
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles

    def process_image(self, image_msg):
        """Process one image and publish gesture direction, speed, and debug."""
        try:
            frame = self.bridge.imgmsg_to_cv2(image_msg, desired_encoding='bgr8')
        except Exception as exc:
            self.get_logger().warn('cv_bridge conversion failed: %s' % exc)
            self.publish_gesture(self.lost_hand_direction, self.default_speed)
            return

        if self.selfie_view:
            frame = cv2.flip(frame, 1)

        results, output_frame = self.detect_hands(frame)
        direction, speed = self.extract_command(results, output_frame)
        self.publish_gesture(direction, speed)

        if self.debug_publisher is not None:
            self.publish_debug_image(output_frame, image_msg.header)

    def detect_hands(self, frame):
        """Run MediaPipe and draw landmarks onto a debug image."""
        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image_rgb.flags.writeable = False
        results = self.hands_model.process(image_rgb)
        image_rgb.flags.writeable = True
        output_frame = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                self.mp_drawing.draw_landmarks(
                    output_frame,
                    hand_landmarks,
                    self.mp_hands.HAND_CONNECTIONS,
                    self.mp_drawing_styles.get_default_hand_landmarks_style(),
                    self.mp_drawing_styles.get_default_hand_connections_style(),
                )
        return results, output_frame

    def extract_command(self, results, frame):
        """Extract right-hand direction and left-hand speed from detections."""
        frame_height, frame_width, _ = frame.shape
        right_hand_landmarks = None
        left_hand_landmarks = None

        for landmarks, handedness in self.get_detection_data(results):
            if handedness.lower() == 'right':
                right_hand_landmarks = landmarks
            elif handedness.lower() == 'left':
                left_hand_landmarks = landmarks

        direction = self.lost_hand_direction
        if right_hand_landmarks:
            finger_status = self.gesture_logic.get_fingers_status(
                right_hand_landmarks,
                'Right',
            )
            classified = self.gesture_logic.classify_gesture(finger_status)
            direction = classified or self.lost_hand_direction

        speed = self.default_speed
        if left_hand_landmarks:
            speed = self.gesture_logic.calculate_speed_from_left_hand(
                left_hand_landmarks,
                frame_width,
                frame_height,
            )

        return direction, speed

    @staticmethod
    def get_detection_data(results):
        """Return detected hand landmarks with handedness labels."""
        detected_hands_data = []
        if not results.multi_hand_landmarks:
            return detected_hands_data

        for index, hand_landmarks_proto in enumerate(results.multi_hand_landmarks):
            landmarks = hand_landmarks_proto.landmark
            handedness = 'Unknown'
            if results.multi_handedness and len(results.multi_handedness) > index:
                handedness = results.multi_handedness[
                    index
                ].classification[0].label
            detected_hands_data.append((landmarks, handedness))
        return detected_hands_data

    def publish_gesture(self, direction, speed):
        """Publish direction as text and speed normalized to 0.0-1.0."""
        direction_msg = String()
        direction_msg.data = direction
        self.direction_publisher.publish(direction_msg)

        speed_msg = Float32()
        speed_msg.data = float(normalize_speed(speed))
        self.speed_publisher.publish(speed_msg)

    def publish_debug_image(self, frame, input_header):
        """Publish an annotated debug image."""
        debug_msg = self.bridge.cv2_to_imgmsg(frame, encoding='bgr8')
        debug_msg.header.stamp = self.get_clock().now().to_msg()
        debug_msg.header.frame_id = input_header.frame_id
        self.debug_publisher.publish(debug_msg)

    def shutdown(self):
        """Release MediaPipe resources."""
        if self.hands_model is not None:
            self.hands_model.close()


def main(args=None):
    """Run the hand detector node."""
    rclpy.init(args=args)
    node = None
    try:
        node = HandDetectorNode()
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
