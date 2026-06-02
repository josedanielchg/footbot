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
    camera_topic = LaunchConfiguration('camera_topic')
    detection_topic = LaunchConfiguration('detection_topic')
    debug_image_topic = LaunchConfiguration('debug_image_topic')
    cmd_vel_topic = LaunchConfiguration('cmd_vel_topic')
    publish_debug_image = LaunchConfiguration('publish_debug_image')
    show_debug_view = LaunchConfiguration('show_debug_view')
    search_when_lost = LaunchConfiguration('search_when_lost')
    hsv_lower_h = LaunchConfiguration('hsv_lower_h')
    hsv_upper_h = LaunchConfiguration('hsv_upper_h')
    min_contour_area = LaunchConfiguration('min_contour_area')
    min_circularity = LaunchConfiguration('min_circularity')
    max_linear_velocity = LaunchConfiguration('max_linear_velocity')
    max_angular_velocity = LaunchConfiguration('max_angular_velocity')
    center_tolerance = LaunchConfiguration('center_tolerance')
    target_radius_px = LaunchConfiguration('target_radius_px')

    bringup_share = FindPackageShare('footbot_bringup')
    spawn_launch = PathJoinSubstitution([
        bringup_share,
        'launch',
        'spawn_footbot.launch.py',
    ])

    simulation = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(spawn_launch),
        launch_arguments={
            'use_gui': use_gui,
            'use_http_bridge': 'false',
            'cmd_vel_topic': cmd_vel_topic,
            'world_name': 'footbot_ball_follow.sdf',
        }.items(),
    )

    ball_detector = Node(
        package='footbot_perception',
        executable='ball_detector',
        output='screen',
        parameters=[{
            'image_topic': camera_topic,
            'detection_topic': detection_topic,
            'debug_image_topic': debug_image_topic,
            'publish_debug_image': ParameterValue(
                publish_debug_image,
                value_type=bool,
            ),
            'hsv_lower_h': ParameterValue(hsv_lower_h, value_type=int),
            'hsv_upper_h': ParameterValue(hsv_upper_h, value_type=int),
            'min_contour_area': ParameterValue(
                min_contour_area,
                value_type=float,
            ),
            'min_circularity': ParameterValue(
                min_circularity,
                value_type=float,
            ),
        }],
    )

    ball_follower = Node(
        package='footbot_control',
        executable='ball_follower',
        output='screen',
        parameters=[{
            'detection_topic': detection_topic,
            'cmd_vel_topic': cmd_vel_topic,
            'search_when_lost': ParameterValue(
                search_when_lost,
                value_type=bool,
            ),
            'max_linear_velocity': ParameterValue(
                max_linear_velocity,
                value_type=float,
            ),
            'max_angular_velocity': ParameterValue(
                max_angular_velocity,
                value_type=float,
            ),
            'center_tolerance': ParameterValue(
                center_tolerance,
                value_type=float,
            ),
            'target_radius_px': ParameterValue(
                target_radius_px,
                value_type=float,
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
            'window_name': 'FootBot Ball Follower Debug',
        }],
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_gui',
            default_value='true',
            description='Start the Gazebo GUI when true.',
        ),
        DeclareLaunchArgument(
            'camera_topic',
            default_value='/camera/image_raw',
            description='Robot-mounted camera image topic.',
        ),
        DeclareLaunchArgument(
            'detection_topic',
            default_value='/ball_detection',
            description='Ball detection topic.',
        ),
        DeclareLaunchArgument(
            'debug_image_topic',
            default_value='/ball/debug_image',
            description='Annotated ball detector debug image topic.',
        ),
        DeclareLaunchArgument(
            'cmd_vel_topic',
            default_value='/cmd_vel',
            description='Shared Twist command topic.',
        ),
        DeclareLaunchArgument(
            'publish_debug_image',
            default_value='true',
            description='Publish annotated ball detection debug images.',
        ),
        DeclareLaunchArgument(
            'show_debug_view',
            default_value='false',
            description='Open an OpenCV window for ball detector debug images.',
        ),
        DeclareLaunchArgument(
            'search_when_lost',
            default_value='false',
            description='Rotate slowly instead of stopping when the ball is lost.',
        ),
        DeclareLaunchArgument(
            'hsv_lower_h',
            default_value='5',
            description='Lower OpenCV HSV hue threshold for the orange ball.',
        ),
        DeclareLaunchArgument(
            'hsv_upper_h',
            default_value='25',
            description='Upper OpenCV HSV hue threshold for the orange ball.',
        ),
        DeclareLaunchArgument(
            'min_contour_area',
            default_value='80.0',
            description='Minimum contour area accepted as a ball.',
        ),
        DeclareLaunchArgument(
            'min_circularity',
            default_value='0.30',
            description='Minimum contour circularity accepted as a ball.',
        ),
        DeclareLaunchArgument(
            'max_linear_velocity',
            default_value='0.16',
            description='Maximum forward velocity for ball following.',
        ),
        DeclareLaunchArgument(
            'max_angular_velocity',
            default_value='1.0',
            description='Maximum turning velocity for ball following.',
        ),
        DeclareLaunchArgument(
            'center_tolerance',
            default_value='0.14',
            description='Normalized horizontal error allowed before driving.',
        ),
        DeclareLaunchArgument(
            'target_radius_px',
            default_value='150.0',
            description='Apparent ball radius at which the robot stops.',
        ),
        simulation,
        ball_detector,
        ball_follower,
        debug_image_viewer,
    ])
