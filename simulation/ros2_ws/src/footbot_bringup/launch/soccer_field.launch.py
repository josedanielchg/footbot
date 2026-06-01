from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition, UnlessCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    use_gui = LaunchConfiguration('use_gui')
    bridge_camera = LaunchConfiguration('bridge_camera')

    world_file = PathJoinSubstitution([
        FindPackageShare('footbot_gazebo'),
        'worlds',
        'footbot_soccer_field.sdf',
    ])
    gz_launch_file = PathJoinSubstitution([
        FindPackageShare('ros_gz_sim'),
        'launch',
        'gz_sim.launch.py',
    ])

    gazebo_gui = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(gz_launch_file),
        launch_arguments={
            'gz_args': ['-r ', world_file],
            'gz_version': '6',
        }.items(),
        condition=IfCondition(use_gui),
    )

    gazebo_headless = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(gz_launch_file),
        launch_arguments={
            'gz_args': ['-r -s ', world_file],
            'gz_version': '6',
        }.items(),
        condition=UnlessCondition(use_gui),
    )

    camera_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/soccer/camera/image_raw@sensor_msgs/msg/Image[gz.msgs.Image',
            '/soccer/camera/camera_info@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo',
        ],
        output='screen',
        condition=IfCondition(bridge_camera),
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_gui',
            default_value='true',
            description='Start the Gazebo GUI when true; run server-only when false.',
        ),
        DeclareLaunchArgument(
            'bridge_camera',
            default_value='true',
            description='Bridge the soccer field camera topics into ROS 2.',
        ),
        gazebo_gui,
        gazebo_headless,
        camera_bridge,
    ])
