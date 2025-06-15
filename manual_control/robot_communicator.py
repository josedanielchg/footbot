# manual_control/robot_communicator.py
import httpx
import asyncio
import time
from . import config
import json

class RobotCommunicator:
    def __init__(self):
        self.http_client = None
        self.is_request_in_flight = False
        self.last_sent_command_to_robot = None
        self.last_sent_speed_to_robot = None
        self.last_command_time_robot = 0

    async def initialize(self):
        if self.http_client is None:
            limits = httpx.Limits(max_connections=5, max_keepalive_connections=2)
            timeout = httpx.Timeout(config.HTTP_TIMEOUT_READ, connect=config.HTTP_TIMEOUT_CONNECT)
            self.http_client = httpx.AsyncClient(timeout=timeout, limits=limits)
            print("RobotCommunicator: Async HTTP client initialized.")

    async def close(self):
        if self.http_client:
            await self.http_client.aclose()
            self.http_client = None
            print("RobotCommunicator: Async HTTP client closed.")

    async def send_command(self, direction, speed=config.DEFAULT_SPEED):
        if not direction:
            return

        if not self.http_client:
            print("RobotCommunicator: HTTP client not initialized. Command not sent.")
            return

        current_time_ms = time.time() * 1000

        # Prevent flooding the ESP32 with any command too quickly
        if current_time_ms - self.last_command_time_robot < config.MIN_TIME_BETWEEN_ANY_COMMAND_MS:
            return

        # Send if command OR speed changed, or enough time passed for resending same command/speed
        if (direction == self.last_sent_command_to_robot and speed == self.last_sent_speed_to_robot) and \
           (current_time_ms - self.last_command_time_robot < config.COMMAND_SEND_INTERVAL_MS):
            return


        if self.is_request_in_flight:
            # print(f"RobotCommunicator: Request for '{self.last_sent_command_to_robot}' still in flight. Skipping '{command}'.")
            return

        self.is_request_in_flight = True
        payload = {"direction": direction, "speed": int(speed)}
        
         # --- Print JSON payload for debugging ---
        json_payload_str = json.dumps(payload)
        print(f"RobotCommunicator: Attempting to send payload: {json_payload_str}")

        try:
            response = await self.http_client.post(config.ESP32_MOVE_ENDPOINT, json=payload)
            response.raise_for_status()
            print(f"RobotCommunicator: Sent '{direction}', ESP32 Response: {response.status_code} - {response.text}")
            self.last_sent_command_to_robot = direction
            self.last_sent_speed_to_robot = speed
            self.last_command_time_robot = current_time_ms
        except httpx.ReadTimeout:
            print(f"RobotCommunicator: ReadTimeout sending command '{direction}'.")
        except httpx.ConnectTimeout:
             print(f"RobotCommunicator: ConnectTimeout sending command '{direction}'.")
        except httpx.RequestError as e:
            print(f"RobotCommunicator: Error sending command '{direction}': {e}")
        except Exception as e:
            print(f"RobotCommunicator: Unexpected error sending command '{direction}': {e}")
        finally:
            self.is_request_in_flight = False