import json
import math
import threading
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node


VALID_DIRECTIONS = {
    'forward',
    'backward',
    'left',
    'right',
    'soft_left',
    'soft_right',
    'stop',
}


def clamp(value, minimum, maximum):
    return max(minimum, min(maximum, value))


class BridgeRequestError(Exception):
    def __init__(self, message, status=HTTPStatus.BAD_REQUEST):
        super().__init__(message)
        self.status = status


class FootbotHttpBridge(Node):
    def __init__(self):
        super().__init__('footbot_http_bridge')

        self.declare_parameter('cmd_vel_topic', '/cmd_vel')
        self.declare_parameter('http_host', '127.0.0.1')
        self.declare_parameter('http_port', 8080)
        self.declare_parameter('max_linear_velocity', 0.25)
        self.declare_parameter('max_angular_velocity', 1.2)
        self.declare_parameter('default_speed', 150)
        self.declare_parameter('min_effective_speed', 50)
        self.declare_parameter('command_timeout_sec', 0.75)
        self.declare_parameter('enable_cors', True)
        self.declare_parameter('max_request_bytes', 4096)

        self.cmd_vel_topic = self.get_parameter('cmd_vel_topic').value
        self.http_host = self.get_parameter('http_host').value
        self.http_port = int(self.get_parameter('http_port').value)
        self.max_linear_velocity = float(
            self.get_parameter('max_linear_velocity').value
        )
        self.max_angular_velocity = float(
            self.get_parameter('max_angular_velocity').value
        )
        self.default_speed = int(self.get_parameter('default_speed').value)
        self.min_effective_speed = int(
            self.get_parameter('min_effective_speed').value
        )
        self.command_timeout_sec = float(
            self.get_parameter('command_timeout_sec').value
        )
        self.enable_cors = bool(self.get_parameter('enable_cors').value)
        self.max_request_bytes = int(self.get_parameter('max_request_bytes').value)

        self.publisher = self.create_publisher(Twist, self.cmd_vel_topic, 10)
        self.last_command = None
        self.last_twist = self.make_zero_twist()
        self.last_command_time = None
        self._lock = threading.Lock()
        self._server = None
        self._server_thread = None
        self._stopped_by_timeout = False

        self.timeout_timer = self.create_timer(0.1, self._stop_stale_motion)
        self._start_http_server()

    def _start_http_server(self):
        handler = self._make_handler()
        self._server = ThreadingHTTPServer((self.http_host, self.http_port), handler)
        self._server_thread = threading.Thread(
            target=self._server.serve_forever,
            name='footbot_http_bridge_server',
            daemon=True,
        )
        self._server_thread.start()
        self.get_logger().info(
            'HTTP bridge listening on http://%s:%d and publishing to %s'
            % (self.http_host, self.http_port, self.cmd_vel_topic)
        )

    def _make_handler(self):
        bridge = self

        class RequestHandler(BaseHTTPRequestHandler):
            server_version = 'FootbotHttpBridge/0.1'

            def log_message(self, format_string, *args):
                bridge.get_logger().debug(
                    '%s - %s' % (self.address_string(), format_string % args)
                )

            def do_OPTIONS(self):
                self._send_empty(HTTPStatus.NO_CONTENT)

            def do_GET(self):
                if self._request_path() != '/status':
                    self._send_json(
                        HTTPStatus.NOT_FOUND,
                        {'ok': False, 'error': 'Unknown endpoint'},
                    )
                    return
                self._send_json(HTTPStatus.OK, bridge.get_status())

            def do_POST(self):
                if self._request_path() != '/move':
                    self._send_json(
                        HTTPStatus.NOT_FOUND,
                        {'ok': False, 'error': 'Unknown endpoint'},
                    )
                    return

                try:
                    body = self._read_json_body()
                    response = bridge.handle_move_request(body)
                    self._send_json(HTTPStatus.OK, response)
                except BridgeRequestError as exc:
                    self._send_json(exc.status, {'ok': False, 'error': str(exc)})
                except Exception as exc:  # pragma: no cover - defensive server boundary
                    bridge.get_logger().error('Unexpected /move failure: %s' % exc)
                    self._send_json(
                        HTTPStatus.INTERNAL_SERVER_ERROR,
                        {'ok': False, 'error': 'Internal bridge failure'},
                    )

            def do_PUT(self):
                self._send_method_not_allowed()

            def do_PATCH(self):
                self._send_method_not_allowed()

            def do_DELETE(self):
                self._send_method_not_allowed()

            def _request_path(self):
                return urlparse(self.path).path

            def _send_method_not_allowed(self):
                self._send_json(
                    HTTPStatus.METHOD_NOT_ALLOWED,
                    {'ok': False, 'error': 'Method not allowed'},
                )

            def _read_json_body(self):
                try:
                    content_length = int(self.headers.get('Content-Length', '0'))
                except ValueError as exc:
                    raise BridgeRequestError('Invalid Content-Length header') from exc

                if content_length > bridge.max_request_bytes:
                    raise BridgeRequestError(
                        'Payload too large',
                        status=HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
                    )
                if content_length <= 0:
                    raise BridgeRequestError('Request body is required')

                raw_body = self.rfile.read(content_length)
                try:
                    decoded = raw_body.decode('utf-8')
                    data = json.loads(decoded)
                except UnicodeDecodeError as exc:
                    raise BridgeRequestError('Request body must be UTF-8 JSON') from exc
                except json.JSONDecodeError as exc:
                    raise BridgeRequestError('Malformed JSON body') from exc

                if not isinstance(data, dict):
                    raise BridgeRequestError('JSON body must be an object')
                return data

            def _send_empty(self, status):
                self.send_response(status)
                self._send_common_headers()
                self.end_headers()

            def _send_json(self, status, payload):
                encoded = json.dumps(payload).encode('utf-8')
                self.send_response(status)
                self._send_common_headers()
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(encoded)))
                self.end_headers()
                self.wfile.write(encoded)

            def _send_common_headers(self):
                if bridge.enable_cors:
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
                    self.send_header('Access-Control-Allow-Headers', 'Content-Type')

        return RequestHandler

    def handle_move_request(self, body):
        direction = self._parse_direction(body)
        speed = self._parse_speed(body)
        turn_ratio = self._parse_turn_ratio(body)
        twist = self.command_to_twist(direction, speed, turn_ratio)

        with self._lock:
            self.publisher.publish(twist)
            self.last_command = {
                'direction': direction,
                'speed': speed,
                'turn_ratio': turn_ratio if 'turn_ratio' in body else None,
            }
            self.last_twist = twist
            self.last_command_time = time.monotonic()
            self._stopped_by_timeout = direction == 'stop'

        self.get_logger().debug(
            'Published command %s speed=%d turn_ratio=%.3f to %s'
            % (direction, speed, turn_ratio, self.cmd_vel_topic)
        )
        return self._success_response(direction, speed, body, twist)

    def _parse_direction(self, body):
        direction = body.get('direction')
        if not isinstance(direction, str) or not direction.strip():
            raise BridgeRequestError('Field "direction" is required')
        direction = direction.strip().lower()
        if direction not in VALID_DIRECTIONS:
            raise BridgeRequestError('Invalid direction "%s"' % direction)
        return direction

    def _parse_speed(self, body):
        speed = body.get('speed', self.default_speed)
        if isinstance(speed, bool):
            raise BridgeRequestError('Field "speed" must be a number')
        try:
            speed = int(speed)
        except (TypeError, ValueError) as exc:
            raise BridgeRequestError('Field "speed" must be a number') from exc
        return int(clamp(speed, 0, 255))

    def _parse_turn_ratio(self, body):
        turn_ratio = body.get('turn_ratio', 0.5)
        if isinstance(turn_ratio, bool):
            raise BridgeRequestError('Field "turn_ratio" must be a number')
        try:
            turn_ratio = float(turn_ratio)
        except (TypeError, ValueError) as exc:
            raise BridgeRequestError('Field "turn_ratio" must be a number') from exc
        if not math.isfinite(turn_ratio):
            raise BridgeRequestError('Field "turn_ratio" must be finite')
        return clamp(turn_ratio, 0.0, 1.0)

    def command_to_twist(self, direction, speed, turn_ratio):
        twist = self.make_zero_twist()
        if direction == 'stop' or speed <= 0:
            return twist

        effective_speed = max(speed, self.min_effective_speed)
        scale = effective_speed / 255.0
        linear_speed = scale * self.max_linear_velocity
        angular_speed = scale * self.max_angular_velocity

        if direction == 'forward':
            twist.linear.x = linear_speed
        elif direction == 'backward':
            twist.linear.x = -linear_speed
        elif direction == 'left':
            twist.angular.z = angular_speed
        elif direction == 'right':
            twist.angular.z = -angular_speed
        elif direction == 'soft_left':
            twist.linear.x = linear_speed
            twist.angular.z = angular_speed * turn_ratio
        elif direction == 'soft_right':
            twist.linear.x = linear_speed
            twist.angular.z = -angular_speed * turn_ratio
        return twist

    def _success_response(self, direction, speed, body, twist):
        return {
            'ok': True,
            'direction': direction,
            'speed': speed,
            'turn_ratio': body.get('turn_ratio'),
            'topic': self.cmd_vel_topic,
            'twist': self.twist_to_dict(twist),
        }

    def get_status(self):
        with self._lock:
            return {
                'ok': True,
                'bridge': 'running',
                'mode': 'simulation',
                'topic': self.cmd_vel_topic,
                'last_command': self.last_command,
                'last_twist': self.twist_to_dict(self.last_twist),
                'command_timeout_sec': self.command_timeout_sec,
            }

    def _stop_stale_motion(self):
        with self._lock:
            if self.last_command_time is None or self._stopped_by_timeout:
                return
            elapsed = time.monotonic() - self.last_command_time
            if elapsed < self.command_timeout_sec:
                return

            self.publisher.publish(self.make_zero_twist())
            self.last_twist = self.make_zero_twist()
            self._stopped_by_timeout = True
        self.get_logger().debug('Command timeout reached; published stop Twist')

    def shutdown(self):
        self.publish_stop()
        if self._server is not None:
            self._server.shutdown()
            self._server.server_close()
        if self._server_thread is not None:
            self._server_thread.join(timeout=2.0)

    def publish_stop(self):
        stop = self.make_zero_twist()
        self.publisher.publish(stop)
        with self._lock:
            self.last_twist = stop
            self._stopped_by_timeout = True

    @staticmethod
    def make_zero_twist():
        return Twist()

    @staticmethod
    def twist_to_dict(twist):
        return {
            'linear_x': twist.linear.x,
            'angular_z': twist.angular.z,
        }


def main(args=None):
    rclpy.init(args=args)
    node = FootbotHttpBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.shutdown()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
