import time

import rclpy
from cv_bridge import CvBridge, CvBridgeError
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from sensor_msgs.msg import Image
from vision_msgs.msg import Detection2D, Detection2DArray, ObjectHypothesisWithPose

from footbot_soccer_vision.detectors.yolo_detector import YoloDetector
from footbot_soccer_vision.utils.drawing import draw_detections


class OpponentDetectorNode(Node):
    DEFAULTS = {
        'image_topic': '/camera/image_raw',
        'detections_topic': '/opponent_detections',
        'debug_image_topic': '/opponent_detection/debug_image',
        'publish_debug_image': True,
        'model_path': '',
        'model_name': 'yolo11n.pt',
        'target_classes': 'person',
        'confidence_threshold': 0.35,
        'iou_threshold': 0.45,
        'device': 'cpu',
        'image_size': 640,
        'max_fps': 10.0,
        'max_detections': 20,
    }

    def __init__(self, node_name='opponent_detector', defaults=None):
        super().__init__(node_name)

        parameters = dict(self.DEFAULTS)
        parameters.update(defaults or {})

        for name, value in parameters.items():
            self.declare_parameter(name, value)

        self.image_topic = self.get_parameter('image_topic').value
        self.detections_topic = self.get_parameter('detections_topic').value
        self.debug_image_topic = self.get_parameter('debug_image_topic').value
        self.publish_debug_image = bool(self.get_parameter('publish_debug_image').value)
        self.max_fps = float(self.get_parameter('max_fps').value)
        self.min_period = 0.0 if self.max_fps <= 0.0 else 1.0 / self.max_fps
        self.last_process_time = 0.0
        self.last_fps_time = None
        self.current_fps = 0.0

        self.bridge = CvBridge()
        self.detector = YoloDetector(
            model_path=self.get_parameter('model_path').value,
            model_name=self.get_parameter('model_name').value,
            confidence_threshold=self.get_parameter('confidence_threshold').value,
            iou_threshold=self.get_parameter('iou_threshold').value,
            device=self.get_parameter('device').value,
            image_size=self.get_parameter('image_size').value,
            target_classes=self._target_classes(),
            max_detections=self.get_parameter('max_detections').value,
        )

        self.detections_pub = self.create_publisher(Detection2DArray, self.detections_topic, 10)
        self.debug_pub = None
        if self.publish_debug_image:
            self.debug_pub = self.create_publisher(Image, self.debug_image_topic, 10)

        self.image_sub = self.create_subscription(Image, self.image_topic, self._on_image, 10)
        self.get_logger().info(
            f'Listening on {self.image_topic}; publishing detections to {self.detections_topic}'
        )

    def _on_image(self, msg):
        now = time.monotonic()
        if now - self.last_process_time < self.min_period:
            return
        self.last_process_time = now

        try:
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except CvBridgeError as exc:
            self.get_logger().warning(f'Failed to convert image: {exc}')
            return

        try:
            detections = self.detector.detect(frame)
        except Exception as exc:
            self.get_logger().error(f'YOLO inference failed: {exc}')
            return

        self._update_fps()
        self.detections_pub.publish(self._to_detection_array(msg, detections))

        if self.debug_pub is not None:
            debug_frame = draw_detections(frame, detections, self.current_fps)
            debug_msg = self.bridge.cv2_to_imgmsg(debug_frame, encoding='bgr8')
            debug_msg.header = msg.header
            self.debug_pub.publish(debug_msg)

    def _to_detection_array(self, image_msg, detections):
        array = Detection2DArray()
        array.header = image_msg.header

        for index, detection in enumerate(detections):
            msg = Detection2D()
            msg.header = image_msg.header
            msg.id = f'{detection.class_name}_{index}'
            msg.bbox.center.position.x = detection.center_x
            msg.bbox.center.position.y = detection.center_y
            msg.bbox.center.theta = 0.0
            msg.bbox.size_x = detection.width
            msg.bbox.size_y = detection.height

            result = ObjectHypothesisWithPose()
            result.hypothesis.class_id = detection.class_name
            result.hypothesis.score = detection.confidence
            msg.results.append(result)
            array.detections.append(msg)

        return array

    def _target_classes(self):
        value = self.get_parameter('target_classes').value
        if isinstance(value, str):
            return [item.strip() for item in value.split(',') if item.strip()]
        return [str(item).strip() for item in value if str(item).strip()]

    def _update_fps(self):
        now = time.monotonic()
        if self.last_fps_time is not None:
            elapsed = now - self.last_fps_time
            if elapsed > 0.0:
                self.current_fps = 1.0 / elapsed
        self.last_fps_time = now


def main(args=None):
    rclpy.init(args=args)
    node = None
    try:
        node = OpponentDetectorNode()
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
