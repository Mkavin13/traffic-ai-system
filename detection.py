from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Dict, List

import cv2
from ultralytics import YOLO


VEHICLE_CLASSES = {
    "car",
    "motorcycle",
    "bus",
    "truck",
}

EMERGENCY_ALIASES = {
    "ambulance",
    "fire truck",
    "firetruck",
    "fire engine",
    "fireengine",
    "emergency vehicle",
    "emergencyvehicle",
}


@dataclass
class DetectionResult:
    direction: str
    image_path: str
    vehicle_count: int
    class_counts: Dict[str, int]
    emergency_count: int = 0
    emergency_labels: Dict[str, int] = field(default_factory=dict)
    error: str | None = None


@lru_cache(maxsize=1)
def load_model() -> YOLO:
    """Load the YOLOv8 model once and reuse it for every request."""
    weights_path = os.getenv("YOLO_MODEL_WEIGHTS", "yolov8n.pt")
    return YOLO(weights_path)


def _resolve_image_path(image_path: str) -> str:
    if os.path.isabs(image_path):
        return image_path
    base_dir = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_dir, image_path)


def detect_vehicles(image_path: str, direction: str) -> DetectionResult:
    """
    Detect vehicles in a single image using YOLOv8.

    The function counts only cars, motorcycles, buses, and trucks.
    """
    resolved_path = _resolve_image_path(image_path)

    if not os.path.exists(resolved_path):
        return DetectionResult(
            direction=direction,
            image_path=image_path,
            vehicle_count=0,
            class_counts={},
            error=f"Image not found: {image_path}",
        )

    model = load_model()
    image = cv2.imread(resolved_path)
    if image is None:
        return DetectionResult(
            direction=direction,
            image_path=image_path,
            vehicle_count=0,
            class_counts={},
            error=f"Unable to read image: {image_path}",
        )

    results = model.predict(source=image, verbose=False)
    names = model.names
    class_counts: Dict[str, int] = {}
    emergency_labels: Dict[str, int] = {}

    for result in results:
        if result.boxes is None:
            continue
        for cls_id in result.boxes.cls.tolist():
            class_name = str(names[int(cls_id)])
            normalized_name = class_name.lower().replace("_", " ").replace("-", " ").strip()
            if normalized_name in VEHICLE_CLASSES:
                class_counts[class_name] = class_counts.get(class_name, 0) + 1
            if normalized_name in EMERGENCY_ALIASES:
                emergency_labels[class_name] = emergency_labels.get(class_name, 0) + 1

    vehicle_count = sum(class_counts.values())
    return DetectionResult(
        direction=direction,
        image_path=image_path,
        vehicle_count=vehicle_count,
        class_counts=class_counts,
        emergency_count=sum(emergency_labels.values()),
        emergency_labels=emergency_labels,
    )


def detect_all_directions(images: Dict[str, str]) -> List[DetectionResult]:
    """Run detection for all directions and return the results in order."""
    return [
        detect_vehicles(image_path, direction)
        for direction, image_path in images.items()
    ]
