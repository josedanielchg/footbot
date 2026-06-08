"""Offline logic tests for the Reach-goal behavior.

These cover the perception-derived state estimator, the bounded skills, and the
FSM transitions with fabricated inputs. They do not need Gazebo or a running ROS
graph; nodes are constructed and their pure decision methods are driven directly.
"""

import time

import pytest
import rclpy
from geometry_msgs.msg import Pose, TransformStamped
from std_msgs.msg import Bool
from tf2_msgs.msg import TFMessage
from vision_msgs.msg import Detection2D, Detection2DArray, ObjectHypothesisWithPose

from footbot_soccer_msgs.msg import BallGoalState
from footbot_soccer_behavior.referee.reach_goal_score_monitor_node import (
    ReachGoalScoreMonitor,
    pose_inside_goal_zone,
)
from footbot_soccer_behavior.skills.reach_goal_skills import (
    ReachGoalSkillConfig,
    ReachGoalSkills,
)
from footbot_soccer_behavior.state_estimation.ball_goal_state_estimator_node import (
    BallGoalStateEstimator,
    best_detection,
    detection_score,
    focal_length_px,
    horizontal_geometry,
)
from footbot_soccer_behavior.fsm.reach_goal_fsm_node import ReachGoalFsm


IMAGE_WIDTH = 640.0
CENTER_X = IMAGE_WIDTH / 2.0


@pytest.fixture(scope='module', autouse=True)
def ros_context():
    created = False
    if not rclpy.ok():
        rclpy.init()
        created = True
    yield
    if created and rclpy.ok():
        rclpy.shutdown()


def make_detection(class_id, score, center_x, size_x, center_y=240.0, size_y=None):
    detection = Detection2D()
    detection.bbox.center.position.x = float(center_x)
    detection.bbox.center.position.y = float(center_y)
    detection.bbox.size_x = float(size_x)
    detection.bbox.size_y = float(size_y if size_y is not None else size_x)
    hypothesis = ObjectHypothesisWithPose()
    hypothesis.hypothesis.class_id = class_id
    hypothesis.hypothesis.score = float(score)
    detection.results.append(hypothesis)
    return detection


def make_array(detections):
    array = Detection2DArray()
    for detection in detections:
        array.detections.append(detection)
    return array


def make_state(**fields):
    state = BallGoalState()
    for name, value in fields.items():
        setattr(state, name, value)
    return state


# --- Pure helper functions -------------------------------------------------

def test_focal_length_matches_fov():
    focal = focal_length_px(640.0, 1.047)
    # 60-degree horizontal FOV on a 640px image is ~554px focal length.
    assert focal == pytest.approx(554.0, abs=2.0)


def test_horizontal_geometry_signs():
    focal = focal_length_px(IMAGE_WIDTH, 1.047)
    center_error, angle = horizontal_geometry(CENTER_X, IMAGE_WIDTH, focal)
    assert center_error == pytest.approx(0.0)
    assert angle == pytest.approx(0.0)

    right_error, right_angle = horizontal_geometry(CENTER_X + 160.0, IMAGE_WIDTH, focal)
    assert right_error > 0.0
    assert right_angle > 0.0

    left_error, left_angle = horizontal_geometry(CENTER_X - 160.0, IMAGE_WIDTH, focal)
    assert left_error < 0.0
    assert left_angle < 0.0


def test_best_detection_picks_highest_confidence_of_class():
    detections = [
        make_detection('ball', 0.40, CENTER_X, 60.0),
        make_detection('ball', 0.80, CENTER_X + 20.0, 70.0),
        make_detection('goal', 0.90, CENTER_X, 200.0),
    ]
    ball = best_detection(detections, 'ball', 0.25)
    assert detection_score(ball) == pytest.approx(0.80)
    goal = best_detection(detections, 'goal', 0.25)
    assert detection_score(goal) == pytest.approx(0.90)


def test_best_detection_respects_threshold():
    detections = [make_detection('ball', 0.10, CENTER_X, 60.0)]
    assert best_detection(detections, 'ball', 0.25) is None


# --- State estimator -------------------------------------------------------

def test_estimator_ball_only():
    estimator = BallGoalStateEstimator()
    try:
        estimator.on_detections(make_array([
            make_detection('ball', 0.9, CENTER_X, 80.0),
        ]))
        state = estimator.build_state(time.monotonic())
        assert state.ball_visible is True
        assert state.goal_visible is False
        assert state.stale is False
    finally:
        estimator.destroy_node()


def test_estimator_goal_only():
    estimator = BallGoalStateEstimator()
    try:
        estimator.on_detections(make_array([
            make_detection('goal', 0.9, CENTER_X, 220.0),
        ]))
        state = estimator.build_state(time.monotonic())
        assert state.goal_visible is True
        assert state.ball_visible is False
        assert state.stale is False
        assert state.goal_width_px == pytest.approx(220.0)
    finally:
        estimator.destroy_node()


def test_estimator_ball_and_goal_centered_aligned_and_controlled():
    estimator = BallGoalStateEstimator()
    try:
        # Make control immediate so a single build call can report it.
        estimator.control_hold_time_sec = 0.0
        estimator.on_detections(make_array([
            make_detection('ball', 0.9, CENTER_X, 220.0),
            make_detection('goal', 0.9, CENTER_X, 240.0),
        ]))
        state = estimator.build_state(time.monotonic())
        assert state.ball_visible is True
        assert state.goal_visible is True
        assert state.ball_goal_aligned is True
        assert state.has_ball_control is True
    finally:
        estimator.destroy_node()


def test_estimator_remembers_goal_after_temporary_loss():
    estimator = BallGoalStateEstimator()
    try:
        estimator.control_hold_time_sec = 0.0
        estimator.on_detections(make_array([
            make_detection('ball', 0.9, CENTER_X, 220.0),
            make_detection('goal', 0.9, CENTER_X + 20.0, 240.0),
        ]))
        fresh_state = estimator.build_state(time.monotonic())
        assert fresh_state.goal_visible is True
        assert fresh_state.goal_memory_active is False

        estimator.on_detections(make_array([
            make_detection('ball', 0.9, CENTER_X, 220.0),
        ]))
        remembered = estimator.build_state(time.monotonic())
        assert remembered.goal_visible is False
        assert remembered.goal_memory_active is True
        assert remembered.goal_memory_age_sec >= 0.0
        assert remembered.goal_center_error == pytest.approx(fresh_state.goal_center_error)
        assert remembered.ball_goal_aligned is True
    finally:
        estimator.destroy_node()


def test_estimator_goal_memory_expires():
    estimator = BallGoalStateEstimator()
    try:
        estimator.control_hold_time_sec = 0.0
        now = time.monotonic()
        estimator.on_detections(make_array([
            make_detection('ball', 0.9, CENTER_X, 220.0),
            make_detection('goal', 0.9, CENTER_X, 240.0),
        ]))
        estimator.latest_array_time = now
        estimator.latest_ball_time = now
        estimator.latest_goal_time = now - estimator.goal_memory_timeout_sec - 0.1
        state = estimator.build_state(now)
        assert state.goal_visible is False
        assert state.goal_memory_active is False
        assert estimator.latest_goal is None
    finally:
        estimator.destroy_node()


def test_estimator_goal_memory_clears_when_ball_control_is_lost():
    estimator = BallGoalStateEstimator()
    try:
        estimator.control_hold_time_sec = 0.0
        estimator.on_detections(make_array([
            make_detection('ball', 0.9, CENTER_X, 220.0),
            make_detection('goal', 0.9, CENTER_X, 240.0),
        ]))
        assert estimator.build_state(time.monotonic()).has_ball_control is True

        estimator.on_detections(make_array([
            make_detection('ball', 0.9, CENTER_X + 260.0, 20.0),
        ]))
        state = estimator.build_state(time.monotonic())
        assert state.has_ball_control is False
        assert state.goal_memory_active is False
        assert estimator.latest_goal is None
    finally:
        estimator.destroy_node()


def test_estimator_offset_ball_and_goal_not_aligned():
    estimator = BallGoalStateEstimator()
    try:
        estimator.on_detections(make_array([
            make_detection('ball', 0.9, CENTER_X - 200.0, 220.0),
            make_detection('goal', 0.9, CENTER_X + 200.0, 240.0),
        ]))
        state = estimator.build_state(time.monotonic())
        assert state.ball_goal_aligned is False
    finally:
        estimator.destroy_node()


def test_estimator_no_detections_is_stale():
    estimator = BallGoalStateEstimator()
    try:
        state = estimator.build_state(time.monotonic())
        assert state.stale is True
        assert state.ball_visible is False
        assert state.goal_visible is False
    finally:
        estimator.destroy_node()


def test_estimator_timed_out_detections_is_stale():
    estimator = BallGoalStateEstimator()
    try:
        estimator.on_detections(make_array([
            make_detection('ball', 0.9, CENTER_X, 220.0),
        ]))
        # Pretend the last array arrived well beyond the timeout window.
        old = time.monotonic() - (estimator.lost_detection_timeout_sec + 1.0)
        estimator.latest_array_time = old
        estimator.latest_ball_time = old
        state = estimator.build_state(time.monotonic())
        assert state.stale is True
        assert state.ball_visible is False
    finally:
        estimator.destroy_node()


# --- Skills ----------------------------------------------------------------

def test_skills_search_ball_rotates_in_place():
    skills = ReachGoalSkills()
    twist = skills.search_ball(make_state())
    assert twist.linear.x == pytest.approx(0.0)
    assert twist.angular.z > 0.0


def test_skills_approach_steers_toward_ball_and_moves_forward():
    skills = ReachGoalSkills()
    twist = skills.approach_ball(make_state(ball_angle_rad=0.3, ball_radius_px=40.0))
    assert twist.linear.x > 0.0
    # Ball to the right (positive angle) -> turn right (negative angular.z).
    assert twist.angular.z < 0.0


def test_skills_dribble_drives_forward():
    skills = ReachGoalSkills()
    twist = skills.dribble_to_goal(make_state(goal_angle_rad=0.0, ball_angle_rad=0.0))
    assert twist.linear.x > 0.0


def test_skills_commit_to_goal_drives_forward_with_ball_correction():
    skills = ReachGoalSkills()
    twist = skills.commit_to_goal(make_state(ball_angle_rad=0.25))
    assert twist.linear.x > 0.0
    # Ball to the right (positive angle) -> turn right (negative angular.z).
    assert twist.angular.z < 0.0


def test_skills_stop_safe_is_zero():
    skills = ReachGoalSkills()
    twist = skills.stop_safe()
    assert twist.linear.x == pytest.approx(0.0)
    assert twist.angular.z == pytest.approx(0.0)


def test_skills_commands_are_bounded():
    config = ReachGoalSkillConfig(max_linear_velocity=0.1, max_angular_velocity=0.5)
    skills = ReachGoalSkills(config)
    # Huge angle error must still clamp to the configured limits.
    twist = skills.approach_ball(make_state(ball_angle_rad=10.0, ball_radius_px=0.0))
    assert abs(twist.linear.x) <= 0.1 + 1e-9
    assert abs(twist.angular.z) <= 0.5 + 1e-9


# --- FSM transitions -------------------------------------------------------

def fresh(node, state):
    node.latest_state = state
    node.latest_state_time = time.monotonic()


def test_fsm_no_ball_searches_and_rotates():
    fsm = ReachGoalFsm()
    try:
        fresh(fsm, make_state(stale=False, ball_visible=False))
        fsm.state = ReachGoalFsm.SEARCH_BALL
        fsm.update_state(time.monotonic())
        assert fsm.state == ReachGoalFsm.SEARCH_BALL
        twist = fsm.command_for_state()
        assert twist.angular.z > 0.0
        assert twist.linear.x == pytest.approx(0.0)
    finally:
        fsm.destroy_node()


def test_fsm_visible_ball_approaches():
    fsm = ReachGoalFsm()
    try:
        fresh(fsm, make_state(stale=False, ball_visible=True, ball_radius_px=40.0))
        fsm.state = ReachGoalFsm.SEARCH_BALL
        fsm.update_state(time.monotonic())
        assert fsm.state == ReachGoalFsm.APPROACH_BALL
        assert fsm.command_for_state().linear.x > 0.0
    finally:
        fsm.destroy_node()


def test_fsm_controlled_ball_no_goal_searches_goal():
    fsm = ReachGoalFsm()
    try:
        fresh(fsm, make_state(
            stale=False,
            ball_visible=True,
            has_ball_control=True,
            goal_visible=False,
        ))
        fsm.state = ReachGoalFsm.CONTROL_BALL
        fsm.update_state(time.monotonic())
        assert fsm.state == ReachGoalFsm.SEARCH_GOAL
        twist = fsm.command_for_state()
        # Keeps a small forward push to hold the ball while scanning.
        assert twist.linear.x > 0.0
    finally:
        fsm.destroy_node()


def test_fsm_aligned_ball_and_goal_dribbles_forward():
    fsm = ReachGoalFsm()
    try:
        fresh(fsm, make_state(
            stale=False,
            ball_visible=True,
            has_ball_control=True,
            goal_visible=True,
            ball_goal_aligned=True,
        ))
        fsm.state = ReachGoalFsm.CONTROL_BALL
        fsm.update_state(time.monotonic())
        assert fsm.state == ReachGoalFsm.DRIBBLE_TO_GOAL
        assert fsm.command_for_state().linear.x > 0.0
    finally:
        fsm.destroy_node()


def test_fsm_uses_remembered_goal_to_keep_dribbling():
    fsm = ReachGoalFsm()
    try:
        fresh(fsm, make_state(
            stale=False,
            ball_visible=True,
            has_ball_control=True,
            goal_visible=False,
            goal_memory_active=True,
            ball_goal_aligned=True,
        ))
        fsm.state = ReachGoalFsm.SEARCH_GOAL
        fsm.update_state(time.monotonic())
        assert fsm.state == ReachGoalFsm.DRIBBLE_TO_GOAL

        fsm.update_state(time.monotonic())
        assert fsm.state == ReachGoalFsm.DRIBBLE_TO_GOAL
        assert fsm.command_for_state().linear.x > 0.0
    finally:
        fsm.destroy_node()


def test_fsm_dribble_goal_loss_enters_commit_to_goal():
    fsm = ReachGoalFsm()
    try:
        fresh(fsm, make_state(
            stale=False,
            ball_visible=True,
            has_ball_control=True,
            goal_visible=False,
            goal_memory_active=False,
            ball_angle_rad=0.0,
        ))
        fsm.state = ReachGoalFsm.DRIBBLE_TO_GOAL
        fsm.update_state(time.monotonic())
        assert fsm.state == ReachGoalFsm.COMMIT_TO_GOAL
        assert fsm.command_for_state().linear.x > 0.0
    finally:
        fsm.destroy_node()


def test_fsm_commit_to_goal_enters_goal_scored_and_stops():
    fsm = ReachGoalFsm()
    try:
        fresh(fsm, make_state(
            stale=False,
            ball_visible=True,
            has_ball_control=True,
            ball_angle_rad=0.0,
        ))
        fsm.state = ReachGoalFsm.COMMIT_TO_GOAL
        fsm.on_goal_scored(Bool(data=True))
        fsm.update_state(time.monotonic())
        assert fsm.state == ReachGoalFsm.GOAL_SCORED
        twist = fsm.command_for_state()
        assert twist.linear.x == pytest.approx(0.0)
        assert twist.angular.z == pytest.approx(0.0)
    finally:
        fsm.destroy_node()


def test_fsm_commit_to_goal_losing_control_recovers():
    fsm = ReachGoalFsm()
    try:
        fresh(fsm, make_state(
            stale=False,
            ball_visible=True,
            has_ball_control=False,
            ball_angle_rad=0.0,
        ))
        fsm.state = ReachGoalFsm.COMMIT_TO_GOAL
        fsm.update_state(time.monotonic())
        assert fsm.state == ReachGoalFsm.RECOVER_BALL
    finally:
        fsm.destroy_node()


def test_fsm_commit_to_goal_large_ball_angle_recovers():
    fsm = ReachGoalFsm()
    try:
        fresh(fsm, make_state(
            stale=False,
            ball_visible=True,
            has_ball_control=True,
            ball_angle_rad=fsm.commit_to_goal_max_ball_angle_rad + 0.1,
        ))
        fsm.state = ReachGoalFsm.COMMIT_TO_GOAL
        fsm.update_state(time.monotonic())
        assert fsm.state == ReachGoalFsm.RECOVER_BALL
    finally:
        fsm.destroy_node()


def test_fsm_commit_to_goal_times_out_to_search_goal():
    fsm = ReachGoalFsm()
    try:
        now = time.monotonic()
        fresh(fsm, make_state(
            stale=False,
            ball_visible=True,
            has_ball_control=True,
            ball_angle_rad=0.0,
            goal_visible=False,
            goal_memory_active=False,
        ))
        fsm.state = ReachGoalFsm.COMMIT_TO_GOAL
        fsm.state_entry_time = now - fsm.commit_to_goal_timeout_sec - 0.1
        fsm.update_state(now)
        assert fsm.state == ReachGoalFsm.SEARCH_GOAL
    finally:
        fsm.destroy_node()


def test_fsm_commit_to_goal_returns_to_dribble_when_goal_reappears_aligned():
    fsm = ReachGoalFsm()
    try:
        fresh(fsm, make_state(
            stale=False,
            ball_visible=True,
            has_ball_control=True,
            goal_visible=True,
            goal_memory_active=False,
            ball_goal_aligned=True,
            ball_angle_rad=0.0,
        ))
        fsm.state = ReachGoalFsm.COMMIT_TO_GOAL
        fsm.update_state(time.monotonic())
        assert fsm.state == ReachGoalFsm.DRIBBLE_TO_GOAL
    finally:
        fsm.destroy_node()


def test_fsm_enters_goal_scored_and_stops():
    fsm = ReachGoalFsm()
    try:
        fresh(fsm, make_state(
            stale=False,
            ball_visible=True,
            has_ball_control=True,
            goal_visible=True,
            ball_goal_aligned=True,
        ))
        fsm.state = ReachGoalFsm.DRIBBLE_TO_GOAL
        fsm.on_goal_scored(Bool(data=True))
        fsm.update_state(time.monotonic())
        assert fsm.state == ReachGoalFsm.GOAL_SCORED
        twist = fsm.command_for_state()
        assert twist.linear.x == pytest.approx(0.0)
        assert twist.angular.z == pytest.approx(0.0)

        fsm.update_state(time.monotonic())
        assert fsm.state == ReachGoalFsm.GOAL_SCORED
    finally:
        fsm.destroy_node()


def test_fsm_losing_control_recovers():
    fsm = ReachGoalFsm()
    try:
        fresh(fsm, make_state(
            stale=False,
            ball_visible=True,
            has_ball_control=False,
            goal_visible=True,
            ball_goal_aligned=True,
        ))
        fsm.state = ReachGoalFsm.DRIBBLE_TO_GOAL
        fsm.update_state(time.monotonic())
        assert fsm.state == ReachGoalFsm.RECOVER_BALL
    finally:
        fsm.destroy_node()


# --- Score monitor ---------------------------------------------------------

def make_pose(x, y=0.0, z=0.045):
    pose = Pose()
    pose.position.x = float(x)
    pose.position.y = float(y)
    pose.position.z = float(z)
    return pose


def make_pose_message(entity_name, x, y=0.0, z=0.045):
    transform = TransformStamped()
    transform.child_frame_id = entity_name
    transform.transform.translation.x = float(x)
    transform.transform.translation.y = float(y)
    transform.transform.translation.z = float(z)
    transform.transform.rotation.w = 1.0
    message = TFMessage()
    message.transforms.append(transform)
    return message


def test_score_zone_geometry():
    assert pose_inside_goal_zone(make_pose(1.70, 0.0), 1.68, 0.38, 0.20) is True
    assert pose_inside_goal_zone(make_pose(1.60, 0.0), 1.68, 0.38, 0.20) is False
    assert pose_inside_goal_zone(make_pose(1.70, 0.50), 1.68, 0.38, 0.20) is False
    assert pose_inside_goal_zone(make_pose(1.70, 0.0, 0.30), 1.68, 0.38, 0.20) is False


def test_score_monitor_requires_hold_time_and_latches():
    monitor = ReachGoalScoreMonitor()
    try:
        monitor.score_hold_time_sec = 0.15
        monitor.on_pose(make_pose(1.70, 0.0))
        start = time.monotonic()
        assert monitor.update_score(start) is False
        assert monitor.update_score(start + 0.20) is True

        monitor.on_pose(make_pose(1.20, 0.0))
        assert monitor.update_score(start + 0.30) is True
    finally:
        monitor.destroy_node()


def test_score_monitor_extracts_ball_from_world_pose_message():
    monitor = ReachGoalScoreMonitor()
    try:
        monitor.ball_entity_name = 'reach_goal_ball'
        monitor.on_world_pose(make_pose_message('some_other_entity', 1.70))
        assert monitor.latest_pose is None

        monitor.on_world_pose(make_pose_message('reach_goal_ball', 1.70, 0.12, 0.055))
        assert monitor.latest_pose is not None
        assert monitor.latest_pose.position.x == pytest.approx(1.70)
        assert monitor.latest_pose.position.y == pytest.approx(0.12)
    finally:
        monitor.destroy_node()


def test_fsm_stale_state_stops_safe():
    fsm = ReachGoalFsm()
    try:
        fresh(fsm, make_state(stale=True))
        fsm.state = ReachGoalFsm.DRIBBLE_TO_GOAL
        fsm.update_state(time.monotonic())
        assert fsm.state == ReachGoalFsm.STOP_SAFE
        twist = fsm.command_for_state()
        assert twist.linear.x == pytest.approx(0.0)
        assert twist.angular.z == pytest.approx(0.0)
    finally:
        fsm.destroy_node()


def test_fsm_recovers_from_stop_when_state_returns():
    fsm = ReachGoalFsm()
    try:
        fresh(fsm, make_state(stale=False, ball_visible=False))
        fsm.state = ReachGoalFsm.STOP_SAFE
        fsm.update_state(time.monotonic())
        assert fsm.state == ReachGoalFsm.SEARCH_BALL
    finally:
        fsm.destroy_node()


def test_fsm_no_fresh_message_stops_safe():
    fsm = ReachGoalFsm()
    try:
        # Never received a state message.
        fsm.state = ReachGoalFsm.SEARCH_BALL
        fsm.update_state(time.monotonic())
        assert fsm.state == ReachGoalFsm.STOP_SAFE
    finally:
        fsm.destroy_node()


if __name__ == '__main__':
    import sys
    sys.exit(pytest.main([__file__, '-v']))
