from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class TrafficDecision:
    green_direction: str
    green_time: int
    counts: Dict[str, int]
    ranked_directions: List[str]
    emergency_direction: str | None = None
    is_emergency_override: bool = False
    emergency_note: str | None = None


def calculate_green_time(vehicle_count: int) -> int:
    """Dynamic signal timing based on traffic density."""
    return 10 + (vehicle_count * 2)


def decide_signal(
    counts: Dict[str, int],
    emergency_counts: Dict[str, int] | None = None,
) -> TrafficDecision:
    """
    Pick the direction with the highest vehicle count.

    In case of a tie, the first direction in the provided mapping order wins.
    """
    emergency_counts = emergency_counts or {}
    emergency_ranked = sorted(emergency_counts.keys(), key=lambda key: emergency_counts[key], reverse=True)
    if emergency_ranked:
        emergency_direction = emergency_ranked[0]
        green_time = max(30, calculate_green_time(counts.get(emergency_direction, 0)))
        return TrafficDecision(
            green_direction=emergency_direction,
            green_time=green_time,
            counts=counts,
            ranked_directions=sorted(counts.keys(), key=lambda key: counts[key], reverse=True),
            emergency_direction=emergency_direction,
            is_emergency_override=True,
            emergency_note="Emergency vehicle detected. Green signal granted immediately.",
        )

    if not counts:
        return TrafficDecision(
            green_direction="N/A",
            green_time=10,
            counts={},
            ranked_directions=[],
        )

    ranked = sorted(counts.keys(), key=lambda key: counts[key], reverse=True)
    green_direction = ranked[0]
    green_time = calculate_green_time(counts[green_direction])
    return TrafficDecision(
        green_direction=green_direction,
        green_time=green_time,
        counts=counts,
        ranked_directions=ranked,
    )


def normalize_direction_name(direction: str) -> str:
    return direction.strip().upper()
