import time

import rclpy
from footbot_soccer_behavior.skills.ball_control_skills import (
    BallControlSkillConfig,
    BallControlSkills,
)
from footbot_soccer_msgs.msg import BallState
from geometry_msgs.msg import Twist
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from std_msgs.msg import String


class BallControlFsm(Node):
    SEARCH_BALL = 'SEARCH_BALL'
    ALIGN_TO_BALL = 'ALIGN_TO_BALL'
    APPROACH_BALL = 'APPROACH_BALL'
    CONTACT_BALL = 'CONTACT_BALL'
    CONTROL_BALL = 'CONTROL_BALL'
    ROTATE_WITH_BALL = 'ROTATE_WITH_BALL'
    RECOVER_BALL = 'RECOVER_BALL'
    STOP_SAFE = 'STOP_SAFE'

    def __init__(self):
        super().__init__('ball_control_fsm')

        self.declare_parameter('ball_state_topic', '/soccer/ball_state')
        self.declare_parameter('cmd_vel_topic', '/cmd_vel')
        self.declare_parameter('fsm_state_topic', '/soccer/fsm_state')
        self.declare_parameter('update_rate', 20.0)
        self.declare_parameter('lost_ball_timeout_sec', 0.7)
        self.declare_parameter('recover_duration_sec', 0.5)
        self.declare_parameter('contact_timeout_sec', 2.0)
        self.declare_parameter('control_min_duration_sec', 0.5)
        self.declare_parameter('rotate_with_ball_enabled', True)
        self.declare_parameter('rotate_duration_sec', 2.0)
        self.declare_parameter('emergency_stop', False)
        self.declare_parameter('max_linear_velocity', 0.14)
        self.declare_parameter('max_angular_velocity', 0.8)
        self.declare_parameter('search_angular_velocity', 0.25)
        self.declare_parameter('approach_linear_velocity', 0.12)
        self.declare_parameter('contact_linear_velocity', 0.045)
        self.declare_parameter('control_linear_velocity', 0.055)
        self.declare_parameter('rotate_with_ball_angular_velocity', 0.22)
        self.declare_parameter('recover_reverse_velocity', -0.04)
        self.declare_parameter('angular_kp', 0.9)
        self.declare_parameter('linear_kp', 0.16)
        self.declare_parameter('acceleration_smoothing_alpha', 0.35)

        self.ball_state_topic = self.get_parameter('ball_state_topic').value
        self.cmd_vel_topic = self.get_parameter('cmd_vel_topic').value
        self.fsm_state_topic = self.get_parameter('fsm_state_topic').value
        self.update_rate = float(self.get_parameter('update_rate').value)
        self.lost_ball_timeout_sec = float(
            self.get_parameter('lost_ball_timeout_sec').value
        )
        self.recover_duration_sec = float(
            self.get_parameter('recover_duration_sec').value
        )
        self.contact_timeout_sec = float(
            self.get_parameter('contact_timeout_sec').value
        )
        self.control_min_duration_sec = float(
            self.get_parameter('control_min_duration_sec').value
        )
        self.rotate_with_ball_enabled = bool(
            self.get_parameter('rotate_with_ball_enabled').value
        )
        self.rotate_duration_sec = float(
            self.get_parameter('rotate_duration_sec').value
        )

        config = BallControlSkillConfig(
            max_linear_velocity=float(self.get_parameter('max_linear_velocity').value),
            max_angular_velocity=float(self.get_parameter('max_angular_velocity').value),
            search_angular_velocity=float(
                self.get_parameter('search_angular_velocity').value
            ),
            approach_linear_velocity=float(
                self.get_parameter('approach_linear_velocity').value
            ),
            contact_linear_velocity=float(
                self.get_parameter('contact_linear_velocity').value
            ),
            control_linear_velocity=float(
                self.get_parameter('control_linear_velocity').value
            ),
            rotate_with_ball_angular_velocity=float(
                self.get_parameter('rotate_with_ball_angular_velocity').value
            ),
            recover_reverse_velocity=float(
                self.get_parameter('recover_reverse_velocity').value
            ),
            angular_kp=float(self.get_parameter('angular_kp').value),
            linear_kp=float(self.get_parameter('linear_kp').value),
            acceleration_smoothing_alpha=float(
                self.get_parameter('acceleration_smoothing_alpha').value
            ),
        )
        self.skills = BallControlSkills(config)

        self.latest_ball_state = BallState()
        self.latest_ball_state.stale = True
        self.latest_ball_state_time = None
        self.state = self.SEARCH_BALL
        self.state_entry_time = time.monotonic()
        self.first_detection_time = None
        self.contact_entry_time = None
        self.control_entry_time = None
        self.lost_ball_count = 0
        self.successful_contact_count = 0

        self.cmd_vel_publisher = self.create_publisher(Twist, self.cmd_vel_topic, 10)
        self.state_publisher = self.create_publisher(String, self.fsm_state_topic, 10)
        self.ball_state_subscription = self.create_subscription(
            BallState,
            self.ball_state_topic,
            self.on_ball_state,
            10,
        )
        self.timer = self.create_timer(
            1.0 / max(self.update_rate, 1.0),
            self.tick,
        )
        self.get_logger().info(
            f'Ball-control FSM listening on {self.ball_state_topic}; publishing {self.cmd_vel_topic}'
        )

    def on_ball_state(self, message):
        self.latest_ball_state = message
        self.latest_ball_state_time = time.monotonic()
        if message.visible and not message.stale and self.first_detection_time is None:
            self.first_detection_time = self.latest_ball_state_time
            self.get_logger().info('First ball detection received')

    def tick(self):
        now = time.monotonic()
        self.update_state(now)
        desired = self.command_for_state()
        if self.state == self.STOP_SAFE:
            command = desired
            self.skills.reset()
        else:
            command = self.skills.smooth(desired)
        self.cmd_vel_publisher.publish(command)
        self.state_publisher.publish(String(data=self.state))

    def update_state(self, now):
        if bool(self.get_parameter('emergency_stop').value):
            self.transition(self.STOP_SAFE, now)
            return

        ball = self.latest_ball_state
        ball_lost = self.is_ball_lost(now)

        if self.state != self.STOP_SAFE and ball_lost:
            if self.state != self.SEARCH_BALL:
                self.lost_ball_count += 1
            self.transition(self.SEARCH_BALL, now)
            return

        if self.state == self.SEARCH_BALL:
            if self.ball_visible():
                self.transition(self.ALIGN_TO_BALL, now)
            return

        if self.state == self.ALIGN_TO_BALL:
            if ball.centered and ball.near:
                self.transition(self.CONTACT_BALL, now)
            elif ball.centered:
                self.transition(self.APPROACH_BALL, now)
            return

        if self.state == self.APPROACH_BALL:
            if not ball.centered:
                self.transition(self.ALIGN_TO_BALL, now)
            elif ball.contact_ready:
                self.transition(self.CONTACT_BALL, now)
            return

        if self.state == self.CONTACT_BALL:
            if ball.has_control:
                self.successful_contact_count += 1
                self.control_entry_time = now
                self.transition(self.CONTROL_BALL, now)
            elif now - self.state_entry_time > self.contact_timeout_sec:
                self.transition(self.RECOVER_BALL, now)
            return

        if self.state == self.CONTROL_BALL:
            if not ball.centered or not ball.near:
                self.transition(self.RECOVER_BALL, now)
            elif (
                self.rotate_with_ball_enabled
                and self.control_entry_time is not None
                and now - self.control_entry_time >= self.control_min_duration_sec
            ):
                self.transition(self.ROTATE_WITH_BALL, now)
            return

        if self.state == self.ROTATE_WITH_BALL:
            if not ball.has_control:
                self.transition(self.RECOVER_BALL, now)
            elif now - self.state_entry_time >= self.rotate_duration_sec:
                self.control_entry_time = now
                self.transition(self.CONTROL_BALL, now)
            return

        if self.state == self.RECOVER_BALL:
            if now - self.state_entry_time >= self.recover_duration_sec:
                if self.ball_visible():
                    self.transition(self.ALIGN_TO_BALL, now)
                else:
                    self.transition(self.SEARCH_BALL, now)

    def command_for_state(self):
        ball = self.latest_ball_state
        if self.state == self.SEARCH_BALL:
            return self.skills.search_ball(ball)
        if self.state == self.ALIGN_TO_BALL:
            return self.skills.align_to_ball(ball)
        if self.state == self.APPROACH_BALL:
            return self.skills.approach_ball(ball)
        if self.state == self.CONTACT_BALL:
            return self.skills.contact_ball(ball)
        if self.state == self.CONTROL_BALL:
            return self.skills.control_ball(ball)
        if self.state == self.ROTATE_WITH_BALL:
            return self.skills.rotate_with_ball(ball)
        if self.state == self.RECOVER_BALL:
            return self.skills.recover_ball(ball)
        return self.skills.stop_safe()

    def ball_visible(self):
        ball = self.latest_ball_state
        return bool(ball.visible and not ball.stale)

    def is_ball_lost(self, now):
        if self.latest_ball_state_time is None:
            return True
        if now - self.latest_ball_state_time > self.lost_ball_timeout_sec:
            return True
        return not self.ball_visible()

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
                self.cmd_vel_publisher.publish(Twist())
                self.get_logger().info(
                    'Stopping ball-control FSM. '
                    f'lost_ball_count={self.lost_ball_count}, '
                    f'successful_contact_count={self.successful_contact_count}'
                )
        except Exception:
            pass


def main(args=None):
    rclpy.init(args=args)
    node = None
    try:
        node = BallControlFsm()
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
