"""Reusable path-planning algorithms."""
import heapq
from resqbot.core.config import DIRS
from resqbot.core.geometry import inside, manhattan

def astar(start, goal, blocked, risk=None):
    """Risk-aware A*: hazardous cells remain traversable but incur a penalty."""
    if start == goal:
        return [start]
    risk = risk or {}
    frontier = [(0, start)]
    came = {}
    cost_so_far = {start: 0}
    while frontier:
        _, current = heapq.heappop(frontier)
        if current == goal:
            path = [current]
            while current in came:
                current = came[current]
                path.append(current)
            return list(reversed(path))
        for dx, dy in DIRS:
            nxt = (current[0] + dx, current[1] + dy)
            if not inside(*nxt) or nxt in blocked:
                continue
            level = risk.get(nxt, 0) if hasattr(risk, "get") else (1 if nxt in risk else 0)
            penalty = 8 if level == 1 else 20 if level == 2 else 40 if level >= 3 else 0
            new_cost = cost_so_far[current] + 1 + penalty
            if new_cost < cost_so_far.get(nxt, float("inf")):
                cost_so_far[nxt] = new_cost
                came[nxt] = current
                heapq.heappush(frontier, (new_cost + manhattan(nxt, goal), nxt))
    return []
