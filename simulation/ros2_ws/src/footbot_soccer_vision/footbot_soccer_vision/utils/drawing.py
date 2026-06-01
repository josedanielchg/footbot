import cv2


def draw_detections(image, detections, fps=None):
    output = image.copy()

    for detection in detections:
        x1 = int(round(detection.x1))
        y1 = int(round(detection.y1))
        x2 = int(round(detection.x2))
        y2 = int(round(detection.y2))
        label = f'{detection.class_name} {detection.confidence:.2f}'

        cv2.rectangle(output, (x1, y1), (x2, y2), (60, 220, 80), 2)
        cv2.circle(
            output,
            (int(round(detection.center_x)), int(round(detection.center_y))),
            4,
            (0, 0, 255),
            -1,
        )
        _draw_label(output, label, x1, max(0, y1 - 8))

    if fps is not None:
        _draw_label(output, f'FPS: {fps:.1f}', 10, 28)

    return output


def _draw_label(image, text, x, y):
    font = cv2.FONT_HERSHEY_SIMPLEX
    scale = 0.55
    thickness = 1
    (width, height), baseline = cv2.getTextSize(text, font, scale, thickness)
    top_left = (x, max(0, y - height - baseline - 4))
    bottom_right = (x + width + 8, y + baseline + 4)
    cv2.rectangle(image, top_left, bottom_right, (20, 20, 20), -1)
    cv2.putText(image, text, (x + 4, y), font, scale, (255, 255, 255), thickness, cv2.LINE_AA)
