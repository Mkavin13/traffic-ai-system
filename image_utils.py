from __future__ import annotations

import os
import random
from typing import Iterable, List, Optional


ALLOWED_IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp")


def list_direction_images(image_dir: str | Iterable[str], direction_stem: str) -> List[str]:
    """
    Return all images for a given direction.

    Supported naming examples:
    - north.jpg
    - north_1.jpeg
    - north-road.png
    """
    prefix = direction_stem.lower()
    matches: List[str] = []

    image_dirs = [image_dir] if isinstance(image_dir, str) else list(image_dir)

    for current_dir in image_dirs:
        if not os.path.isdir(current_dir):
            continue

        for filename in os.listdir(current_dir):
            lower_name = filename.lower()
            if not lower_name.startswith(prefix):
                continue
            if not lower_name.endswith(ALLOWED_IMAGE_EXTENSIONS):
                continue
            matches.append(os.path.join(current_dir, filename))

    return sorted(matches)


def pick_random_direction_image(image_dir: str | Iterable[str], direction_stem: str) -> Optional[str]:
    """Randomly choose one image for a direction on every request."""
    matches = list_direction_images(image_dir, direction_stem)
    if not matches:
        return None
    return random.choice(matches)


def pick_latest_direction_image(image_dir: str | Iterable[str], direction_stem: str) -> Optional[str]:
    """
    Choose the newest image for a direction.

    This is useful for uploaded files so the dashboard shows the most recently
    submitted image instead of a random legacy sample.
    """
    matches = list_direction_images(image_dir, direction_stem)
    if not matches:
        return None
    return max(matches, key=os.path.getmtime)
