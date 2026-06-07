"""Bounded low-level Twist generators for the Reach-goal FSM.

Each method maps a ``BallGoalState`` to a single bounded ``Twist``. Skills never
decide transitions; the FSM owns the state machine and only asks a skill for the
command of the current state. All commands are clamped to configured limits.
"""

from dataclasses import dataclass

from footbot_common.math_utils import clamp
from geometry_msgs.msg import Twist


@dataclass
class ReachGoalSkillConfig:
    max_linear_velocity: float = 0.14
    max_angular_velocity: float = 0.8
    search_ball_angular_velocity: float = 0.30
    approach_linear_velocity: float = 0.12
    approach_angular_kp: float = 0.9
    approach_slowdown_radius_px: float = 130.0
    approach_min_scale: float = 0.2
    control_linear_velocity: float = 0.05
    control_angular_kp: float = 0.5
    search_goal_linear_velocity: float = 0.03
    search_goal_angular_velocity: float = 0.25
    keep_ball_angular_kp: float = 0.3
    align_linear_velocity: float = 0.035
    align_angular_kp: float = 0.6
    dribble_linear_velocity: float = 0.07
    dribble_angular_kp: float = 0.5
    recover_reverse_velocity: float = -0.05
    recover_angular_velocity: float = 0.3
    acceleration_smoothing_alpha: float = 0.35


class ReachGoalSkills:
    def __init__(self, config=None):
        self.config = config or ReachGoalSkillConfig()
        self.previous_twist = Twist()

    def search_ball(self, _state):
        # No ball in view: rotate in place to scan for it.
        twist = Twist()
        twist.angular.z = self.config.search_ball_angular_velocity
        return self._bounded(twist)

    def approach_ball(self, state):
        # Drive toward the ball, slowing as it grows in the frame so we make
        # gentle contact instead of knocking it away.
        twist = Twist()
        radius = max(float(state.ball_radius_px), 0.0)
        slowdown = max(self.config.approach_slowdown_radius_px, 1.0)
        scale = clamp(1.0 - radius / slowdown, self.config.approach_min_scale, 1.0)
        twist.linear.x = self.config.approach_linear_velocity * scale
        twist.angular.z = -self.config.approach_angular_kp * float(state.ball_angle_rad)
        return self._bounded(twist)

    def control_ball(self, state):
        # Ball is in the frontal control zone: nudge forward while keeping it
        # centered.
        twist = Twist()
        twist.linear.x = self.config.control_linear_velocity
        twist.angular.z = -self.config.control_angular_kp * float(state.ball_angle_rad)
        return self._bounded(twist)

    def search_goal(self, state):
        # Ball controlled but goal not seen: rotate slowly to find the goal
        # while keeping the controlled ball from drifting out of frame.
        twist = Twist()
        twist.linear.x = self.config.search_goal_linear_velocity
        twist.angular.z = (
            self.config.search_goal_angular_velocity
            - self.config.keep_ball_angular_kp * float(state.ball_angle_rad)
        )
        return self._bounded(twist)

    def align_ball_to_goal(self, state):
        # Turn the robot (and the ball it is pushing) toward the goal bearing,
        # with a small forward push so the ball stays in contact.
        twist = Twist()
        twist.linear.x = self.config.align_linear_velocity
        twist.angular.z = (
            -self.config.align_angular_kp * float(state.goal_angle_rad)
            - self.config.keep_ball_angular_kp * float(state.ball_angle_rad)
        )
        return self._bounded(twist)

    def dribble_to_goal(self, state):
        # Ball lined up with the goal: drive forward, correcting heading toward
        # the goal while keeping the ball centered.
        twist = Twist()
        twist.linear.x = self.config.dribble_linear_velocity
        twist.angular.z = (
            -self.config.dribble_angular_kp * float(state.goal_angle_rad)
            - self.config.keep_ball_angular_kp * float(state.ball_angle_rad)
        )
        return self._bounded(twist)

    def recover_ball(self, state):
        # Lost control: back off slightly and turn toward the ball if visible,
        # otherwise rotate to search.
        twist = Twist()
        twist.linear.x = self.config.recover_reverse_velocity
        if getattr(state, 'ball_visible', False) and not getattr(state, 'stale', True):
            twist.angular.z = -self.config.control_angular_kp * float(state.ball_angle_rad)
        else:
            twist.angular.z = self.config.recover_angular_velocity
        return self._bounded(twist)

    def stop_safe(self):
        return Twist()

    def smooth(self, desired):
        alpha = clamp(self.config.acceleration_smoothing_alpha, 0.0, 1.0)
        smoothed = Twist()
        smoothed.linear.x = (
            alpha * desired.linear.x + (1.0 - alpha) * self.previous_twist.linear.x
        )
        smoothed.angular.z = (
            alpha * desired.angular.z + (1.0 - alpha) * self.previous_twist.angular.z
        )
        smoothed = self._bounded(smoothed)
        self.previous_twist = smoothed
        return smoothed

    def reset(self):
        self.previous_twist = Twist()

    def _bounded(self, twist):
        bounded = Twist()
        bounded.linear.x = clamp(
            twist.linear.x,
            -self.config.max_linear_velocity,
            self.config.max_linear_velocity,
        )
        bounded.angular.z = clamp(
            twist.angular.z,
            -self.config.max_angular_velocity,
            self.config.max_angular_velocity,
        )
        return bounded
