"""Reach-goal FSM.

Deterministic controller that drives one FootBot to push the ball toward a
visible goal. It consumes the image-derived ``BallGoalState`` and is the only
node that owns ``/cmd_vel`` in reach-goal mode. It never reads Gazebo poses.
"""

import time

import rclpy
from footbot_common.topics import (
    CMD_VEL,
    SOCCER_BALL_GOAL_STATE,
    SOCCER_GOAL_SCORED,
    SOCCER_REACH_GOAL_FSM_STATE,
)
from footbot_soccer_behavior.skills.reach_goal_skills import (
    ReachGoalSkillConfig,
    ReachGoalSkills,
)
from footbot_soccer_msgs.msg import BallGoalState
from geometry_msgs.msg import Twist
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from std_msgs.msg import Bool
from std_msgs.msg import String


class ReachGoalFsm(Node):
    SEARCH_BALL = 'SEARCH_BALL'
    APPROACH_BALL = 'APPROACH_BALL'
    CONTROL_BALL = 'CONTROL_BALL'
    SEARCH_GOAL = 'SEARCH_GOAL'
    ALIGN_BALL_TO_GOAL = 'ALIGN_BALL_TO_GOAL'
    DRIBBLE_TO_GOAL = 'DRIBBLE_TO_GOAL'
    COMMIT_TO_GOAL = 'COMMIT_TO_GOAL'
    RECOVER_BALL = 'RECOVER_BALL'
    STOP_SAFE = 'STOP_SAFE'
    GOAL_SCORED = 'GOAL_SCORED'

    # States that only make sense while the robot is holding the ball.
    BALL_CONTROL_STATES = (
        CONTROL_BALL,
        SEARCH_GOAL,
        ALIGN_BALL_TO_GOAL,
        DRIBBLE_TO_GOAL,
        COMMIT_TO_GOAL,
    )

    def __init__(self):
        super().__init__('reach_goal_fsm')

        self.declare_parameter('ball_goal_state_topic', SOCCER_BALL_GOAL_STATE)
        self.declare_parameter('cmd_vel_topic', CMD_VEL)
        self.declare_parameter('fsm_state_topic', SOCCER_REACH_GOAL_FSM_STATE)
        self.declare_parameter('goal_scored_topic', SOCCER_GOAL_SCORED)
        self.declare_parameter('update_rate', 20.0)
        self.declare_parameter('lost_state_timeout_sec', 0.7)
        self.declare_parameter('recover_duration_sec', 0.6)
        self.declare_parameter('emergency_stop', False)
        self.declare_parameter('max_linear_velocity', 0.14)
        self.declare_parameter('max_angular_velocity', 0.8)
        self.declare_parameter('search_ball_angular_velocity', 0.30)
        self.declare_parameter('approach_linear_velocity', 0.12)
        self.declare_parameter('approach_angular_kp', 0.9)
        self.declare_parameter('approach_slowdown_radius_px', 130.0)
        self.declare_parameter('approach_min_scale', 0.2)
        self.declare_parameter('control_linear_velocity', 0.05)
        self.declare_parameter('control_angular_kp', 0.5)
        self.declare_parameter('search_goal_linear_velocity', 0.03)
        self.declare_parameter('search_goal_angular_velocity', 0.25)
        self.declare_parameter('keep_ball_angular_kp', 0.3)
        self.declare_parameter('align_linear_velocity', 0.035)
        self.declare_parameter('align_angular_kp', 0.6)
        self.declare_parameter('dribble_linear_velocity', 0.07)
        self.declare_parameter('dribble_angular_kp', 0.5)
        self.declare_parameter('commit_to_goal_enabled', True)
        self.declare_parameter('commit_to_goal_timeout_sec', 4.0)
        self.declare_parameter('commit_to_goal_linear_velocity', 0.06)
        self.declare_parameter('commit_to_goal_ball_angular_kp', 0.45)
        self.declare_parameter('commit_to_goal_max_ball_angle_rad', 0.35)
        self.declare_parameter('commit_to_goal_requires_ball_visible', True)
        self.declare_parameter('recover_reverse_velocity', -0.05)
        self.declare_parameter('recover_angular_velocity', 0.3)
        self.declare_parameter('acceleration_smoothing_alpha', 0.35)

        self.ball_goal_state_topic = self.get_parameter('ball_goal_state_topic').value
        self.cmd_vel_topic = self.get_parameter('cmd_vel_topic').value
        self.fsm_state_topic = self.get_parameter('fsm_state_topic').value
        self.goal_scored_topic = self.get_parameter('goal_scored_topic').value
        self.update_rate = float(self.get_parameter('update_rate').value)
        self.lost_state_timeout_sec = float(
            self.get_parameter('lost_state_timeout_sec').value
        )
        self.recover_duration_sec = float(
            self.get_parameter('recover_duration_sec').value
        )
        self.commit_to_goal_timeout_sec = float(
            self.get_parameter('commit_to_goal_timeout_sec').value
        )
        self.commit_to_goal_max_ball_angle_rad = float(
            self.get_parameter('commit_to_goal_max_ball_angle_rad').value
        )

        config = ReachGoalSkillConfig(
            max_linear_velocity=float(self.get_parameter('max_linear_velocity').value),
            max_angular_velocity=float(self.get_parameter('max_angular_velocity').value),
            search_ball_angular_velocity=float(
                self.get_parameter('search_ball_angular_velocity').value
            ),
            approach_linear_velocity=float(
                self.get_parameter('approach_linear_velocity').value
            ),
            approach_angular_kp=float(self.get_parameter('approach_angular_kp').value),
            approach_slowdown_radius_px=float(
                self.get_parameter('approach_slowdown_radius_px').value
            ),
            approach_min_scale=float(self.get_parameter('approach_min_scale').value),
            control_linear_velocity=float(
                self.get_parameter('control_linear_velocity').value
            ),
            control_angular_kp=float(self.get_parameter('control_angular_kp').value),
            search_goal_linear_velocity=float(
                self.get_parameter('search_goal_linear_velocity').value
            ),
            search_goal_angular_velocity=float(
                self.get_parameter('search_goal_angular_velocity').value
            ),
            keep_ball_angular_kp=float(self.get_parameter('keep_ball_angular_kp').value),
            align_linear_velocity=float(
                self.get_parameter('align_linear_velocity').value
            ),
            align_angular_kp=float(self.get_parameter('align_angular_kp').value),
            dribble_linear_velocity=float(
                self.get_parameter('dribble_linear_velocity').value
            ),
            dribble_angular_kp=float(self.get_parameter('dribble_angular_kp').value),
            commit_to_goal_linear_velocity=float(
                self.get_parameter('commit_to_goal_linear_velocity').value
            ),
            commit_to_goal_ball_angular_kp=float(
                self.get_parameter('commit_to_goal_ball_angular_kp').value
            ),
            recover_reverse_velocity=float(
                self.get_parameter('recover_reverse_velocity').value
            ),
            recover_angular_velocity=float(
                self.get_parameter('recover_angular_velocity').value
            ),
            acceleration_smoothing_alpha=float(
                self.get_parameter('acceleration_smoothing_alpha').value
            ),
        )
        self.skills = ReachGoalSkills(config)

        self.latest_state = BallGoalState()
        self.latest_state.stale = True
        self.latest_state_time = None
        self.goal_scored = False
        self.state = self.SEARCH_BALL
        self.state_entry_time = time.monotonic()

        self.cmd_vel_publisher = self.create_publisher(Twist, self.cmd_vel_topic, 10)
        self.fsm_state_publisher = self.create_publisher(
            String, self.fsm_state_topic, 10
        )
        self.state_subscription = self.create_subscription(
            BallGoalState,
            self.ball_goal_state_topic,
            self.on_state,
            10,
        )
        self.goal_scored_subscription = self.create_subscription(
            Bool,
            self.goal_scored_topic,
            self.on_goal_scored,
            10,
        )
        self.timer = self.create_timer(
            1.0 / max(self.update_rate, 1.0),
            self.tick,
        )
        self.get_logger().info(
            f'Reach-goal FSM listening on {self.ball_goal_state_topic}; '
            f'publishing {self.cmd_vel_topic}'
        )

    def on_state(self, message):
        self.latest_state = message
        self.latest_state_time = time.monotonic()

    def on_goal_scored(self, message):
        if message.data:
            self.goal_scored = True

    def tick(self):
        now = time.monotonic()
        self.update_state(now)
        desired = self.command_for_state()
        if self.state in (self.STOP_SAFE, self.GOAL_SCORED):
            command = desired
            self.skills.reset()
        else:
            command = self.skills.smooth(desired)
        self.cmd_vel_publisher.publish(command)
        self.fsm_state_publisher.publish(String(data=self.state))

    def update_state(self, now):
        if self.goal_scored:
            self.transition(self.GOAL_SCORED, now)
            return

        if self.state == self.GOAL_SCORED:
            return

        if bool(self.get_parameter('emergency_stop').value):
            self.transition(self.STOP_SAFE, now)
            return

        # Safety first: if perception is stale, stop. Recover into the search
        # state once fresh detections return.
        if self.is_state_lost(now):
            self.transition(self.STOP_SAFE, now)
            return
        if self.state == self.STOP_SAFE:
            self.transition(self.SEARCH_BALL, now)
            return

        state = self.latest_state

        # Losing ball control from any holding state drops back to recovery.
        if self.state in self.BALL_CONTROL_STATES and not state.has_ball_control:
            self.transition(self.RECOVER_BALL, now)
            return

        if self.state == self.SEARCH_BALL:
            if state.ball_visible:
                self.transition(self.APPROACH_BALL, now)
            return

        if self.state == self.APPROACH_BALL:
            if not state.ball_visible:
                self.transition(self.SEARCH_BALL, now)
            elif state.has_ball_control:
                self.transition(self.CONTROL_BALL, now)
            return

        if self.state == self.CONTROL_BALL:
            self.transition(self.goal_phase_target(state), now)
            return

        if self.state == self.SEARCH_GOAL:
            if self.goal_known(state):
                self.transition(self.goal_phase_target(state), now)
            return

        if self.state == self.ALIGN_BALL_TO_GOAL:
            if not self.goal_known(state):
                self.transition(self.SEARCH_GOAL, now)
            elif state.ball_goal_aligned:
                self.transition(self.DRIBBLE_TO_GOAL, now)
            return

        if self.state == self.DRIBBLE_TO_GOAL:
            if not self.goal_known(state):
                if self.can_commit_to_goal(state):
                    self.transition(self.COMMIT_TO_GOAL, now)
                else:
                    self.transition(self.SEARCH_GOAL, now)
            elif not state.ball_goal_aligned:
                self.transition(self.ALIGN_BALL_TO_GOAL, now)
            return

        if self.state == self.COMMIT_TO_GOAL:
            if self.goal_known(state) and state.ball_goal_aligned:
                self.transition(self.DRIBBLE_TO_GOAL, now)
            elif not self.can_continue_commit_to_goal(state):
                self.transition(self.RECOVER_BALL, now)
            elif now - self.state_entry_time >= self.commit_to_goal_timeout_sec:
                self.transition(self.SEARCH_GOAL, now)
            return

        if self.state == self.RECOVER_BALL:
            if now - self.state_entry_time >= self.recover_duration_sec:
                if state.ball_visible:
                    self.transition(self.APPROACH_BALL, now)
                else:
                    self.transition(self.SEARCH_BALL, now)
            return

    def goal_phase_target(self, state):
        # Shared decision for "I have the ball": chase the goal in the right
        # sub-state given current visibility and alignment.
        if not self.goal_known(state):
            return self.SEARCH_GOAL
        if state.ball_goal_aligned:
            return self.DRIBBLE_TO_GOAL
        return self.ALIGN_BALL_TO_GOAL

    @staticmethod
    def goal_known(state):
        return bool(state.goal_visible or state.goal_memory_active)

    def can_commit_to_goal(self, state):
        if not bool(self.get_parameter('commit_to_goal_enabled').value):
            return False
        return self.can_continue_commit_to_goal(state)

    def can_continue_commit_to_goal(self, state):
        requires_ball_visible = bool(
            self.get_parameter('commit_to_goal_requires_ball_visible').value
        )
        if requires_ball_visible and not state.ball_visible:
            return False
        if not state.has_ball_control:
            return False
        return abs(float(state.ball_angle_rad)) <= self.commit_to_goal_max_ball_angle_rad

    def command_for_state(self):
        state = self.latest_state
        if self.state == self.SEARCH_BALL:
            return self.skills.search_ball(state)
        if self.state == self.APPROACH_BALL:
            return self.skills.approach_ball(state)
        if self.state == self.CONTROL_BALL:
            return self.skills.control_ball(state)
        if self.state == self.SEARCH_GOAL:
            return self.skills.search_goal(state)
        if self.state == self.ALIGN_BALL_TO_GOAL:
            return self.skills.align_ball_to_goal(state)
        if self.state == self.DRIBBLE_TO_GOAL:
            return self.skills.dribble_to_goal(state)
        if self.state == self.COMMIT_TO_GOAL:
            return self.skills.commit_to_goal(state)
        if self.state == self.RECOVER_BALL:
            return self.skills.recover_ball(state)
        return self.skills.stop_safe()

    def is_state_lost(self, now):
        if self.latest_state_time is None:
            return True
        if now - self.latest_state_time > self.lost_state_timeout_sec:
            return True
        return bool(self.latest_state.stale)

    def transition(self, next_state, now):
        if self.state == next_state:
            return
        previous = self.state
        self.state = next_state
        self.state_entry_time = now
        self.get_logger().info(f'{previous} -> {next_state}')

    def shutdown(self):
        try:
            if rclpy.ok():
                # Never leave a nonzero velocity command active after shutdown.
                self.cmd_vel_publisher.publish(Twist())
                self.get_logger().info('Stopping Reach-goal FSM.')
        except Exception:
            pass


def main(args=None):
    rclpy.init(args=args)
    node = None
    try:
        node = ReachGoalFsm()
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        if node is not None:
            node.shutdown()
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
