import cv2
import asyncio
import time
import numpy as np # Make sure to import numpy
from .camera_manager import CameraManager
from .ball_detector import BallDetector
from .robot_controller import RobotController
from .robot_communicator import RobotCommunicator
from . import config_auto as config

def enhance_frame_colors(frame, saturation_scale=1.5, value_scale=1.2):
    """
    Enhances the color saturation and value of a frame to make colors more vibrant.
    :param frame: The input frame in BGR format.
    :param saturation_scale: Factor to scale the saturation by (e.g., 1.5 for 50% increase).
    :param value_scale: Factor to scale the brightness by (e.g., 1.2 for 20% increase).
    :return: The enhanced frame in BGR format.
    """
    if frame is None:
        return None
    
    # Convert the image from BGR to HSV color space
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    
    # Split the channels
    h, s, v = cv2.split(hsv)

    # Increase the saturation
    # We multiply the saturation channel by a factor.
    # We must then ensure the values remain in the valid 8-bit range [0, 255].
    s = cv2.multiply(s, saturation_scale)
    s = np.clip(s, 0, 255).astype(np.uint8)

    # Optionally, increase the brightness/value as well
    v = cv2.multiply(v, value_scale)
    v = np.clip(v, 0, 255).astype(np.uint8)

    # Merge the channels back together
    final_hsv = cv2.merge((h, s, v))
    
    # Convert the HSV image back to BGR format
    enhanced_frame = cv2.cvtColor(final_hsv, cv2.COLOR_HSV2BGR)
    
    return enhanced_frame


class Application:
    def __init__(self):
        self.camera_manager = CameraManager()
        self.ball_detector = BallDetector()
        self.robot_controller = RobotController()
        self.robot_communicator = RobotCommunicator()
        self.running = False

    async def initialize(self):
        if not self.camera_manager.initialize(): return False
        if not self.ball_detector.initialize():
            self.camera_manager.release()
            return False
        await self.robot_communicator.initialize()
        self.running = True
        print("Auto Soccer Bot Application initialized.")
        return True

    async def run_main_loop(self):
        print("Starting Automatic Ball Chasing. Press ESC in OpenCV window to quit.")
        print(f"Target ESP32 Endpoint: {config.ESP32_MOVE_ENDPOINT}")

        # --- Frame Skipping & State Variables ---
        frame_counter = 0
        last_yolo_detection = None # Store the last valid detection result

        while self.running and self.camera_manager.is_opened():
            raw_frame = self.camera_manager.get_frame()
            if raw_frame is None:
                await asyncio.sleep(0.01)
                continue

            # --- Pre-processing Steps (Color enhancement, resizing, etc.) ---
            # TODO: For best performance, you should also resize the frame here
            # raw_frame = cv2.resize(raw_frame, (640, 480))

            if self.camera_manager.source_type != 'webcam':
                enhanced_frame = enhance_frame_colors(raw_frame, saturation_scale=config.SATURATION, value_scale=config.BRIGHTNESS)
            else:
                enhanced_frame = raw_frame

            # The frame dimensions should be taken from the final processed frame
            frame_height, frame_width, _ = enhanced_frame.shape
            if self.camera_manager.frame_width == 0:
                self.camera_manager.frame_width = frame_width
                self.camera_manager.frame_height = frame_height

            frame_counter += 1
            # We will draw on this copy of the frame
            display_frame = enhanced_frame.copy()

            # --- Frame Skipping Logic ---
            if frame_counter % config.DETECTION_INTERVAL == 0:
                # On a detection frame, we UNCONDITIONALLY update our memory. The result of process_frame is the new reality.
                last_yolo_detection = self.ball_detector.process_frame(enhanced_frame)
            
            # Now, draw whatever is in our memory (either the new detection or None)
            display_frame = self.ball_detector.draw_detection(display_frame, last_yolo_detection)

            # 2. Decide robot action based on the most recent valid ball position
            ball_info = self.ball_detector.get_detection_data(last_yolo_detection)

            direction_command, speed_command, turn_ratio_command = self.robot_controller.decide_action(
                ball_info, frame_width
            )

            # 3. Send command to robot
            asyncio.create_task(
                self.robot_communicator.send_command(direction_command, speed_command, turn_ratio_command)
            )

            # 4. Display visuals on the frame we've been drawing on
            self.robot_controller.draw_target_zone(display_frame, frame_width, frame_height)
            self.robot_controller.draw_state_info(display_frame)
            cv2.putText(display_frame, f"Cmd: {direction_command} @ {speed_command}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.imshow('Auto Soccer Bot - Ball Detection', display_frame)
            
            key = cv2.waitKey(5) & 0xFF
            if key == 27:  # ESC key
                self.running = False
                asyncio.create_task(self.robot_communicator.send_command("stop", 0))
                await asyncio.sleep(0.2)
                break
            
            await asyncio.sleep(0.001)

    async def cleanup(self):
        self.camera_manager.release()
        cv2.destroyAllWindows()
        await self.robot_communicator.close()
        print("Auto Soccer Bot Application cleaned up.")

async def start_auto_application():
    app = Application()
    if await app.initialize():
        try:
            await app.run_main_loop()
        except Exception as e:
            print(f"Error in auto_soccer_bot main loop: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await app.cleanup()