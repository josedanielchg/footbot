import cv2
import asyncio

from .camera_manager import CameraManager
from .ball_detector import BallDetector
from .robot_controller import RobotController
from .robot_communicator import RobotCommunicator
from .color_manager import ColorManager
from . import config_auto as config

# Optional tuner (fully isolated)
if getattr(config, "COLOR_TUNER_ENABLED", False):
    from .color_tuner import ColorTuner
else:
    ColorTuner = None


class Application:
    def __init__(self):
        self.camera_manager = CameraManager()
        self.color_manager = ColorManager()
        self.ball_detector = BallDetector(self.color_manager)
        self.robot_controller = RobotController()
        self.robot_communicator = RobotCommunicator()
        self.color_tuner = ColorTuner(self.color_manager) if ColorTuner else None
        self._dbg_i = 0
        self.running = False

    async def initialize(self):
        if not self.camera_manager.initialize():
            return False
        if not self.ball_detector.initialize():
            self.camera_manager.release()
            return False
        await self.robot_communicator.initialize()
        self.running = True
        print("Auto Soccer Bot Application initialized.")
        return True

    async def run_main_loop(self):
        print("Starting Automatic Ball Chasing. Press ESC to quit.")
        print(f"Target ESP32 Endpoint: {config.ESP32_MOVE_ENDPOINT}")

        while self.running and self.camera_manager.is_opened():
            raw = self.camera_manager.get_frame()
            if raw is None:
                await asyncio.sleep(0.01)
                continue

            # Optionally resize for speed:
            # raw = cv2.resize(raw, (320, 240))

            frame = self.color_manager.enhance_frame_colors(raw)

            h, w = frame.shape[:2]
            if self.camera_manager.frame_width == 0:
                self.camera_manager.frame_width, self.camera_manager.frame_height = w, h

            # Main detection (YOLO cadenced; color every frame)
            det = self.ball_detector.process_frame(frame)

            # Start display with the chosen detection
            display = self.ball_detector.draw_detection(frame.copy(), det)

            # Get components; allow stale YOLO so both overlays are always visible
            comps = self.ball_detector.get_last_components(allow_stale=True)

            # Draw BOTH overlays (YOLO=green, Color=magenta)
            display = self.ball_detector.draw_both_detections(
                display,
                comps.get("yolo"),
                comps.get("color"),
                tol_px=getattr(config, "TUNER_POSITION_TOL_PX", 20),
            )

            # Optional: annotate color IoU/circularity if available (helps debug “too big” blobs)
            cdet = comps.get("color")
            if cdet is not None and "iou" in cdet and "circularity" in cdet:
                bx, by, bw, bh = cdet.get("bbox", (10, 40, 0, 0))
                cv2.putText(display, f"IoU:{cdet['iou']:.2f}  circ:{cdet['circularity']:.2f}",
                            (bx, max(0, by - 22)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 1)

            # Control based on the chosen detection
            data = self.ball_detector.get_detection_data(det)
            direction, speed, turn_ratio = self.robot_controller.decide_action(data, w)
            asyncio.create_task(self.robot_communicator.send_command(direction, speed, turn_ratio))

            # Optional tuner
            if self.color_tuner:
                self.color_tuner.update(frame, comps.get("yolo"), comps.get("color"))

                status = self.color_tuner.get_status()
                lo, hi = self.color_manager.get_hsv_bounds()
                s, v = self.color_manager.get_sv_gains()
                hud = (
                    f"SamePlace:{status['same_place_count']}/{status['same_place_needed']}  "
                    f"ConsecCorrect:{status['consecutive_correct']}/{status['correct_needed']}  "
                    f"Sx:{s:.2f} Vx:{v:.2f}  "
                    f"L:{tuple(int(x) for x in lo)} U:{tuple(int(x) for x in hi)}"
                )
                cv2.putText(display, hud, (10, h - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 0), 1)

            # Compact console line every 10 frames (centers + distance + near)
            self._dbg_i += 1
            if (self._dbg_i % 10) == 0:
                def _center_of(det_):
                    if not det_:
                        return None
                    if det_.get("type") == "color":
                        return tuple(map(int, det_["center"]))
                    x_, y_, w_, h_ = det_["bbox"]
                    return (int(x_ + w_ // 2), int(y_ + h_ // 2))

                yc = _center_of(comps.get("yolo"))
                cc = _center_of(comps.get("color"))
                if yc and cc:
                    dx, dy = cc[0] - yc[0], cc[1] - yc[1]
                    dist = (dx * dx + dy * dy) ** 0.5
                    near = dist <= getattr(config, "TUNER_POSITION_TOL_PX", 20)
                else:
                    dist, near = None, False
                print(f"[DetCompare] used={comps.get('used')} yolo={yc} color={cc} "
                      f"dist={None if dist is None else round(dist,1)} near={near}")

            # Overlay controller info and show
            self.robot_controller.draw_target_zone(display, w, h)
            self.robot_controller.draw_state_info(display)
            cv2.putText(display, f"Cmd: {direction} @ {speed}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.imshow('Auto Soccer Bot - Ball Detection', display)

            key = cv2.waitKey(5) & 0xFF
            if key == 27:
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
            import traceback; traceback.print_exc()
        finally:
            await app.cleanup()