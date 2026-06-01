from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class YoloDetection:
    class_id: int
    class_name: str
    confidence: float
    center_x: float
    center_y: float
    width: float
    height: float
    x1: float
    y1: float
    x2: float
    y2: float


class YoloDetector:
    def __init__(
        self,
        model_path='',
        model_name='yolo11n.pt',
        confidence_threshold=0.35,
        iou_threshold=0.45,
        device='cpu',
        image_size=640,
        target_classes=None,
        max_detections=20,
    ):
        self.confidence_threshold = float(confidence_threshold)
        self.iou_threshold = float(iou_threshold)
        self.device = str(device)
        self.image_size = int(image_size)
        self.max_detections = int(max_detections)
        self.target_classes = {
            class_name.strip().lower()
            for class_name in (target_classes or [])
            if class_name and class_name.strip()
        }

        try:
            from ultralytics import YOLO
        except ImportError as exc:
            raise RuntimeError(
                'Ultralytics YOLO is not installed. Install it from the repository root with: '
                'python3 -m pip install --user -r simulation/requirements-yolo.txt'
            ) from exc

        selected_model = self._resolve_model(model_path, model_name)
        self.model = YOLO(selected_model)
        self.names = self._read_model_names()

    def detect(self, bgr_image):
        results = self.model.predict(
            source=bgr_image,
            conf=self.confidence_threshold,
            iou=self.iou_threshold,
            imgsz=self.image_size,
            device=self.device,
            max_det=self.max_detections,
            verbose=False,
        )

        detections = []
        if not results:
            return detections

        result = results[0]
        if result.boxes is None:
            return detections

        boxes = result.boxes
        xyxy = boxes.xyxy.cpu().numpy()
        class_ids = boxes.cls.cpu().numpy().astype(int)
        confidences = boxes.conf.cpu().numpy()

        for box, class_id, confidence in zip(xyxy, class_ids, confidences):
            class_name = self.names.get(int(class_id), str(class_id))
            if self.target_classes and class_name.lower() not in self.target_classes:
                continue

            x1, y1, x2, y2 = [float(value) for value in box]
            width = max(0.0, x2 - x1)
            height = max(0.0, y2 - y1)
            detections.append(YoloDetection(
                class_id=int(class_id),
                class_name=class_name,
                confidence=float(confidence),
                center_x=x1 + width / 2.0,
                center_y=y1 + height / 2.0,
                width=width,
                height=height,
                x1=x1,
                y1=y1,
                x2=x2,
                y2=y2,
            ))

        return detections

    def _resolve_model(self, model_path, model_name):
        if model_path:
            path = Path(model_path).expanduser()
            if not path.exists():
                raise RuntimeError(f'YOLO model path does not exist: {path}')
            return str(path)

        local_model = Path(__file__).resolve().parents[2] / 'models' / 'weights' / model_name
        if local_model.exists():
            return str(local_model)

        return model_name

    def _read_model_names(self):
        names = getattr(self.model, 'names', {})
        if isinstance(names, dict):
            return {int(key): str(value) for key, value in names.items()}
        return {index: str(value) for index, value in enumerate(names)}
