# manual_control/robot_communicator.py
import httpx
import asyncio
import time
from . import config

class RobotCommunicator:
    def __init__(self):
        self.http_client = None
        self.is_request_in_flight = False
        self.last_sent_command_to_robot = None # Renamed to be specific
        self.last_command_time_robot = 0       # Renamed

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

    async def send_command(self, command):
        if not command: # If no command, do nothing or send stop
            # Decide if a "None" command should implicitly send "stop"
            # For now, let's assume the calling logic handles that.
            return

        if not self.http_client:
            print("RobotCommunicator: HTTP client not initialized. Command not sent.")
            return

        current_time_ms = time.time() * 1000

        # Prevent flooding the ESP32 with any command too quickly
        if current_time_ms - self.last_command_time_robot < config.MIN_TIME_BETWEEN_ANY_COMMAND_MS:
            return

        # Prevent resending the *same* command too quickly
        if command == self.last_sent_command_to_robot and \
           current_time_ms - self.last_command_time_robot < config.COMMAND_SEND_INTERVAL_MS:
            return

        if self.is_request_in_flight:
            # print(f"RobotCommunicator: Request for '{self.last_sent_command_to_robot}' still in flight. Skipping '{command}'.")
            return

        self.is_request_in_flight = True
        payload = {"direction": command}
        # print(f"RobotCommunicator: Attempting to send command: {command}")

        try:
            response = await self.http_client.post(config.ESP32_MOVE_ENDPOINT, json=payload)
            response.raise_for_status()
            print(f"RobotCommunicator: Sent '{command}', ESP32 Response: {response.status_code} - {response.text}")
            self.last_sent_command_to_robot = command
            self.last_command_time_robot = current_time_ms
        except httpx.ReadTimeout:
            print(f"RobotCommunicator: ReadTimeout sending command '{command}'.")
        except httpx.ConnectTimeout:
             print(f"RobotCommunicator: ConnectTimeout sending command '{command}'.")
        except httpx.RequestError as e:
            print(f"RobotCommunicator: Error sending command '{command}': {e}")
        except Exception as e:
            print(f"RobotCommunicator: Unexpected error sending command '{command}': {e}")
        finally:
            self.is_request_in_flight = False