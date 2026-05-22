from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, FindExecutable, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
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

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(gz_launch_file),
        launch_arguments={
            'gz_args': ['-r ', world_file],
            'gz_version': '6',
        }.items(),
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
        gazebo,
        robot_state_publisher,
        joint_state_publisher,
        spawn_footbot,
    ])
