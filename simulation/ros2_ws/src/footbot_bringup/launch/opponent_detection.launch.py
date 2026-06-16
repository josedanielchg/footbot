from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    use_gui = LaunchConfiguration('use_gui')
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
    capture_images = LaunchConfiguration('capture_images')
    capture_output_dir = LaunchConfiguration('capture_output_dir')
    show_debug_view = LaunchConfiguration('show_debug_view')

    spawn_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([
                FindPackageShare('footbot_bringup'),
                'launch',
                'spawn_footbot.launch.py',
            ])
        ]),
        launch_arguments={
            'use_gui': use_gui,
            'world_name': 'footbot_opponent_detection.sdf',
            'use_http_bridge': 'false',
            'cmd_vel_topic': '/cmd_vel',
        }.items(),
    )

    opponent_detector = Node(
        package='footbot_soccer_vision',
        executable='opponent_detector',
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
            'device': ParameterValue(device, value_type=str),
            'image_size': ParameterValue(image_size, value_type=int),
            'max_fps': ParameterValue(max_fps, value_type=float),
            'max_detections': ParameterValue(max_detections, value_type=int),
        }],
    )

    image_capture = Node(
        package='footbot_soccer_vision',
        executable='image_capture',
        output='screen',
        condition=IfCondition(capture_images),
        parameters=[{
            'image_topic': image_topic,
            'output_dir': capture_output_dir,
            'source_world': 'footbot_opponent_detection.sdf',
        }],
    )

    debug_viewer = Node(
        package='footbot_perception',
        executable='debug_image_viewer',
        output='screen',
        condition=IfCondition(show_debug_view),
        parameters=[{
            'image_topic': debug_image_topic,
            'window_name': 'FootBot Opponent Detection Debug',
        }],
    )

    return LaunchDescription([
        DeclareLaunchArgument('use_gui', default_value='true'),
        DeclareLaunchArgument('image_topic', default_value='/camera/image_raw'),
        DeclareLaunchArgument('detections_topic', default_value='/opponent_detections'),
        DeclareLaunchArgument('debug_image_topic', default_value='/opponent_detection/debug_image'),
        DeclareLaunchArgument('publish_debug_image', default_value='true'),
        DeclareLaunchArgument('model_path', default_value=''),
        DeclareLaunchArgument('model_name', default_value='yolo11n.pt'),
        DeclareLaunchArgument('target_classes', default_value='person'),
        DeclareLaunchArgument('confidence_threshold', default_value='0.35'),
        DeclareLaunchArgument('iou_threshold', default_value='0.45'),
        DeclareLaunchArgument('device', default_value='cpu'),
        DeclareLaunchArgument('image_size', default_value='640'),
        DeclareLaunchArgument('max_fps', default_value='10.0'),
        DeclareLaunchArgument('max_detections', default_value='20'),
        DeclareLaunchArgument('capture_images', default_value='false'),
        DeclareLaunchArgument('capture_output_dir', default_value=''),
        DeclareLaunchArgument('show_debug_view', default_value='false'),
        spawn_launch,
        opponent_detector,
        image_capture,
        debug_viewer,
    ])
