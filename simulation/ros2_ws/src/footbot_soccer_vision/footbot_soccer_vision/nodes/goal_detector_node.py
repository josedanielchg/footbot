import rclpy

from footbot_soccer_vision.nodes.opponent_detector_node import OpponentDetectorNode


def main(args=None):
    rclpy.init(args=args)
    node = None
    try:
        node = OpponentDetectorNode(
            node_name='goal_detector',
            defaults={
                'image_topic': '/soccer/camera/image_raw',
                'detections_topic': '/goal_detections',
                'debug_image_topic': '/goal_detection/debug_image',
                'target_classes': 'goal',
            },
        )
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if node is not None:
            node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
