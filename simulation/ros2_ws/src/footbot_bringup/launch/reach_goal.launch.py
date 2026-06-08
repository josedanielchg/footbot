from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction, TimerAction
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def spawn_ball(context):
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
                        '-name', 'reach_goal_ball',
                        '-allow_renaming', 'false',
                        '-x', LaunchConfiguration('ball_x'),
                        '-y', LaunchConfiguration('ball_y'),
                        '-z', '0.045',
                    ],
                ),
            ],
        ),
    ]


def include_spawn():
    spawn_launch = PathJoinSubstitution([
        FindPackageShare('footbot_bringup'),
        'launch',
        'spawn_footbot.launch.py',
    ])
    return IncludeLaunchDescription(
        PythonLaunchDescriptionSource(spawn_launch),
        launch_arguments={
            'use_gui': LaunchConfiguration('use_gui'),
            'use_http_bridge': 'false',
            'cmd_vel_topic': LaunchConfiguration('cmd_vel_topic'),
            'world_name': 'footbot_reach_goal.sdf',
            'robot_x': LaunchConfiguration('robot_x'),
            'robot_y': LaunchConfiguration('robot_y'),
            'robot_z': '0.02',
            'robot_yaw': LaunchConfiguration('robot_yaw'),
        }.items(),
    )


def generate_launch_description():
    reach_goal_config = PathJoinSubstitution([
        FindPackageShare('footbot_soccer_behavior'),
        'config',
        'reach_goal.yaml',
    ])

    yolo_detector = Node(
        package='footbot_soccer_vision',
        executable='yolo_detector',
        output='screen',
        parameters=[{
            'image_topic': LaunchConfiguration('camera_topic'),
            'detections_topic': LaunchConfiguration('detections_topic'),
            'debug_image_topic': LaunchConfiguration('debug_image_topic'),
            'publish_debug_image': ParameterValue(
                LaunchConfiguration('publish_debug_image'),
                value_type=bool,
            ),
            'model_path': LaunchConfiguration('model_path'),
            'model_name': LaunchConfiguration('model_name'),
            'target_classes': LaunchConfiguration('target_classes'),
            'confidence_threshold': ParameterValue(
                LaunchConfiguration('confidence_threshold'),
                value_type=float,
            ),
            'iou_threshold': ParameterValue(
                LaunchConfiguration('iou_threshold'),
                value_type=float,
            ),
            'device': LaunchConfiguration('device'),
            'image_size': ParameterValue(LaunchConfiguration('image_size'), value_type=int),
            'max_fps': ParameterValue(LaunchConfiguration('max_fps'), value_type=float),
            'max_detections': ParameterValue(LaunchConfiguration('max_detections'), value_type=int),
        }],
    )

    debug_viewer = Node(
        package='footbot_perception',
        executable='debug_image_viewer',
        output='screen',
        condition=IfCondition(LaunchConfiguration('show_debug_view')),
        parameters=[{
            'image_topic': LaunchConfiguration('debug_image_topic'),
            'window_name': 'FootBot Reach Goal YOLO Debug',
        }],
    )

    # Reach Goal behavior. Only the FSM owns /cmd_vel in this mode.
    world_pose_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        output='screen',
        condition=IfCondition(LaunchConfiguration('run_score_monitor')),
        arguments=[
            '/world/footbot_world/pose/info@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V',
        ],
    )

    ball_goal_state_estimator = Node(
        package='footbot_soccer_behavior',
        executable='ball_goal_state_estimator',
        output='screen',
        condition=IfCondition(LaunchConfiguration('run_behavior')),
        parameters=[reach_goal_config, {
            'detections_topic': LaunchConfiguration('detections_topic'),
            'ball_goal_state_topic': LaunchConfiguration('ball_goal_state_topic'),
        }],
    )

    reach_goal_fsm = Node(
        package='footbot_soccer_behavior',
        executable='reach_goal_fsm',
        output='screen',
        condition=IfCondition(LaunchConfiguration('run_behavior')),
        parameters=[reach_goal_config, {
            'ball_goal_state_topic': LaunchConfiguration('ball_goal_state_topic'),
            'cmd_vel_topic': LaunchConfiguration('cmd_vel_topic'),
            'fsm_state_topic': LaunchConfiguration('fsm_state_topic'),
            'goal_scored_topic': LaunchConfiguration('goal_scored_topic'),
        }],
    )

    score_monitor = Node(
        package='footbot_soccer_behavior',
        executable='reach_goal_score_monitor',
        output='screen',
        condition=IfCondition(LaunchConfiguration('run_score_monitor')),
        parameters=[reach_goal_config, {
            'ball_pose_topic': LaunchConfiguration('ball_pose_topic'),
            'world_pose_topic': LaunchConfiguration('world_pose_topic'),
            'ball_entity_name': LaunchConfiguration('ball_entity_name'),
            'goal_scored_topic': LaunchConfiguration('goal_scored_topic'),
        }],
    )

    return LaunchDescription([
        DeclareLaunchArgument('use_gui', default_value='true'),
        DeclareLaunchArgument('show_debug_view', default_value='true'),
        DeclareLaunchArgument('run_behavior', default_value='true'),
        DeclareLaunchArgument('run_score_monitor', default_value='true'),
        DeclareLaunchArgument('robot_x', default_value='0.0'),
        DeclareLaunchArgument('robot_y', default_value='0.0'),
        DeclareLaunchArgument('robot_yaw', default_value='0.0'),
        DeclareLaunchArgument('ball_x', default_value='0.62'),
        DeclareLaunchArgument('ball_y', default_value='0.0'),
        DeclareLaunchArgument('cmd_vel_topic', default_value='/cmd_vel'),
        DeclareLaunchArgument('camera_topic', default_value='/camera/image_raw'),
        DeclareLaunchArgument('detections_topic', default_value='/soccer/detections'),
        DeclareLaunchArgument('debug_image_topic', default_value='/soccer/detections/debug_image'),
        DeclareLaunchArgument('ball_goal_state_topic', default_value='/soccer/ball_goal_state'),
        DeclareLaunchArgument('fsm_state_topic', default_value='/soccer/reach_goal_fsm_state'),
        DeclareLaunchArgument('goal_scored_topic', default_value='/soccer/goal_scored'),
        DeclareLaunchArgument('ball_pose_topic', default_value='/reach_goal/ball_pose'),
        DeclareLaunchArgument('world_pose_topic', default_value='/world/footbot_world/pose/info'),
        DeclareLaunchArgument('ball_entity_name', default_value='reach_goal_ball'),
        DeclareLaunchArgument('publish_debug_image', default_value='true'),
        DeclareLaunchArgument('model_path', default_value=''),
        DeclareLaunchArgument('model_name', default_value='yolo11n.pt'),
        DeclareLaunchArgument('target_classes', default_value='ball,goal'),
        DeclareLaunchArgument('confidence_threshold', default_value='0.25'),
        DeclareLaunchArgument('iou_threshold', default_value='0.45'),
        DeclareLaunchArgument('device', default_value='cpu'),
        DeclareLaunchArgument('image_size', default_value='640'),
        DeclareLaunchArgument('max_fps', default_value='10.0'),
        DeclareLaunchArgument('max_detections', default_value='20'),
        include_spawn(),
        OpaqueFunction(function=spawn_ball),
        yolo_detector,
        debug_viewer,
        world_pose_bridge,
        ball_goal_state_estimator,
        reach_goal_fsm,
        score_monitor,
    ])
