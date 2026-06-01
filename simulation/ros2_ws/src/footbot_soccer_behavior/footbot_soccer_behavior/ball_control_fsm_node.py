"""Compatibility wrapper for the relocated ball-control FSM node."""

from footbot_soccer_behavior.fsm.ball_control_fsm_node import BallControlFsm, main

__all__ = ['BallControlFsm', 'main']


if __name__ == '__main__':
    main()
