import threading
import httpx
import cv2
import numpy as np
import re
from collections import deque
from . import config_auto as config

class MJPEGLowLatencyReader:
    def __init__(self, url: str):
        self.url = url
        self.client = httpx.Client(timeout=None)
        self.resp = None
        self.boundary = None
        self.thread = None
        self.running = False
        self.latest = None    # último frame decodificado (np.ndarray)
        self.dim = (0, 0)

    def start(self):
        # Abrimos la conexión en modo streaming
        self.stream_ctx = self.client.stream(
            "GET",
            self.url,
            headers={"Accept": "multipart/x-mixed-replace"},
        )
        # Entramos al context manager manualmente para poder cerrarlo en stop()
        self.resp = self.stream_ctx.__enter__()

        ctype = self.resp.headers.get("Content-Type", "")
        m = re.search(r'boundary="?([^";]+)"?', ctype, re.I)
        boundary = m.group(1) if m else "123456789000000000000987654321"
        if boundary.startswith("--"):
            boundary = boundary[2:]
        self.boundary = ("--" + boundary).encode()

        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        try:
            if self.resp:
                self.resp.close()
        except Exception:
            pass
        try:
            if getattr(self, "stream_ctx", None):
                self.stream_ctx.__exit__(None, None, None)
        except Exception:
            pass
        try:
            self.client.close()
        except Exception:
            pass

    def _run(self):
        # Parser simple por cabeceras + Content-Length (tal como las envía tu ESP32)
        buf = b""
        it = self.resp.iter_bytes()
        boundary_marker = b"--" + self.boundary
        while self.running:
            try:
                chunk = next(it)
            except StopIteration:
                break
            except Exception:
                break
            buf += chunk
            # Consume varias partes si ya están completas en buffer
            while True:
                bpos = buf.find(boundary_marker)
                if bpos == -1:
                    break
                # Busca fin de cabeceras (\r\n\r\n) después del boundary
                hdr_start = buf.find(b"\r\n", bpos)
                if hdr_start == -1:
                    break
                hdr_end = buf.find(b"\r\n\r\n", hdr_start + 2)
                if hdr_end == -1:
                    break
                headers_blob = buf[hdr_start + 2:hdr_end].decode("latin1", "ignore")
                mlen = re.search(r"Content-Length:\s*(\d+)", headers_blob, re.I)
                if not mlen:
                    # descarta boundary y sigue
                    buf = buf[hdr_end + 4:]
                    continue
                length = int(mlen.group(1))
                body_start = hdr_end + 4
                if len(buf) < body_start + length:
                    # espera más datos
                    break
                jpeg = buf[body_start:body_start + length]
                buf = buf[body_start + length:]  # recorta lo ya consumido

                # Decodifica y guarda SOLO el último (drop frames!)
                img = cv2.imdecode(np.frombuffer(jpeg, np.uint8), cv2.IMREAD_COLOR)
                if img is not None:
                    h, w = img.shape[:2]
                    self.dim = (w, h)
                    self.latest = img  # sobrescribe (cola de tamaño 1)

    def read(self):
        return self.latest

    def size(self):
        return self.dim


class CameraManager:
    def __init__(self):
        self.source_type = config.VIDEO_SOURCE
        self.source_path = config.WEBCAM_INDEX if self.source_type == 'webcam' else config.ESP32_STREAM_URL
        self.cap = None
        self.reader = None
        self.frame_width = 0
        self.frame_height = 0

    def initialize(self):
        print(f"Initializing camera source: {self.source_type} at {self.source_path}")
        if self.source_type == 'webcam':
            self.cap = cv2.VideoCapture(self.source_path)
            if not self.cap.isOpened():
                print(f"Error: Could not open webcam: {self.source_path}")
                return False
            self.frame_width  = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            print(f"Webcam initialized. {self.frame_width}x{self.frame_height}")
            return True
        else:
            # ESP32 MJPEG lector sin cola
            self.reader = MJPEGLowLatencyReader(self.source_path)
            self.reader.start()
            print("ESP32 MJPEG low-latency reader started.")
            return True

    def get_frame(self):
        if self.source_type == 'webcam':
            if self.cap and self.cap.isOpened():
                ok, frame = self.cap.read()
                if ok:
                    if self.frame_width == 0 or self.frame_height == 0:
                        self.frame_height, self.frame_width = frame.shape[:2]
                    return frame
                return None
        else:
            frame = self.reader.read()
            if frame is not None:
                if self.frame_width == 0 or self.frame_height == 0:
                    w, h = self.reader.size()
                    if w and h:
                        self.frame_width, self.frame_height = w, h
                return frame
            return None

    def get_frame_dimensions(self):
        return self.frame_height, self.frame_width

    def release(self):
        if self.source_type == 'webcam':
            if self.cap:
                self.cap.release()
        else:
            if self.reader:
                self.reader.stop()
        print("Video source released.")

    def is_opened(self):
        if self.source_type == 'webcam':
            return self.cap is not None and self.cap.isOpened()
        else:
            return self.reader is not None