import httpx
import asyncio
import time
from . import config_auto as config
import json

class RobotCommunicator:
    def __init__(self):
        self.http_client = None
        self.is_request_in_flight = False
        self.last_sent_command_to_robot = None
        self.last_sent_speed_to_robot = None
        self.last_sent_turn_ratio = None
        self.last_command_time_robot = 0

    async def initialize(self):
        if self.http_client is None:
            limits = httpx.Limits(max_connections=5, max_keepalive_connections=2)
            timeout = httpx.Timeout(config.HTTP_TIMEOUT_READ, connect=config.HTTP_TIMEOUT_CONNECT)
            self.http_client = httpx.AsyncClient(timeout=timeout, limits=limits)
            print("RobotCommunicator (Auto): Async HTTP client initialized.")

    async def close(self):
        if self.http_client:
            await self.http_client.aclose()
            self.http_client = None
            print("RobotCommunicator (Auto): Async HTTP client closed.")

    async def send_command(self, direction, speed=config.DEFAULT_ROBOT_SPEED, turn_ratio=1.0):
        if not direction:
            return

        if not self.http_client:
            print("RobotCommunicator: HTTP client not initialized. Command not sent.")
            return

        current_time_ms = time.time() * 1000

        if current_time_ms - self.last_command_time_robot < config.MIN_TIME_BETWEEN_ANY_COMMAND_MS:
            return
        if (direction == self.last_sent_command_to_robot and 
            speed == self.last_sent_speed_to_robot and
            turn_ratio == self.last_sent_turn_ratio and
            current_time_ms - self.last_command_time_robot < config.COMMAND_SEND_INTERVAL_MS):
            return
        if self.is_request_in_flight:
            return

        self.is_request_in_flight = True
        payload = {"direction": direction, "speed": int(speed), "turn_ratio": float(turn_ratio)}
        json_payload_str = json.dumps(payload)
        # print(f"RobotCommunicator (Auto): Sending: {json_payload_str}") # Debug print

        try:
            print(payload)
            response = await self.http_client.post(config.ESP32_MOVE_ENDPOINT, json=payload)
            response.raise_for_status()
            self.last_sent_command_to_robot = direction
            self.last_sent_speed_to_robot = speed
            self.last_sent_turn_ratio = turn_ratio
            self.last_command_time_robot = current_time_ms
        except httpx.ReadTimeout:
            print(f"RobotCommunicator (Auto): ReadTimeout sending command '{direction}'.")
        except httpx.ConnectTimeout:
            print(f"RobotCommunicator (Auto): ConnectTimeout sending command '{direction}'.")
        except httpx.RequestError as e:
            print(f"RobotCommunicator (Auto): Error sending command '{direction}': {e}")
        except Exception as e:
            print(f"RobotCommunicator (Auto): Unexpected error sending command '{direction}': {e}")
        finally:
            self.is_request_in_flight = False