"""Generic YOLO detector node for Reach Goal soccer detections."""

import rclpy
from rclpy.executors import ExternalShutdownException

from footbot_soccer_vision.nodes.opponent_detector_node import OpponentDetectorNode


def main(args=None):
    rclpy.init(args=args)
    node = None
    try:
        node = OpponentDetectorNode(
            node_name='yolo_detector',
            defaults={
                'image_topic': '/camera/image_raw',
                'detections_topic': '/soccer/detections',
                'debug_image_topic': '/soccer/detections/debug_image',
                'target_classes': 'ball,goal',
                'confidence_threshold': 0.25,
                'iou_threshold': 0.45,
                'max_fps': 10.0,
            },
        )
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
