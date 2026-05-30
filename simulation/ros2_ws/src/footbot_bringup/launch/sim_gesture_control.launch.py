from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    use_gui = LaunchConfiguration('use_gui')
    use_http_bridge = LaunchConfiguration('use_http_bridge')
    http_host = LaunchConfiguration('http_host')
    http_port = LaunchConfiguration('http_port')
    cmd_vel_topic = LaunchConfiguration('cmd_vel_topic')
    camera_index = LaunchConfiguration('camera_index')
    publish_debug_image = LaunchConfiguration('publish_debug_image')
    show_debug_view = LaunchConfiguration('show_debug_view')

    bringup_share = FindPackageShare('footbot_bringup')
    simulation_launch = PathJoinSubstitution([
        bringup_share,
        'launch',
        'spawn_footbot.launch.py',
    ])
    perception_launch = PathJoinSubstitution([
        bringup_share,
        'launch',
        'gesture_perception.launch.py',
    ])
    control_launch = PathJoinSubstitution([
        bringup_share,
        'launch',
        'gesture_control.launch.py',
    ])

    simulation = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(simulation_launch),
        launch_arguments={
            'use_gui': use_gui,
            'use_http_bridge': use_http_bridge,
            'http_host': http_host,
            'http_port': http_port,
            'cmd_vel_topic': cmd_vel_topic,
        }.items(),
    )

    perception = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(perception_launch),
        launch_arguments={
            'camera_index': camera_index,
            'publish_debug_image': publish_debug_image,
            'show_debug_view': show_debug_view,
        }.items(),
    )

    control = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(control_launch),
        launch_arguments={
            'cmd_vel_topic': cmd_vel_topic,
        }.items(),
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_gui',
            default_value='true',
            description='Start the Gazebo GUI when true.',
        ),
        DeclareLaunchArgument(
            'use_http_bridge',
            default_value='true',
            description='Keep the ESP32-compatible HTTP bridge available.',
        ),
        DeclareLaunchArgument(
            'http_host',
            default_value='127.0.0.1',
            description='Host address for the HTTP command bridge.',
        ),
        DeclareLaunchArgument(
            'http_port',
            default_value='8080',
            description='Port for the HTTP command bridge.',
        ),
        DeclareLaunchArgument(
            'cmd_vel_topic',
            default_value='/cmd_vel',
            description='Shared Twist command topic.',
        ),
        DeclareLaunchArgument(
            'camera_index',
            default_value='0',
            description='OpenCV camera index for gesture input.',
        ),
        DeclareLaunchArgument(
            'publish_debug_image',
            default_value='true',
            description='Publish annotated gesture debug images.',
        ),
        DeclareLaunchArgument(
            'show_debug_view',
            default_value='false',
            description='Open an OpenCV window for annotated gesture images.',
        ),
        simulation,
        perception,
        control,
    ])
