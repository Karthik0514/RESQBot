"""Disaster world model and multi-agent simulation loop."""
import math
import random

from resqbot.core.config import *
from resqbot.core.geometry import inside, manhattan
from resqbot.ai.pathfinding import astar
from resqbot.ai.task_allocator import rank_survivors

class RescueWorld:
    def __init__(self, seed=None):
        self.rng = random.Random(seed)
        self.start = (1, 1)
        self.base = (1, 1)
        self.robot = self.start
        self.robot_positions = [self.start, (2, 1), (1, 2)]
        self.robot_homes = [(1, 1), (2, 1), (1, 2)]
        self.robot_paths = [[], [], []]
        self.robot_steps = [0, 0, 0]
        self.robot_battery = [100.0, 100.0, 100.0]
        self.robot_returning = [False, False, False]
        self.robot_failure_ticks = [0, 0, 0]
        self.robot_colors = [(53, 169, 230), (172, 117, 235), (80, 190, 145)]
        self.walls = set()
        self.hazards = set()
        self.survivors = set()
        self.found = set()
        self.rescued = set()
        self.triage = {}
        self.detection_confidence = {}
        self.visited = set()
        self.visible = set()
        self.known_blocked = set()
        self.known_hazards = set()
        self.hazard_levels = {}
        self.known_hazard_levels = {}
        self.hazard_clock = 0
        self.hazard_events = 0
        self.path = []
        self.steps = 0
        self.distance = 0
        self.running = False
        self.complete = False
        self.status = "Ready for deployment"
        self.last_move = 0
        self.explored_count = 0
        self.generate()

    def generate(self):
        # Continue the seeded RNG stream so repeated maps are reproducible in tests.
        self.walls = set()
        self.hazards = set()
        self.survivors = set()
        self.found = set()
        self.rescued = set()
        self.triage = {}
        self.detection_confidence = {}
        self.visited = set()
        self.visible = set()
        self.known_blocked = set()
        self.known_hazards = set()
        self.hazard_levels = {}
        self.known_hazard_levels = {}
        self.hazard_clock = 0
        self.hazard_events = 0
        self.path = []
        self.robot = self.start
        self.robot_positions = list(self.robot_homes)
        self.robot_paths = [[], [], []]
        self.robot_steps = [0, 0, 0]
        self.robot_battery = [100.0, 100.0, 100.0]
        self.robot_returning = [False, False, False]
        self.robot_failure_ticks = [0, 0, 0]
        self.communication_links = 0
        self.steps = self.distance = 0
        self.running = self.complete = False
        self.explored_count = 0

        # Boundary walls
        for x in range(COLS):
            self.walls.add((x, 0))
            self.walls.add((x, ROWS-1))
        for y in range(ROWS):
            self.walls.add((0, y))
            self.walls.add((COLS-1, y))

        # Scattered rubble blocks; keep start/base region clear.
        candidates = [(x,y) for x in range(3, COLS-2) for y in range(2, ROWS-2)]
        self.rng.shuffle(candidates)
        for cell in candidates[:52]:
            self.walls.add(cell)

        # Hazards and survivors are placed on free cells.
        free = [(x,y) for x in range(2, COLS-2) for y in range(2, ROWS-2)
                if (x,y) not in self.walls]
        self.rng.shuffle(free)
        self.hazards = set(free[:7])
        self.hazard_levels = {p: self.rng.randint(1, 2) for p in self.hazards}
        self.survivors = set(free[10:14])
        # Synthetic triage categories used only to demonstrate mission scheduling.
        self.triage = {
            p: self.rng.choice(["CRITICAL", "URGENT", "STABLE"])
            for p in self.survivors
        }

        # Ensure at least one clear corridor from entry into the map.
        for x in range(1, 8):
            self.walls.discard((x, 1))
            self.hazards.discard((x, 1))
        for home in self.robot_homes:
            self.walls.discard(home)
            self.hazards.discard(home)
            self.survivors.discard(home)
        self._sense()
        self.status = "Environment generated — press SPACE to deploy"

    def _line_of_sight(self, target):
        """Grid ray check: solid rubble blocks the simulated thermal signal."""
        x0, y0 = self.robot
        x1, y1 = target
        dx, dy = abs(x1-x0), abs(y1-y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        x, y = x0, y0
        while (x, y) != (x1, y1):
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy
            if (x, y) != (x1, y1) and (x, y) in self.walls:
                return False
        return True

    def _sense(self):
        rx, ry = self.robot
        for y in range(max(0, ry-SENSOR_RADIUS), min(ROWS, ry+SENSOR_RADIUS+1)):
            for x in range(max(0, rx-SENSOR_RADIUS), min(COLS, rx+SENSOR_RADIUS+1)):
                if math.hypot(x-rx, y-ry) <= SENSOR_RADIUS + 0.25:
                    p = (x,y)
                    self.visible.add(p)
                    if p in self.walls:
                        self.known_blocked.add(p)
                    if p in self.hazards:
                        self.known_hazards.add(p)
                        self.known_hazard_levels[p] = self.hazard_levels.get(p, 1)
                    # Survivors are only detected when the virtual sensor has
                    # an unobstructed line of sight through the simulated map.
                    if p in self.survivors and p not in self.found and self._line_of_sight(p):
                        self.found.add(p)
                        # Demonstration score: stronger virtual signal at shorter range.
                        confidence = max(0.60, 0.99 - 0.09 * math.hypot(x-rx, y-ry))
                        self.detection_confidence[p] = round(confidence, 2)
                        self.status = (
                            f"{self.triage[p]} survivor signal detected "
                            f"at grid {p[0]}, {p[1]}"
                        )

    def _evolve_hazards(self):
        """Periodically intensify and occasionally spread simulated fire to nearby floor."""
        self.hazard_clock += 1
        if self.hazard_clock < 12:
            return
        self.hazard_clock = 0
        updated = dict(self.hazard_levels)
        for p, level in list(self.hazard_levels.items()):
            if level < 3 and self.rng.random() < 0.45:
                updated[p] = level + 1
                self.hazard_events += 1
            if self.rng.random() < 0.12:
                for dx, dy in DIRS:
                    q = (p[0] + dx, p[1] + dy)
                    if (inside(*q) and q not in self.walls and q not in self.hazards
                            and q not in self.survivors and q != self.base
                            and self.rng.random() < 0.10):
                        updated[q] = 1
                        self.hazards.add(q)
                        self.hazard_events += 1
                        break
        self.hazard_levels = updated
        self._sense()
        self.status = "Hazard conditions changed — updating risk map and route"

    def _frontiers(self):
        # A frontier is a known free cell adjacent to at least one unknown cell.
        result = []
        for p in self.visible:
            if p in self.known_blocked:
                continue
            for dx, dy in DIRS:
                q = (p[0]+dx, p[1]+dy)
                if inside(*q) and q not in self.visible and q not in self.known_blocked:
                    result.append(p)
                    break
        return list(set(result))

    def _choose_target(self, excluded=None):
        excluded = excluded or set()
        # Prioritize detected survivors by synthetic triage urgency, then distance.
        # This is a scheduling demonstration, not a medical triage diagnosis.
        targets = [s for s in self.found if s not in self.rescued and s not in excluded]
        if targets:
            targets = rank_survivors(targets, self.triage, self.robot)
            return targets[0], f"Responding to {self.triage[targets[0]]} survivor"
        if len(self.rescued) == len(self.survivors) and self.rescued:
            return self.base, "Returning to rescue base"
        frontiers = self._frontiers()
        options = []
        for target in frontiers:
            if target in excluded:
                continue
            route = astar(self.robot, target, self.known_blocked, self.known_hazard_levels)
            if route:
                # Prefer short routes and frontiers that reveal more map.
                unknown_near = sum(
                    1 for dx,dy in DIRS
                    if inside(target[0]+dx, target[1]+dy)
                    and (target[0]+dx, target[1]+dy) not in self.visible
                )
                score = len(route) - 0.7 * unknown_near
                options.append((score, target, route))
        if options:
            options.sort(key=lambda item: item[0])
            return options[0][1], "Exploring unknown area"
        return None, "Exploration complete"

    def multi_tick(self):
        """Advance three agents with shared information, battery management and recovery."""
        if not self.running or self.complete:
            return

        claimed = set()
        occupied = set(self.robot_positions)

        # Communication links are available when two active robots are within radio range.
        active_ids = [i for i in range(3) if self.robot_failure_ticks[i] <= 0]
        self.communication_links = sum(
            1 for a in range(len(active_ids)) for b in range(a + 1, len(active_ids))
            if manhattan(self.robot_positions[active_ids[a]],
                         self.robot_positions[active_ids[b]]) <= 10
        )

        for idx in range(3):
            current = self.robot_positions[idx]
            self.robot = current

            if self.robot_failure_ticks[idx] > 0:
                self.robot_failure_ticks[idx] -= 1
                self.robot_paths[idx] = []
                continue

            self._sense()

            # Low-battery robots return to their own base to recharge.
            if self.robot_battery[idx] <= 22:
                self.robot_returning[idx] = True

            if self.robot_returning[idx]:
                target = self.robot_homes[idx]
                message = f"Robot {idx+1}: returning to recharge"
                if current == target:
                    self.robot_battery[idx] = min(100.0, self.robot_battery[idx] + 5.0)
                    if self.robot_battery[idx] >= 90:
                        self.robot_returning[idx] = False
                        self.status = f"Robot {idx+1} recharged and available"
                    self.robot_paths[idx] = []
                    continue
            elif len(self.rescued) == len(self.survivors):
                target = self.robot_homes[idx]
                message = f"Robot {idx+1}: returning to staging point"
            else:
                target, message = self._choose_target(claimed)

            if target is None:
                self.robot_paths[idx] = []
                continue

            claimed.add(target)
            if current == target:
                if target in self.found and target not in self.rescued:
                    self.rescued.add(target)
                    self.status = f"Robot {idx+1} assisted {self.triage.get(target, 'STABLE')} survivor"
                self.robot_paths[idx] = []
                continue

            other_robots = occupied - {current}
            blocked = self.known_blocked | other_robots
            route = astar(current, target, blocked, self.known_hazard_levels)
            self.robot_paths[idx] = route
            if len(route) > 1:
                nxt = route[1]
                if nxt not in occupied and nxt not in self.known_blocked:
                    occupied.discard(current)
                    occupied.add(nxt)
                    self.robot_positions[idx] = nxt
                    self.robot = nxt
                    self.robot_steps[idx] += 1
                    self.steps += 1
                    self.distance += 1
                    self.robot_battery[idx] = max(0.0, self.robot_battery[idx] - 0.65)
                    self.visited.add(nxt)
                    self._sense()

                    # Rare temporary breakdown when entering a severe simulated hazard.
                    if self.hazard_levels.get(nxt, 0) >= 3 and self.rng.random() < 0.06:
                        self.robot_failure_ticks[idx] = 24
                        self.status = f"Robot {idx+1} temporarily disabled by severe hazard — tasks reassigned"

        self.robot = self.robot_positions[0]
        self._evolve_hazards()
        self._sense()
        self.explored_count = len([p for p in self.visible if p not in self.known_blocked])

        if (len(self.rescued) == len(self.survivors)
                and all(pos == home for pos, home in zip(self.robot_positions, self.robot_homes))
                and not any(self.robot_returning)
                and all(battery >= 90 for battery in self.robot_battery)):
            self.running = False
            self.complete = True
            self.status = "Mission complete — survivors assisted and all robots recovered"
        elif all(not self._frontiers() for _ in [0]) and len(self.rescued) < len(self.survivors):
            if all(not path for path in self.robot_paths) and not any(self.robot_failure_ticks):
                self.running = False
                self.complete = True
                self.status = "Exploration stopped — no reachable frontier remains"

    def tick(self):
        if not self.running or self.complete:
            return
        target, message = self._choose_target()
        self.status = message
        if target == self.robot and target in self.found and target not in self.rescued:
            self.rescued.add(target)
            self.visited.add(target)
            self.status = f"Survivor assisted: {self.triage[target]} priority"
            return
        if target == self.robot and target == self.base and len(self.rescued) == len(self.survivors):
            self.running = False
            self.complete = True
            self.status = "Mission complete — survivors assisted, robot returned to base"
            return
        if target is None:
            self.running = False
            self.complete = True
            self.status = "Mission complete — all reachable areas explored"
            return
        route = astar(self.robot, target, self.known_blocked, self.known_hazard_levels)
        self.path = route
        if len(route) <= 1:
            self.visited.add(target)
            if target in self.found:
                self.visited.add(target)
            return
        nxt = route[1]
        # Simulated local sensing before movement prevents entering a newly seen wall.
        self._sense()
        if nxt in self.known_blocked:
            self.path = []
            return
        self.robot = nxt
        self.steps += 1
        self.distance += 1
        self.visited.add(nxt)
        self._evolve_hazards()
        self._sense()
        self.explored_count = len([p for p in self.visible if p not in self.known_blocked])

    def add_obstacle(self):
        # Add a wall a few cells away, not on the robot or base.
        candidates = []
        for dx,dy in DIRS:
            p = (self.robot[0]+dx*2, self.robot[1]+dy*2)
            if inside(*p) and p not in self.walls and p not in self.hazards and p not in self.survivors and p != self.base:
                candidates.append(p)
        if candidates:
            p = self.rng.choice(candidates)
            self.walls.add(p)
            if p in self.visible:
                self.known_blocked.add(p)
            self.status = f"New rubble detected at {p[0]}, {p[1]} — replanning"
        else:
            self.status = "No safe location for a new obstacle"


