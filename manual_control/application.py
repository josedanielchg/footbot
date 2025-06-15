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
                await asyncio.sleep(0.01)
                continue
            
            frame_height, frame_width, _ = frame.shape

            # 1. Detect hands (or other objects in the future)
            processed_frame, detection_results_mp = self.hand_detector.process_frame(frame, draw=True)

            # 2. Extract relevant data from detection
            # --- Process detected hands ---
            all_hands_data = self.hand_detector.get_detection_data(detection_results_mp)

            right_hand_landmarks = None
            left_hand_landmarks = None

            # --- Iterate through detected hands to find left and right ---
            for landmarks, handedness_str in all_hands_data:
                if handedness_str.lower() == "right": # Use .lower() for case-insensitivity
                    right_hand_landmarks = landmarks
                    # print("Found Right Hand")
                elif handedness_str.lower() == "left":
                    left_hand_landmarks = landmarks
                    # print("Found Left Hand")

            # 3.1 Classify gesture based on landmarks
            # --- Get Direction from Right Hand ---
            current_direction_command = "stop" # Default

            if right_hand_landmarks:
                right_fingers_status = self.gesture_classifier.get_fingers_status(right_hand_landmarks, "Right")
                if right_fingers_status:
                    cmd = self.gesture_classifier.classify_gesture(right_fingers_status)
                    if cmd:
                        current_direction_command = cmd
            
            # 3.2 Calculate spped based on landmarks
            # --- Get Speed from Left Hand ---
            current_speed = config.DEFAULT_SPEED
            if left_hand_landmarks:
                current_speed = self.gesture_classifier.calculate_speed_from_left_hand(
                    left_hand_landmarks, frame_width, frame_height
                )
                # Display speed (optional)
                cv2.putText(processed_frame, f"Speed: {current_speed}", (10, 60),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

            current_command = "stop" # Default to stop if no hand or specific gesture

            # 4. Send command to robot (if changed or needs resending based on communicator's logic)
            # The communicator handles rate limiting and in-flight checks.
            asyncio.create_task(self.robot_communicator.send_command(current_direction_command, current_speed))

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