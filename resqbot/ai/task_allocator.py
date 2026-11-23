"""Task-allocation policies for survivor response."""
from resqbot.core.geometry import manhattan

TRIAGE_URGENCY = {"CRITICAL": 3, "URGENT": 2, "STABLE": 1}

def rank_survivors(targets, triage, robot_position):
    """Return survivor grid cells by synthetic urgency, then travel distance.

    Triage values are simulation labels only, not medical classifications.
    """
    return sorted(
        targets,
        key=lambda cell: (
            -TRIAGE_URGENCY.get(triage.get(cell, "STABLE"), 1),
            manhattan(robot_position, cell),
        ),
    )
