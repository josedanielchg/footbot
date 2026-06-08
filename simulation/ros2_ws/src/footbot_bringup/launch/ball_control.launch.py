from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction, TimerAction
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


SCENARIOS = {
    'front': {'ball_x': '0.85', 'ball_y': '0.00', 'robot_yaw': '0.0'},
    'left': {'ball_x': '0.75', 'ball_y': '0.30', 'robot_yaw': '0.0'},
    'right': {'ball_x': '0.75', 'ball_y': '-0.30', 'robot_yaw': '0.0'},
    'far': {'ball_x': '1.35', 'ball_y': '0.00', 'robot_yaw': '0.0'},
    'close': {'ball_x': '0.32', 'ball_y': '0.00', 'robot_yaw': '0.0'},
    'misaligned': {'ball_x': '0.85', 'ball_y': '0.00', 'robot_yaw': '0.45'},
}


def resolve_scenario(context):
    scenario_name = LaunchConfiguration('scenario').perform(context)
    scenario = SCENARIOS.get(scenario_name, SCENARIOS['front'])
    ball_x = LaunchConfiguration('ball_x').perform(context)
    ball_y = LaunchConfiguration('ball_y').perform(context)
    robot_yaw = LaunchConfiguration('robot_yaw').perform(context)
    return {
        'ball_x': scenario['ball_x'] if ball_x == 'auto' else ball_x,
        'ball_y': scenario['ball_y'] if ball_y == 'auto' else ball_y,
        'robot_yaw': scenario['robot_yaw'] if robot_yaw == 'auto' else robot_yaw,
    }


def spawn_ball(context):
    values = resolve_scenario(context)
    ball_model = PathJoinSubstitution([
        FindPackageShare('footbot_gazebo'),
        'models',
        'orange_ball',
        'model.sdf',
    ])
    return [
        TimerAction(
            period=4.0,
            actions=[
                Node(
                    package='ros_gz_sim',
                    executable='create',
                    output='screen',
                    arguments=[
                        '-world', 'footbot_world',
                        '-file', ball_model,
                        '-name', 'ball',
                        '-allow_renaming', 'false',
                        '-x', values['ball_x'],
                        '-y', values['ball_y'],
                        '-z', '0.045',
                    ],
                ),
            ],
        ),
    ]


def include_spawn(context):
    values = resolve_scenario(context)
    spawn_launch = PathJoinSubstitution([
        FindPackageShare('footbot_bringup'),
        'launch',
        'spawn_footbot.launch.py',
    ])
    return [
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(spawn_launch),
            launch_arguments={
                'use_gui': LaunchConfiguration('use_gui'),
                'use_http_bridge': 'false',
                'cmd_vel_topic': LaunchConfiguration('cmd_vel_topic'),
                'world_name': 'footbot_ball_control.sdf',
                'robot_x': LaunchConfiguration('robot_x'),
                'robot_y': LaunchConfiguration('robot_y'),
                'robot_z': '0.02',
                'robot_yaw': values['robot_yaw'],
            }.items(),
        ),
    ]


def generate_launch_description():
    use_gui = LaunchConfiguration('use_gui')
    camera_topic = LaunchConfiguration('camera_topic')
    detection_topic = LaunchConfiguration('detection_topic')
    debug_image_topic = LaunchConfiguration('debug_image_topic')
    ball_state_topic = LaunchConfiguration('ball_state_topic')
    fsm_state_topic = LaunchConfiguration('fsm_state_topic')
    cmd_vel_topic = LaunchConfiguration('cmd_vel_topic')
    show_debug_view = LaunchConfiguration('show_debug_view')
    publish_debug_image = LaunchConfiguration('publish_debug_image')
    rotate_with_ball_enabled = LaunchConfiguration('rotate_with_ball_enabled')
    ball_control_config = PathJoinSubstitution([
        FindPackageShare('footbot_soccer_behavior'),
        'config',
        'ball_control.yaml',
    ])

    ball_detector = Node(
        package='footbot_perception',
        executable='ball_detector',
        output='screen',
        parameters=[{
            'image_topic': camera_topic,
            'detection_topic': detection_topic,
            'debug_image_topic': debug_image_topic,
            'publish_debug_image': ParameterValue(publish_debug_image, value_type=bool),
            'min_circularity': 0.30,
            'min_confidence': 0.30,
        }],
    )

    ball_state_estimator = Node(
        package='footbot_soccer_behavior',
        executable='ball_state_estimator',
        output='screen',
        parameters=[ball_control_config, {
            'detection_topic': detection_topic,
            'ball_state_topic': ball_state_topic,
        }],
    )

    ball_control_fsm = Node(
        package='footbot_soccer_behavior',
        executable='ball_control_fsm',
        output='screen',
        parameters=[ball_control_config, {
            'ball_state_topic': ball_state_topic,
            'cmd_vel_topic': cmd_vel_topic,
            'fsm_state_topic': fsm_state_topic,
            'rotate_with_ball_enabled': ParameterValue(
                rotate_with_ball_enabled,
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
            'window_name': 'FootBot Ball Control Debug',
        }],
    )

    return LaunchDescription([
        DeclareLaunchArgument('use_gui', default_value='true'),
        DeclareLaunchArgument('scenario', default_value='front'),
        DeclareLaunchArgument('camera_topic', default_value='/camera/image_raw'),
        DeclareLaunchArgument('detection_topic', default_value='/ball_detection'),
        DeclareLaunchArgument('debug_image_topic', default_value='/ball/debug_image'),
        DeclareLaunchArgument('ball_state_topic', default_value='/soccer/ball_state'),
        DeclareLaunchArgument('fsm_state_topic', default_value='/soccer/fsm_state'),
        DeclareLaunchArgument('cmd_vel_topic', default_value='/cmd_vel'),
        DeclareLaunchArgument('show_debug_view', default_value='false'),
        DeclareLaunchArgument('publish_debug_image', default_value='true'),
        DeclareLaunchArgument('rotate_with_ball_enabled', default_value='true'),
        DeclareLaunchArgument('ball_x', default_value='auto'),
        DeclareLaunchArgument('ball_y', default_value='auto'),
        DeclareLaunchArgument('robot_x', default_value='0.0'),
        DeclareLaunchArgument('robot_y', default_value='0.0'),
        DeclareLaunchArgument('robot_yaw', default_value='auto'),
        OpaqueFunction(function=include_spawn),
        OpaqueFunction(function=spawn_ball),
        ball_detector,
        ball_state_estimator,
        ball_control_fsm,
        debug_image_viewer,
    ])
