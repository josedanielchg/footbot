# Planned Soccer Stages

This roadmap describes where the simulated soccer stack is going. The stable
baseline is intentionally deterministic: perception topics feed state
estimators, state estimators feed finite-state machines, and exactly one
controller owns `/cmd_vel` in each launch mode.

## Implemented Foundations

### Ball Control

Goal: prove that one FootBot can find, approach, contact, and keep the orange
ball in a frontal control zone.

Current behavior:

- Uses the HSV ball detector from `footbot_perception`.
- Converts `Detection2D` into `BallState`.
- Runs a deterministic FSM with search, align, approach, contact, control,
  rotate-with-ball, recover, and safe-stop states.
- Provides single-scenario and multi-lane validation worlds.

Validation focus:

- The robot should not move without fresh ball state.
- The ball should remain close enough for controlled contact.
- Multi-lane tests should isolate topics so several scenarios can run in one
  Gazebo session.

### Reach Goal

Goal: push the ball toward a visible goal using robot-camera perception.

Current behavior:

- Uses a YOLO `ball` + `goal` detector.
- Converts `Detection2DArray` into `BallGoalState`.
- Keeps short temporal goal memory when the goal disappears near the mouth.
- Uses `COMMIT_TO_GOAL` to keep a slow, ball-centered push after close-range
  goal dropouts, without using Gazebo poses for navigation.
- Uses `reach_goal_fsm` as the only `/cmd_vel` owner.
- Uses `reach_goal_score_monitor` as simulation referee logic to stop after a
  score.

Validation focus:

- The model should detect both ball and goal in the initial approach.
- Goal memory should bridge short YOLO dropouts while the ball remains
  controlled.
- `COMMIT_TO_GOAL` should carry the final push when the goal disappears near
  the mouth, then stop once `/soccer/goal_scored` fires.
- `/soccer/goal_scored` should stop the robot once the ball enters the goal
  zone.

## Next: Goal-Directed Dribbling Improvements

Objective: make Reach Goal more reliable before adding opponents.

Ideas for implementation:

- Add more near-goal images to the dataset, especially when the goal posts are
  partially visible or the goal mouth fills the frame.
- Improve goal reacquisition after temporary loss by combining temporal memory
  with a gentle scan behavior that preserves ball control.
- Replace the current commit fallback with stronger close-range perception once
  the dataset includes enough near-goal examples.
- Tune dribble speed, angular gain, and recovery duration so the robot pushes
  the ball instead of overshooting it.
- Add recovery paths for common failures: ball slips left/right, ball gets stuck
  near a post, or the robot reaches the goal without the ball.
- Track simple metrics such as time to first control, time to score, goal-memory
  duration, lost-control count, and final ball pose.

Expected launch shape:

- Keep a dedicated Reach Goal launch.
- Keep `/cmd_vel` owned by `reach_goal_fsm`.
- Keep scoring as simulation referee logic, not robot perception.

## Planned: Opponent Interaction

Objective: detect an opponent with the ball and challenge for possession without
destabilizing the baseline behaviors.

Ideas for implementation:

- Use the soccer vision package to detect `opponent`, `robot`, or `teammate`
  classes from the robot camera.
- Add an image-derived possession estimate: ball close to opponent, ball close
  to self, or ball free.
- Start with static or scripted opponent robots before adding active opponents.
- Add FSM states for observe, approach-opponent, challenge-ball, recover-ball,
  and stop-safe.
- Keep collision and safety behavior conservative; the first version should
  challenge slowly and recover cleanly.

Validation focus:

- The robot should never use Gazebo opponent poses for decision making.
- Opponent detection should not publish movement commands directly.
- Opponent launch modes should be separate from Ball Control and Reach Goal.

## Planned: Team Play

Objective: support three robots per side with clear roles and isolated command
ownership.

Ideas for implementation:

- Define roles such as goalkeeper, defender, and attacker.
- Start with fixed formations around the center ball and goals.
- Add per-robot namespaces for camera topics, detections, state, FSM state, and
  `/cmd_vel`.
- Share only high-level information at first, such as "ball visible", "goal
  visible", "robot has control", or "role target".
- Explore simple passing behavior after each robot can independently control
  and approach the ball.

Validation focus:

- Every robot should have exactly one command owner.
- Namespaces must prevent camera, detection, and `/cmd_vel` topic collisions.
- Team behavior should still allow single-robot modes to run unchanged.

## Research Tracks

Objective: compare tactical methods only after deterministic baselines are
measurable.

Candidate approaches:

- Heuristic FSMs for predictable first tactics.
- Behavior trees if FSM transitions become difficult to maintain.
- MCTS or SPO-style planning for short-horizon tactical choices.
- RL or MARL only after the simulation has stable reset, scoring, metrics, and
  reproducible scenarios.

Rules for experiments:

- Keep research policies in separate launch modes.
- Do not replace deterministic baselines until a new method is easier to debug
  and measurably better.
- Log metrics and failure cases before adding more complex policy code.
