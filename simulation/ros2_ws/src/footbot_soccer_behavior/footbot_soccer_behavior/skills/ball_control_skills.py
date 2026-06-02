from dataclasses import dataclass

from footbot_common.math_utils import clamp
from geometry_msgs.msg import Twist


@dataclass
class BallControlSkillConfig:
    max_linear_velocity: float = 0.14
    max_angular_velocity: float = 0.8
    search_angular_velocity: float = 0.25
    approach_linear_velocity: float = 0.12
    contact_linear_velocity: float = 0.045
    control_linear_velocity: float = 0.055
    rotate_with_ball_angular_velocity: float = 0.22
    recover_reverse_velocity: float = -0.04
    angular_kp: float = 0.9
    linear_kp: float = 0.16
    acceleration_smoothing_alpha: float = 0.35


class BallControlSkills:
    def __init__(self, config=None):
        self.config = config or BallControlSkillConfig()
        self.previous_twist = Twist()

    def search_ball(self, _ball_state):
        twist = Twist()
        twist.angular.z = self.config.search_angular_velocity
        return self._bounded(twist)

    def align_to_ball(self, ball_state):
        twist = Twist()
        twist.angular.z = -self.config.angular_kp * float(ball_state.angle_rad)
        return self._bounded(twist)

    def approach_ball(self, ball_state):
        twist = Twist()
        distance_scale = clamp((float(ball_state.distance_m) - 0.22) / 0.5, 0.25, 1.0)
        twist.linear.x = min(
            self.config.approach_linear_velocity,
            self.config.linear_kp * distance_scale,
        )
        twist.angular.z = -self.config.angular_kp * float(ball_state.angle_rad)
        return self._bounded(twist)

    def contact_ball(self, ball_state):
        twist = Twist()
        twist.linear.x = self.config.contact_linear_velocity
        twist.angular.z = -0.45 * self.config.angular_kp * float(ball_state.angle_rad)
        return self._bounded(twist)

    def control_ball(self, ball_state):
        twist = Twist()
        twist.linear.x = self.config.control_linear_velocity
        twist.angular.z = -0.35 * self.config.angular_kp * float(ball_state.angle_rad)
        return self._bounded(twist)

    def rotate_with_ball(self, _ball_state):
        twist = Twist()
        twist.linear.x = min(self.config.control_linear_velocity, 0.04)
        twist.angular.z = self.config.rotate_with_ball_angular_velocity
        return self._bounded(twist)

    def recover_ball(self, ball_state):
        twist = Twist()
        if getattr(ball_state, 'visible', False) and not getattr(ball_state, 'stale', True):
            twist.angular.z = -0.5 * self.config.angular_kp * float(ball_state.angle_rad)
        else:
            twist.angular.z = self.config.search_angular_velocity
        twist.linear.x = self.config.recover_reverse_velocity
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
