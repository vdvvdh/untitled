"""
State engine: turns raw observations into one classification per moment.

This module has NO I/O. It doesn't touch processes, windows, or the
database — it's a pure function so it can be unit tested with plain
inputs and predictable outputs.
"""

from dataclasses import dataclass
from enum import Enum


class GameState(str, Enum):
    ACTIVE = "active"
    IDLE = "idle"
    BACKGROUND = "background"
    UNKNOWN = "unknown"


@dataclass
class Observation:
    """Raw signals collected at one point in time."""
    target_process_running: bool
    target_process_focused: bool
    idle_seconds: float
    session_locked: bool = False


# Matches the product spec: 5-minute default idle threshold.
DEFAULT_IDLE_THRESHOLD_SECONDS = 5 * 60


def classify(observation: Observation, idle_threshold_seconds: float = DEFAULT_IDLE_THRESHOLD_SECONDS) -> GameState:
    """
    Apply state priority rules from the plan:
    1. Idle  - locked/asleep, or past the inactivity threshold
    2. Background - game running but not focused, user active elsewhere
    3. Active - game focused with recent input
    4. Unknown - target isn't running, or no reliable classification
    """
    if not observation.target_process_running:
        return GameState.UNKNOWN

    if observation.session_locked or observation.idle_seconds >= idle_threshold_seconds:
        return GameState.IDLE

    if observation.target_process_focused:
        return GameState.ACTIVE

    return GameState.BACKGROUND