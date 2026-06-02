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
    show_debug_view = LaunchConfiguration('show_debug_view')
    image_topic = LaunchConfiguration('image_topic')
    model_path = LaunchConfiguration('model_path')
    model_name = LaunchConfiguration('model_name')
    opponent_classes = LaunchConfiguration('opponent_classes')
    goal_classes = LaunchConfiguration('goal_classes')
    confidence_threshold = LaunchConfiguration('confidence_threshold')
    iou_threshold = LaunchConfiguration('iou_threshold')
    device = LaunchConfiguration('device')
    image_size = LaunchConfiguration('image_size')
    max_fps = LaunchConfiguration('max_fps')

    field_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([
                FindPackageShare('footbot_bringup'),
                'launch',
                'soccer_field.launch.py',
            ])
        ]),
        launch_arguments={
            'use_gui': use_gui,
            'bridge_camera': 'true',
        }.items(),
    )

    common_params = {
        'image_topic': image_topic,
        'model_path': model_path,
        'model_name': model_name,
        'confidence_threshold': ParameterValue(confidence_threshold, value_type=float),
        'iou_threshold': ParameterValue(iou_threshold, value_type=float),
        'device': device,
        'image_size': ParameterValue(image_size, value_type=int),
        'max_fps': ParameterValue(max_fps, value_type=float),
        'publish_debug_image': True,
    }

    opponent_detector = Node(
        package='footbot_soccer_vision',
        executable='opponent_detector',
        output='screen',
        parameters=[{
            **common_params,
            'detections_topic': '/opponent_detections',
            'debug_image_topic': '/opponent_detection/debug_image',
            'target_classes': opponent_classes,
        }],
    )

    goal_detector = Node(
        package='footbot_soccer_vision',
        executable='goal_detector',
        output='screen',
        parameters=[{
            **common_params,
            'detections_topic': '/goal_detections',
            'debug_image_topic': '/goal_detection/debug_image',
            'target_classes': goal_classes,
        }],
    )

    opponent_debug_viewer = Node(
        package='footbot_perception',
        executable='debug_image_viewer',
        output='screen',
        condition=IfCondition(show_debug_view),
        parameters=[{
            'image_topic': '/opponent_detection/debug_image',
            'window_name': 'FootBot Opponent YOLO Debug',
        }],
    )

    goal_debug_viewer = Node(
        package='footbot_perception',
        executable='debug_image_viewer',
        output='screen',
        condition=IfCondition(show_debug_view),
        parameters=[{
            'image_topic': '/goal_detection/debug_image',
            'window_name': 'FootBot Goal YOLO Debug',
        }],
    )

    return LaunchDescription([
        DeclareLaunchArgument('use_gui', default_value='true'),
        DeclareLaunchArgument('show_debug_view', default_value='false'),
        DeclareLaunchArgument('image_topic', default_value='/soccer/camera/image_raw'),
        DeclareLaunchArgument('model_path', default_value=''),
        DeclareLaunchArgument('model_name', default_value='yolo11n.pt'),
        DeclareLaunchArgument('opponent_classes', default_value='person'),
        DeclareLaunchArgument('goal_classes', default_value='goal'),
        DeclareLaunchArgument('confidence_threshold', default_value='0.35'),
        DeclareLaunchArgument('iou_threshold', default_value='0.45'),
        DeclareLaunchArgument('device', default_value='cpu'),
        DeclareLaunchArgument('image_size', default_value='640'),
        DeclareLaunchArgument('max_fps', default_value='5.0'),
        field_launch,
        opponent_detector,
        goal_detector,
        opponent_debug_viewer,
        goal_debug_viewer,
    ])
