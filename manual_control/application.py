# manual_control/application.py
import cv2
import asyncio
from .camera_manager import CameraManager
from .hand_detector import HandDetector # Or your chosen DetectionManager implementation
from .gesture_classifier import GestureClassifier
from .robot_communicator import RobotCommunicator
from . import config
import time

class Application:
    def __init__(self):
        self.camera_manager = CameraManager()
        self.hand_detector = HandDetector() # Using HandDetector specifically for now
        self.gesture_classifier = GestureClassifier()
        self.robot_communicator = RobotCommunicator()
        self.running = False

    async def initialize(self):
        if not self.camera_manager.initialize():
            return False
        if not self.hand_detector.initialize(): # Assuming detector needs init
            self.camera_manager.release()
            return False
        await self.robot_communicator.initialize()
        self.running = True
        print("Application initialized.")
        return True

    async def run_main_loop(self):
        print("Starting main control loop. Press ESC in OpenCV window to quit.")
        print(f"Sending commands to: {config.ESP32_MOVE_ENDPOINT}")

        last_known_command = "stop" # Start with stop

        while self.running and self.camera_manager.is_opened():
            frame = self.camera_manager.get_frame()
            if frame is None:
                await asyncio.sleep(0.01) # Brief pause if no frame
                continue

            # 1. Detect hands (or other objects in the future)
            processed_frame, detection_results = self.hand_detector.process_frame(frame, draw=True)

            # 2. Extract relevant data from detection
            hand_landmarks, handedness = self.hand_detector.get_detection_data(detection_results)

            current_command = "stop" # Default to stop if no hand or specific gesture

            if hand_landmarks:
                # 3. Classify gesture based on landmarks
                fingers_status = self.gesture_classifier.get_fingers_status(hand_landmarks, handedness)
                if fingers_status:
                    # Display finger status (optional)
                    finger_names = ["Thumb", "Index", "Middle", "Ring", "Pinky"]
                    status_text = ", ".join([f"{name}: {'Down' if status else 'Up'}"
                                             for name, status in zip(finger_names, fingers_status)])
                    cv2.putText(processed_frame, status_text, (10, 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

                    # Get command from gesture
                    gesture_command = self.gesture_classifier.classify_gesture(fingers_status)
                    if gesture_command:
                        current_command = gesture_command
            
            # 4. Send command to robot (if changed or needs resending based on communicator's logic)
            # The communicator now handles its own rate limiting and "in-flight" checks.
            # Only create a task if the command is potentially new or important to resend.
            if current_command != self.robot_communicator.last_sent_command_to_robot or current_command == "stop":
                asyncio.create_task(self.robot_communicator.send_command(current_command))
            elif current_command: # Resend non-stop commands periodically
                # Check if enough time has passed since last_command_time_robot in communicator
                if time.time() * 1000 - self.robot_communicator.last_command_time_robot > config.COMMAND_SEND_INTERVAL_MS :
                    asyncio.create_task(self.robot_communicator.send_command(current_command))

            # 5. Display processed frame
            cv2.imshow('Hand Gesture Control', processed_frame)
            key = cv2.waitKey(5) & 0xFF
            if key == 27:  # ESC key
                self.running = False
                break
            
            await asyncio.sleep(0.001)

    async def cleanup(self):
        self.camera_manager.release()
        cv2.destroyAllWindows()
        await self.robot_communicator.close()
        print("Application cleaned up.")

async def start_application():
    app = Application()
    if await app.initialize():
        try:
            await app.run_main_loop()
        except Exception as e:
            print(f"Error in main loop: {e}")
        finally:
            await app.cleanup()
    else:
        print("Failed to initialize application.")