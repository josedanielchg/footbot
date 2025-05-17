# manual_control/main.py

# manual_control\venv_manual_control\Scripts\activate
# python -m manual_control.main

import cv2
import asyncio  # Import asyncio
from . import config
from .hand_detector import HandDetector
# Import the wrapper and client management functions
from .gesture_controller import interpret_gesture_and_send_command_wrapper, initialize_http_client, close_http_client


async def async_main():  # Make main an async function
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return

    await initialize_http_client()  # Initialize the async client

    detector = HandDetector(
        max_num_hands=config.MAX_NUM_HANDS,
        min_detection_confidence=config.MIN_DETECTION_CONFIDENCE,
        min_tracking_confidence=config.MIN_TRACKING_CONFIDENCE
    )

    print("Starting hand gesture control. Press ESC to quit.")
    print(f"Attempting to send commands to: {config.ESP32_MOVE_ENDPOINT}")

    try:
        while cap.isOpened():
            success, frame = cap.read()
            if not success:
                # print("Ignoring empty camera frame.") # Can be noisy
                await asyncio.sleep(0.01)  # Yield control briefly
                continue

            processed_frame, detection_results = detector.find_hands(frame, draw=True)

            fingers_status = None
            if detection_results.multi_hand_landmarks:
                fingers_status = detector.get_fingers_status(detection_results)
                if fingers_status:
                    finger_names = ["Thumb", "Index", "Middle", "Ring", "Pinky"]
                    status_text = ", ".join([f"{name}: {'Down' if status else 'Up'}"
                                             for name, status in zip(finger_names, fingers_status)])
                    cv2.putText(processed_frame, status_text, (10, 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)

            # Call the synchronous wrapper which internally creates an async task
            interpret_gesture_and_send_command_wrapper(fingers_status)

            cv2.imshow('Hand Gesture Control', processed_frame)

            key = cv2.waitKey(5) & 0xFF
            if key == 27:  # Press ESC to quit
                break

            await asyncio.sleep(0.001)  # Yield control to the event loop very briefly

    finally:  # Ensure cleanup
        cap.release()
        cv2.destroyAllWindows()
        await close_http_client()  # Close the async client
        print("Application terminated.")


if __name__ == "__main__":
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        print("Main loop interrupted by user.")
