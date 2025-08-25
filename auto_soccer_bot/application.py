import cv2
import asyncio
import time
from .camera_manager import CameraManager
from .ball_detector import BallDetector
from .robot_controller import RobotController
from .robot_communicator import RobotCommunicator
from . import config_auto as config

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

        while self.running and self.camera_manager.is_opened():
            frame = self.camera_manager.get_frame()
            if frame is None:
                # print("No frame received.")
                await asyncio.sleep(0.01)
                continue
            
            frame_height, frame_width = self.camera_manager.get_frame_dimensions()
            if frame_width == 0 or frame_height == 0: # Ensure dimensions are valid
                 frame_height_temp, frame_width_temp, _ = frame.shape # Get from current frame
                 if frame_width_temp > 0 and frame_height_temp > 0:
                     self.camera_manager.frame_width = frame_width_temp
                     self.camera_manager.frame_height = frame_height_temp
                     frame_width, frame_height = frame_width_temp, frame_height_temp
                 else:
                     await asyncio.sleep(0.01)
                     continue

            # 1. Detect the ball
            processed_frame, yolo_detection = self.ball_detector.process_frame(frame.copy(), draw=True)

            # 2. Decide robot action based on ball position
            # ball_detection_data is (center_x, center_y, radius, area) or None
            ball_info = self.ball_detector.get_detection_data(yolo_detection)

            direction_command, speed_command, turn_ratio_command = self.robot_controller.decide_action(
                ball_info, frame_width
            )

            # 3. Send command to robot
            asyncio.create_task(
                self.robot_communicator.send_command(direction_command, speed_command, turn_ratio_command)
            )

            # 4. Display visuals
            self.robot_controller.draw_target_zone(processed_frame, frame_width, frame_height)
            self.robot_controller.draw_state_info(processed_frame)
            cv2.putText(processed_frame, f"Cmd: {direction_command} @ {speed_command}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.imshow('Auto Soccer Bot - Ball Detection', processed_frame)
            
            key = cv2.waitKey(5) & 0xFF
            if key == 27:  # ESC key
                self.running = False
                # Send a final stop command
                asyncio.create_task(self.robot_communicator.send_command("stop", 0))
                await asyncio.sleep(0.2) # Give it time to send
                break
            
            await asyncio.sleep(0.001) # Yield to event loop

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
    else:
        print("Failed to initialize auto_soccer_bot application.")