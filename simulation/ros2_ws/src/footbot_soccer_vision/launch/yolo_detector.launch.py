from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    image_topic = LaunchConfiguration('image_topic')
    detections_topic = LaunchConfiguration('detections_topic')
    debug_image_topic = LaunchConfiguration('debug_image_topic')
    publish_debug_image = LaunchConfiguration('publish_debug_image')
    model_path = LaunchConfiguration('model_path')
    model_name = LaunchConfiguration('model_name')
    target_classes = LaunchConfiguration('target_classes')
    confidence_threshold = LaunchConfiguration('confidence_threshold')
    iou_threshold = LaunchConfiguration('iou_threshold')
    device = LaunchConfiguration('device')
    image_size = LaunchConfiguration('image_size')
    max_fps = LaunchConfiguration('max_fps')
    max_detections = LaunchConfiguration('max_detections')
    show_debug_view = LaunchConfiguration('show_debug_view')

    detector = Node(
        package='footbot_soccer_vision',
        executable='yolo_detector',
        output='screen',
        parameters=[{
            'image_topic': image_topic,
            'detections_topic': detections_topic,
            'debug_image_topic': debug_image_topic,
            'publish_debug_image': ParameterValue(publish_debug_image, value_type=bool),
            'model_path': model_path,
            'model_name': model_name,
            'target_classes': target_classes,
            'confidence_threshold': ParameterValue(confidence_threshold, value_type=float),
            'iou_threshold': ParameterValue(iou_threshold, value_type=float),
            'device': device,
            'image_size': ParameterValue(image_size, value_type=int),
            'max_fps': ParameterValue(max_fps, value_type=float),
            'max_detections': ParameterValue(max_detections, value_type=int),
        }],
    )

    debug_viewer = Node(
        package='footbot_perception',
        executable='debug_image_viewer',
        output='screen',
        condition=IfCondition(show_debug_view),
        parameters=[{
            'image_topic': debug_image_topic,
            'window_name': 'FootBot Reach Goal YOLO Debug',
        }],
    )

    return LaunchDescription([
        DeclareLaunchArgument('image_topic', default_value='/camera/image_raw'),
        DeclareLaunchArgument('detections_topic', default_value='/soccer/detections'),
        DeclareLaunchArgument('debug_image_topic', default_value='/soccer/detections/debug_image'),
        DeclareLaunchArgument('publish_debug_image', default_value='true'),
        DeclareLaunchArgument('model_path', default_value=''),
        DeclareLaunchArgument('model_name', default_value='yolo11n.pt'),
        DeclareLaunchArgument('target_classes', default_value='ball,goal'),
        DeclareLaunchArgument('confidence_threshold', default_value='0.25'),
        DeclareLaunchArgument('iou_threshold', default_value='0.45'),
        DeclareLaunchArgument('device', default_value='cpu'),
        DeclareLaunchArgument('image_size', default_value='640'),
        DeclareLaunchArgument('max_fps', default_value='10.0'),
        DeclareLaunchArgument('max_detections', default_value='20'),
        DeclareLaunchArgument('show_debug_view', default_value='false'),
        detector,
        debug_viewer,
    ])
