import asyncio
import re
import httpx
import numpy as np
import cv2
from . import config_auto as config

# Boundary used by the ESP32 MJPEG server (matches firmware PART_BOUNDARY)
BOUNDARY = b"--123456789000000000000987654321"
HEADER_END = b"\r\n\r\n"

class CameraManager:
    def __init__(self):
        self.source_type = config.VIDEO_SOURCE
        self.source_path = config.WEBCAM_INDEX if self.source_type == 'webcam' else config.ESP32_STREAM_URL
        self.cap = None  # used only for 'webcam' or legacy 'esp32_stream'
        self.frame_width = 0
        self.frame_height = 0

        # httpx streaming state
        self._client = None
        self._stream_task = None
        self._stop = False
        self._opened = False
        self._latest_frame = None  # always keep only the newest frame (dropping)

    def initialize(self):
        print(f"Initializing camera source: {self.source_type} at {self.source_path}")

        if self.source_type == 'webcam':
            self.cap = cv2.VideoCapture(self.source_path)
            if not self.cap.isOpened():
                print(f"Error: Could not open webcam index {self.source_path}")
                return False
            self.frame_width  = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 0
            self.frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 0
            self._opened = True
            print(f"Webcam initialized. {self.frame_width}x{self.frame_height}")
            return True

        elif self.source_type == 'esp32_httpx':
            # Start async MJPEG reader; frames are parsed and the latest is stored
            self._stop = False
            self._stream_task = asyncio.create_task(self._run_httpx_mjpeg_reader())
            self._opened = True
            print("ESP32 MJPEG over httpx: reader task started.")
            return True

        else:  # legacy 'esp32_stream' via OpenCV (kept for compatibility)
            self.cap = cv2.VideoCapture(self.source_path)
            if not self.cap.isOpened():
                print(f"Error: Could not open ESP32 stream via OpenCV: {self.source_path}")
                return False
            try:
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # may not have effect on all backends
            except Exception:
                pass
            self._opened = True
            print("Warning: Using OpenCV on network stream can add latency. Prefer 'esp32_httpx'.")
            return True

    async def _run_httpx_mjpeg_reader(self):
        # Infinite MJPEG stream: no read timeout; connect timeout from config
        limits = httpx.Limits(max_connections=1, max_keepalive_connections=1)
        timeout = httpx.Timeout(None, connect=config.HTTP_TIMEOUT_CONNECT)
        headers = {"Accept": "multipart/x-mixed-replace"}

        self._client = httpx.AsyncClient(limits=limits, timeout=timeout)
        try:
            async with self._client.stream("GET", self.source_path, headers=headers) as resp:
                resp.raise_for_status()
                buf = bytearray()

                async for chunk in resp.aiter_bytes():
                    if self._stop:
                        break
                    buf.extend(chunk)

                    # Parse one or more complete MJPEG parts from the buffer
                    while True:
                        bidx = buf.find(BOUNDARY)
                        if bidx == -1:
                            # Keep buffer size in check while waiting for a boundary
                            if len(buf) > 2 * len(BOUNDARY):
                                del buf[:len(buf) - 2 * len(BOUNDARY)]
                            break

                        h_end = buf.find(HEADER_END, bidx)
                        if h_end == -1:
                            # Incomplete headers; wait for more data
                            break

                        headers_bytes = bytes(buf[bidx:h_end])
                        m = re.search(br'Content-Length:\s*(\d+)', headers_bytes, re.IGNORECASE)
                        if not m:
                            # If no Content-Length, drop headers and resync
                            del buf[:h_end + 4]
                            continue

                        length = int(m.group(1))
                        start = h_end + 4  # after \r\n\r\n

                        if len(buf) < start + length:
                            # Incomplete JPEG payload; wait for more data
                            break

                        jpg = bytes(buf[start:start + length])
                        del buf[:start + length]

                        # Decode JPEG to BGR; keep only the most recent frame
                        arr = np.frombuffer(jpg, dtype=np.uint8)
                        frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
                        if frame is not None:
                            # TODO: Jose, check if this feature increases YOLO performance
                            # frame = cv2.resize(frame, (640, 480)) # Or any other desired size
                            self.frame_height, self.frame_width = frame.shape[:2]
                            self._latest_frame = frame

        except Exception as e:
            print(f"ESP32 MJPEG reader error: {e}")
        finally:
            await self._close_httpx()

    async def _close_httpx(self):
        if self._client is not None:
            try:
                await self._client.aclose()
            except Exception:
                pass
            self._client = None

    def get_frame(self):
        # Returns the newest frame available; may be None at startup
        if self.source_type == 'webcam':
            if self.cap and self.cap.isOpened():
                ok, frame = self.cap.read()
                if ok:
                    if self.frame_width == 0 or self.frame_height == 0:
                        self.frame_height, self.frame_width = frame.shape[:2]
                    return frame
            return None

        elif self.source_type == 'esp32_httpx':
            return self._latest_frame

        else:  # 'esp32_stream' legacy
            if self.cap and self.cap.isOpened():
                ok, frame = self.cap.read()
                if ok:
                    if self.frame_width == 0 or self.frame_height == 0:
                        self.frame_height, self.frame_width = frame.shape[:2]
                    return frame
            return None

    def get_frame_dimensions(self):
        return self.frame_height, self.frame_width

    def release(self):
        self._opened = False

        if self.source_type in ('webcam', 'esp32_stream'):
            if self.cap:
                self.cap.release()
                self.cap = None
                print("Video source released.")
        elif self.source_type == 'esp32_httpx':
            self._stop = True
            task = self._stream_task
            self._stream_task = None
            if task and not task.done():
                task.cancel()
            print("ESP32 MJPEG httpx reader stopped.")

    def is_opened(self):
        if self.source_type == 'esp32_httpx':
            return self._opened
        return self.cap is not None and self.cap.isOpened()
