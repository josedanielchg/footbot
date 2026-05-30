from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    camera_index = LaunchConfiguration('camera_index')
    image_topic = LaunchConfiguration('image_topic')
    debug_image_topic = LaunchConfiguration('debug_image_topic')
    direction_topic = LaunchConfiguration('direction_topic')
    speed_topic = LaunchConfiguration('speed_topic')
    publish_debug_image = LaunchConfiguration('publish_debug_image')
    show_debug_view = LaunchConfiguration('show_debug_view')

    webcam_publisher = Node(
        package='footbot_perception',
        executable='webcam_publisher',
        output='screen',
        parameters=[{
            'camera_index': ParameterValue(camera_index, value_type=int),
            'image_topic': image_topic,
        }],
    )

    hand_detector = Node(
        package='footbot_perception',
        executable='hand_detector',
        output='screen',
        parameters=[{
            'image_topic': image_topic,
            'debug_image_topic': debug_image_topic,
            'direction_topic': direction_topic,
            'speed_topic': speed_topic,
            'publish_debug_image': ParameterValue(
                publish_debug_image,
                value_type=bool,
            ),
        }],
    )

    debug_image_viewer = Node(
        package='footbot_perception',
        executable='debug_image_viewer',
        output='screen',
        condition=IfCondition(show_debug_view),
        parameters=[{
            'image_topic': debug_image_topic,
        }],
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'camera_index',
            default_value='0',
            description='OpenCV camera index for the computer webcam.',
        ),
        DeclareLaunchArgument(
            'image_topic',
            default_value='/webcam/image_raw',
            description='ROS image topic used for gesture detection.',
        ),
        DeclareLaunchArgument(
            'debug_image_topic',
            default_value='/gesture/debug_image',
            description='Annotated gesture debug image topic.',
        ),
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
            'publish_debug_image',
            default_value='true',
            description='Publish annotated hand landmark debug images.',
        ),
        DeclareLaunchArgument(
            'show_debug_view',
            default_value='false',
            description='Open an OpenCV window for annotated gesture images.',
        ),
        webcam_publisher,
        hand_detector,
        debug_image_viewer,
    ])
