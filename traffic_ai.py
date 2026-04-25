from __future__ import annotations

import os
from collections import OrderedDict

from detection import detect_all_directions
from image_utils import pick_random_direction_image
from traffic_logic import decide_signal, normalize_direction_name


BASE_DIR = os.path.abspath(os.path.dirname(__file__))
IMAGE_DIR = os.path.join(BASE_DIR, "static", "images")

IMAGES = OrderedDict(
    [
        ("North", "north"),
        ("South", "south"),
        ("East", "east"),
        ("West", "west"),
    ]
)


def main() -> None:
    images = OrderedDict()
    for direction, stem in IMAGES.items():
        selected = pick_random_direction_image(IMAGE_DIR, stem)
        images[direction] = os.path.relpath(selected, BASE_DIR).replace("\\", "/") if selected else os.path.join("static", "images", f"{stem}.jpg")

    detections = detect_all_directions(images)
    counts = OrderedDict(
        (normalize_direction_name(item.direction), item.vehicle_count)
        for item in detections
    )
    decision = decide_signal(counts)

    print("Vehicle counts:")
    for item in detections:
        print(f"- {item.direction}: {item.vehicle_count}")

    print(f"\nGreen signal: {decision.green_direction}")
    print(f"Allocated time: {decision.green_time} seconds")


if __name__ == "__main__":
    main()
