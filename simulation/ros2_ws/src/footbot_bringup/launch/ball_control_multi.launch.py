from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, SetEnvironmentVariable, TimerAction
from launch.conditions import IfCondition, UnlessCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, EnvironmentVariable, FindExecutable, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackagePrefix, FindPackageShare


LANES = [
    {
        'key': 'front',
        'model_name': 'footbot_front',
        'robot_x': '0.0',
        'robot_y': '0.0',
        'robot_yaw': '0.0',
        'ball_name': 'ball_front',
        'ball_x': '0.85',
        'ball_y': '0.0',
        'window_name': 'Ball Control Front Lane',
    },
    {
        'key': 'far',
        'model_name': 'footbot_far',
        'robot_x': '0.0',
        'robot_y': '2.0',
        'robot_yaw': '0.0',
        'ball_name': 'ball_far',
        'ball_x': '1.35',
        'ball_y': '2.0',
        'window_name': 'Ball Control Far Lane',
    },
    {
        'key': 'behind',
        'model_name': 'footbot_behind',
        'robot_x': '0.0',
        'robot_y': '-2.0',
        'robot_yaw': '0.0',
        'ball_name': 'ball_behind',
        'ball_x': '-0.75',
        'ball_y': '-2.0',
        'window_name': 'Ball Control Behind Lane',
    },
]


def lane_topic(lane, suffix):
    return f'/ball_control/{lane["key"]}/{suffix}'


def lane_namespace(lane):
    return f'/ball_control/{lane["key"]}'


def create_lane_actions(lane, robot_description_file, ball_model, show_debug_view):
    namespace = lane_namespace(lane)
    cmd_vel_topic = lane_topic(lane, 'cmd_vel')
    camera_image_topic = lane_topic(lane, 'camera/image_raw')
    camera_info_topic = lane_topic(lane, 'camera/camera_info')
    detection_topic = lane_topic(lane, 'ball_detection')
    debug_image_topic = lane_topic(lane, 'ball/debug_image')
    ball_state_topic = lane_topic(lane, 'soccer/ball_state')
    fsm_state_topic = lane_topic(lane, 'soccer/fsm_state')
    robot_description_topic = lane_topic(lane, 'robot_description')
    odom_gz_topic = f'/model/{lane["model_name"]}/odometry'
    odom_ros_topic = lane_topic(lane, 'odom')

    robot_description = {
        'robot_description': ParameterValue(
            Command([
                FindExecutable(name='xacro'),
                ' ',
                robot_description_file,
                ' cmd_vel_topic:=', cmd_vel_topic,
                ' camera_image_topic:=', camera_image_topic,
                ' camera_info_topic:=', camera_info_topic,
                ' camera_frame_id:=', lane['key'], '_camera_optical_frame',
            ]),
            value_type=str,
        )
    }

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        namespace=namespace,
        output='screen',
        parameters=[
            robot_description,
            {'frame_prefix': f'{lane["key"]}_'},
        ],
    )

    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        namespace=namespace,
        arguments=[
            f'{cmd_vel_topic}@geometry_msgs/msg/Twist]gz.msgs.Twist',
            f'{camera_image_topic}@sensor_msgs/msg/Image[gz.msgs.Image',
            f'{camera_info_topic}@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo',
            f'{odom_gz_topic}@nav_msgs/msg/Odometry[gz.msgs.Odometry',
        ],
        remappings=[
            (odom_gz_topic, odom_ros_topic),
        ],
        output='screen',
    )

    spawn_robot = TimerAction(
        period=3.0,
        actions=[
            Node(
                package='ros_gz_sim',
                executable='create',
                output='screen',
                arguments=[
                    '-world', 'footbot_stage2',
                    '-topic', robot_description_topic,
                    '-name', lane['model_name'],
                    '-allow_renaming', 'false',
                    '-x', lane['robot_x'],
                    '-y', lane['robot_y'],
                    '-z', '0.02',
                    '-Y', lane['robot_yaw'],
                ],
            ),
        ],
    )

    spawn_ball = TimerAction(
        period=5.0,
        actions=[
            Node(
                package='ros_gz_sim',
                executable='create',
                output='screen',
                arguments=[
                    '-world', 'footbot_stage2',
                    '-file', ball_model,
                    '-name', lane['ball_name'],
                    '-allow_renaming', 'false',
                    '-x', lane['ball_x'],
                    '-y', lane['ball_y'],
                    '-z', '0.045',
                ],
            ),
        ],
    )

    ball_detector = Node(
        package='footbot_perception',
        executable='ball_detector',
        namespace=namespace,
        output='screen',
        parameters=[{
            'image_topic': camera_image_topic,
            'detection_topic': detection_topic,
            'debug_image_topic': debug_image_topic,
            'publish_debug_image': True,
            'min_circularity': 0.30,
            'min_confidence': 0.30,
        }],
    )

    ball_state_estimator = Node(
        package='footbot_soccer_behavior',
        executable='ball_state_estimator',
        namespace=namespace,
        output='screen',
        parameters=[{
            'detection_topic': detection_topic,
            'ball_state_topic': ball_state_topic,
        }],
    )

    ball_control_fsm = Node(
        package='footbot_soccer_behavior',
        executable='ball_control_fsm',
        namespace=namespace,
        output='screen',
        parameters=[{
            'ball_state_topic': ball_state_topic,
            'cmd_vel_topic': cmd_vel_topic,
            'fsm_state_topic': fsm_state_topic,
            'rotate_with_ball_enabled': True,
        }],
    )

    debug_image_viewer = Node(
        package='footbot_perception',
        executable='debug_image_viewer',
        namespace=namespace,
        output='screen',
        condition=IfCondition(show_debug_view),
        parameters=[{
            'image_topic': debug_image_topic,
            'window_name': lane['window_name'],
        }],
    )

    return [
        robot_state_publisher,
        bridge,
        spawn_robot,
        spawn_ball,
        ball_detector,
        ball_state_estimator,
        ball_control_fsm,
        debug_image_viewer,
    ]


def generate_launch_description():
    use_gui = LaunchConfiguration('use_gui')
    show_debug_view = LaunchConfiguration('show_debug_view')

    world_file = PathJoinSubstitution([
        FindPackageShare('footbot_gazebo'),
        'worlds',
        'footbot_ball_control_multi.sdf',
    ])
    gz_launch_file = PathJoinSubstitution([
        FindPackageShare('ros_gz_sim'),
        'launch',
        'gz_sim.launch.py',
    ])
    robot_description_file = PathJoinSubstitution([
        FindPackageShare('footbot_description'),
        'urdf',
        'footbot.urdf.xacro',
    ])
    ball_model = PathJoinSubstitution([
        FindPackageShare('footbot_gazebo'),
        'models',
        'orange_ball',
        'model.sdf',
    ])
    gazebo_plugin_path = SetEnvironmentVariable(
        name='IGN_GAZEBO_SYSTEM_PLUGIN_PATH',
        value=[
            PathJoinSubstitution([
                FindPackagePrefix('footbot_gazebo'),
                'lib',
            ]),
            ':',
            EnvironmentVariable(
                'IGN_GAZEBO_SYSTEM_PLUGIN_PATH',
                default_value='',
            ),
        ],
    )

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

    actions = [
        DeclareLaunchArgument('use_gui', default_value='true'),
        DeclareLaunchArgument('show_debug_view', default_value='false'),
        gazebo_plugin_path,
        gazebo_gui,
        gazebo_headless,
    ]

    for lane in LANES:
        actions.extend(
            create_lane_actions(
                lane,
                robot_description_file,
                ball_model,
                show_debug_view,
            )
        )

    return LaunchDescription(actions)
