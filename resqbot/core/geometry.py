"""Grid geometry helpers."""
from resqbot.core.config import COLS, ROWS

def inside(x, y):
    return 0 <= x < COLS and 0 <= y < ROWS

def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])
