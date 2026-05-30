from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.conditions import IfCondition, UnlessCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, FindExecutable, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    use_gui = LaunchConfiguration('use_gui')
    use_http_bridge = LaunchConfiguration('use_http_bridge')
    http_host = LaunchConfiguration('http_host')
    http_port = LaunchConfiguration('http_port')
    cmd_vel_topic = LaunchConfiguration('cmd_vel_topic')
    world_name = LaunchConfiguration('world_name')

    robot_description_file = PathJoinSubstitution([
        FindPackageShare('footbot_description'),
        'urdf',
        'footbot.urdf.xacro',
    ])
    world_file = PathJoinSubstitution([
        FindPackageShare('footbot_gazebo'),
        'worlds',
        world_name,
    ])
    gz_launch_file = PathJoinSubstitution([
        FindPackageShare('ros_gz_sim'),
        'launch',
        'gz_sim.launch.py',
    ])

    robot_description = {
        'robot_description': Command([
            FindExecutable(name='xacro'),
            ' ',
            robot_description_file,
        ])
    }

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

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[robot_description],
    )

    joint_state_publisher = Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
        output='screen',
    )

    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist',
            '/model/footbot/odometry@nav_msgs/msg/Odometry[gz.msgs.Odometry',
            '/camera/image_raw@sensor_msgs/msg/Image[gz.msgs.Image',
            '/camera/camera_info@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo',
        ],
        remappings=[
            ('/model/footbot/odometry', '/odom'),
        ],
        output='screen',
    )

    http_bridge = Node(
        package='footbot_bridge',
        executable='http_bridge',
        output='screen',
        condition=IfCondition(use_http_bridge),
        parameters=[{
            'cmd_vel_topic': cmd_vel_topic,
            'http_host': http_host,
            'http_port': ParameterValue(http_port, value_type=int),
        }],
    )

    spawn_footbot = TimerAction(
        period=3.0,
        actions=[
            Node(
                package='ros_gz_sim',
                executable='create',
                output='screen',
                arguments=[
                    '-world', 'footbot_stage2',
                    '-topic', '/robot_description',
                    '-name', 'footbot',
                    '-x', '0',
                    '-y', '0',
                    '-z', '0.02',
                ],
            )
        ],
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_gui',
            default_value='true',
            description='Start the Gazebo GUI when true; run server-only when false.',
        ),
        DeclareLaunchArgument(
            'use_http_bridge',
            default_value='true',
            description='Start the ESP32-compatible HTTP command bridge.',
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
            description='ROS Twist topic used by the HTTP command bridge.',
        ),
        DeclareLaunchArgument(
            'world_name',
            default_value='footbot_camera_test.sdf',
            description='Gazebo world file from footbot_gazebo/worlds.',
        ),
        gazebo_gui,
        gazebo_headless,
        robot_state_publisher,
        joint_state_publisher,
        bridge,
        http_bridge,
        spawn_footbot,
    ])
