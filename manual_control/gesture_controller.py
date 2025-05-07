# manual_control/gesture_controller.py

import httpx
import asyncio  # For asynchronous operations
import time
from . import config

# To prevent spamming commands
last_sent_command = None
COMMAND_SEND_INTERVAL_MS = 300  # Send command at most every 300ms if different
# Or if same command, can be sent more frequently if needed for responsiveness
MIN_TIME_BETWEEN_ANY_COMMAND_MS = 100  # A hard limit to avoid flooding
last_command_time = 0

# --- New variables for async request management ---
is_request_in_flight = False  # Flag to indicate if an HTTP request is currently being processed
http_client = None  # httpx.AsyncClient instance, will be initialized later


async def initialize_http_client():
    """Initializes the asynchronous HTTP client."""
    global http_client
    if http_client is None:
        # We can set transport limits here if needed
        limits = httpx.Limits(max_connections=5, max_keepalive_connections=2)
        timeout = httpx.Timeout(1.0, connect=2.0)  # 1s read, 2s connect timeout
        http_client = httpx.AsyncClient(timeout=timeout, limits=limits)
    print("Async HTTP client initialized.")


async def close_http_client():
    """Closes the asynchronous HTTP client."""
    global http_client
    if http_client:
        await http_client.aclose()
        http_client = None
        print("Async HTTP client closed.")


async def send_command_to_esp32_async(direction_command):
    """
    Sends a movement command to the ESP32 server asynchronously.
    :param direction_command: String, e.g., "forward", "stop".
    """
    global is_request_in_flight, last_sent_command, last_command_time

    if not http_client:
        print("HTTP client not initialized. Command not sent.")
        return

    current_time_ms = time.time() * 1000

    # Basic rate limiting
    if current_time_ms - last_command_time < MIN_TIME_BETWEEN_ANY_COMMAND_MS:
        # print(f"Rate limited. Last command sent {current_time_ms - last_command_time:.0f}ms ago.")
        return

    # More sophisticated rate limiting based on command type and interval
    if direction_command == last_sent_command and current_time_ms - last_command_time < COMMAND_SEND_INTERVAL_MS:
        # If it's the same command, and we sent it recently, maybe skip or be less frequent
        # This depends on how responsive you want repeated commands to be.
        # For now, we'll rely on the MIN_TIME_BETWEEN_ANY_COMMAND_MS for this.
        pass

    if is_request_in_flight:
        print(f"Request for '{last_sent_command}' still in flight. Skipping new command '{direction_command}'.")
        return

    is_request_in_flight = True
    params = {"direction": direction_command}
    print(f"Attempting to send async command: {direction_command}...")

    try:
        response = await http_client.get(config.ESP32_MOVE_ENDPOINT, params=params)
        response.raise_for_status()
        print(f"Sent command: {direction_command}, ESP32 Response: {response.status_code} - {response.text}")
        last_sent_command = direction_command  # Update only on successful send
        last_command_time = current_time_ms
    except httpx.RequestError as e:
        print(f"Async error sending command '{direction_command}' to ESP32: {e}")
        # Optionally, you might want to retry or handle ESP32 being unavailable
    except Exception as e:
        print(f"An unexpected async error occurred: {e}")
    finally:
        is_request_in_flight = False  # Allow next request


def interpret_gesture_and_send_command_wrapper(fingers_down_status):
    """
    Synchronous wrapper to interpret gesture and schedule the async command.
    This is called from the main synchronous loop.
    """
    global last_sent_command, last_command_time  # Access globals for logic before async call

    current_time_ms = time.time() * 1000
    command_to_send = None

    if fingers_down_status is None:  # No hand detected
        if last_sent_command != "stop":
            if current_time_ms - last_command_time > COMMAND_SEND_INTERVAL_MS:  # Debounce stop
                command_to_send = "stop"
    else:
        # Gesture: All five fingers "down" (curled) means "forward"
        if all(fingers_down_status):
            command_to_send = "forward"
        # Gesture: All five fingers "up" (extended) means "stop"
        elif not any(fingers_down_status):
            command_to_send = "stop"
        # --- Add more gestures here if needed ---
        # Example: Index finger up, others down -> "left"
        # elif not fingers_down_status[0] and fingers_down_status[1] and \
        #      not fingers_down_status[2] and not fingers_down_status[3] and not fingers_down_status[4]:
        #     command = "some_other_command"

    if command_to_send:
        # Check if the command is new or if enough time has passed since the last command
        if command_to_send != last_sent_command or \
                (current_time_ms - last_command_time > COMMAND_SEND_INTERVAL_MS):
            # Schedule the async task.
            # We don't 'await' it here because this wrapper is called from a sync context.
            # The main loop will continue, and this task will run in the background.
            asyncio.create_task(send_command_to_esp32_async(command_to_send))
        # else:
        # print(f"Command '{command_to_send}' same as last or too soon. Not sending.")

    elif last_sent_command != "stop":  # Default to stop if no specific gesture and not already stopping
        if current_time_ms - last_command_time > COMMAND_SEND_INTERVAL_MS:
            asyncio.create_task(send_command_to_esp32_async("stop"))


# --- Main execution block for gesture_controller.py (if run directly for testing) ---
async def _test_async_sending():
    await initialize_http_client()
    print(f"ESP32 Move Endpoint: {config.ESP32_MOVE_ENDPOINT}")

    print("\nTesting 'forward' command (async):")
    interpret_gesture_and_send_command_wrapper([True, True, True, True, True])
    await asyncio.sleep(0.1)  # Give some time for the request to potentially start

    print("\nTesting 'stop' command (async):")
    interpret_gesture_and_send_command_wrapper([False, False, False, False, False])
    await asyncio.sleep(0.1)

    print("\nTesting rapid 'forward' (should be rate limited by in-flight or interval):")
    interpret_gesture_and_send_command_wrapper([True, True, True, True, True])
    await asyncio.sleep(0.05)  # Very short delay
    interpret_gesture_and_send_command_wrapper([True, True, True, True, True])  # This might be skipped
    await asyncio.sleep(0.6)  # Wait longer than interval
    interpret_gesture_and_send_command_wrapper([True, True, True, True, True])  # This should send

    await asyncio.sleep(2)  # Allow pending tasks to complete
    await close_http_client()


if __name__ == '__main__':
    try:
        asyncio.run(_test_async_sending())
    except KeyboardInterrupt:
        print("Test interrupted.")
    finally:
        # Ensure client is closed if run was interrupted before normal close
        if http_client and http_client.is_closed == False:
            asyncio.run(close_http_client())