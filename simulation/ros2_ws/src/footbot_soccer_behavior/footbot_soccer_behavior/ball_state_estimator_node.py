"""Compatibility wrapper for the relocated ball state estimator node."""

from footbot_soccer_behavior.state_estimation.ball_state_estimator_node import (
    BallStateEstimator,
    main,
)

__all__ = ['BallStateEstimator', 'main']


if __name__ == '__main__':
    main()
