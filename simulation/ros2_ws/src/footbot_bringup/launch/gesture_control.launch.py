from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    direction_topic = LaunchConfiguration('direction_topic')
    speed_topic = LaunchConfiguration('speed_topic')
    cmd_vel_topic = LaunchConfiguration('cmd_vel_topic')
    max_linear_velocity = LaunchConfiguration('max_linear_velocity')
    max_angular_velocity = LaunchConfiguration('max_angular_velocity')

    gesture_to_cmd_vel = Node(
        package='footbot_control',
        executable='gesture_to_cmd_vel',
        output='screen',
        parameters=[{
            'direction_topic': direction_topic,
            'speed_topic': speed_topic,
            'cmd_vel_topic': cmd_vel_topic,
            'max_linear_velocity': ParameterValue(
                max_linear_velocity,
                value_type=float,
            ),
            'max_angular_velocity': ParameterValue(
                max_angular_velocity,
                value_type=float,
            ),
        }],
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'direction_topic',
            default_value='/gesture/direction',
            description='Gesture direction topic.',
        ),
        DeclareLaunchArgument(
            'speed_topic',
            default_value='/gesture/speed',
            description='Normalized gesture speed topic.',
        ),
        DeclareLaunchArgument(
            'cmd_vel_topic',
            default_value='/cmd_vel',
            description='Output Twist topic.',
        ),
        DeclareLaunchArgument(
            'max_linear_velocity',
            default_value='0.25',
            description='Maximum linear velocity in meters per second.',
        ),
        DeclareLaunchArgument(
            'max_angular_velocity',
            default_value='1.2',
            description='Maximum angular velocity in radians per second.',
        ),
        gesture_to_cmd_vel,
    ])
