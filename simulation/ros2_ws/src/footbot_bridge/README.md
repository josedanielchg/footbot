# footbot_bridge

Compatibility bridge package for the Footbot simulation.

The bridge exposes an ESP32-compatible HTTP API and publishes ROS 2 velocity
commands to the simulated robot.

## Endpoint

Default server:

```text
http://127.0.0.1:8080
```

Supported endpoints:

- `POST /move`: receive legacy movement commands and publish `Twist`.
- `GET /status`: return bridge state and the last published command.

## Movement Commands

Valid directions:

```text
forward
backward
left
right
soft_left
soft_right
stop
```

Example:

```bash
curl -s -X POST http://127.0.0.1:8080/move \
  -H 'Content-Type: application/json' \
  -d '{"direction":"forward","speed":150}'
```

Soft turns may include `turn_ratio`:

```bash
curl -s -X POST http://127.0.0.1:8080/move \
  -H 'Content-Type: application/json' \
  -d '{"direction":"soft_left","speed":180,"turn_ratio":0.4}'
```

## ROS Output

Default output topic:

```text
/cmd_vel
```

The node converts the ESP32-style speed range `0-255` into bounded
`geometry_msgs/msg/Twist` values.

## Manual Control Testing

To test the existing `manual_control/` app with the simulator, point its move
endpoint at:

```text
http://127.0.0.1:8080/move
```

Do not commit local `manual_control/` configuration changes used only for this
test.
