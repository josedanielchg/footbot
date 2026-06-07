# Planned Soccer Stages

Ball control and the Reach-goal behavior are currently implemented.

## Implemented Now

### Ball Control

The robot detects the orange ball, aligns, approaches, contacts, keeps the ball
in a frontal control zone, and rotates slowly while maintaining control.

### Reach The Goal With The Ball

The robot keeps ball control while pushing the ball toward a YOLO-detected goal.
It reuses the perception-driven pattern: a `BallGoalState` estimator, bounded
skills, and an FSM that owns `/cmd_vel`. See [reach-goal.md](reach-goal.md).

## Planned Later

### Steal The Ball From An Opponent

The robot should detect an opponent or robot that has possession and try to take
the ball. This requires reliable opponent perception and new behavior states.

### Team Play

The intended long-term format is three robots per side. Future approaches may
include FSM roles, heuristic tactics, RL/MARL policies, MCTS/SPO-style planning,
or combinations of these.

## Rule For Future Work

Do not mix experimental policy code with stable launch modes. New behavior
stages should have separate launch files, clear `/cmd_vel` ownership, and docs
that label them as experimental until validated.
