from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.conditions import IfCondition, UnlessCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, FindExecutable, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    use_gui = LaunchConfiguration('use_gui')

    robot_description_file = PathJoinSubstitution([
        FindPackageShare('footbot_description'),
        'urdf',
        'footbot.urdf.xacro',
    ])
    world_file = PathJoinSubstitution([
        FindPackageShare('footbot_gazebo'),
        'worlds',
        'footbot_empty.sdf',
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
        ],
        remappings=[
            ('/model/footbot/odometry', '/odom'),
        ],
        output='screen',
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
        gazebo_gui,
        gazebo_headless,
        robot_state_publisher,
        joint_state_publisher,
        bridge,
        spawn_footbot,
    ])
