"""Pygame command-centre interface."""
import pygame

from resqbot.core.config import *
from resqbot.simulation.world import RescueWorld
from resqbot.services.exporter import export_mission

class App:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("RESQBOT V7 | Modular Rescue Robotics Platform")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("segoeui", 16)
        self.small = pygame.font.SysFont("segoeui", 13)
        self.heading = pygame.font.SysFont("segoeui", 22, bold=True)
        self.world = RescueWorld()
        self.accumulator = 0

    def text(self, s, x, y, color=WHITE, font=None):
        self.screen.blit((font or self.font).render(str(s), True, color), (x,y))

    def draw_button(self, rect, label, active=False):
        color = (40, 110, 150) if active else (47, 62, 80)
        pygame.draw.rect(self.screen, color, rect, border_radius=7)
        pygame.draw.rect(self.screen, (80, 103, 126), rect, 1, border_radius=7)
        surf = self.font.render(label, True, WHITE)
        self.screen.blit(surf, surf.get_rect(center=rect.center))

    def draw_map(self):
        w = self.world
        pygame.draw.rect(self.screen, (20, 29, 42),
                         (MAP_X-5, MAP_Y-5, COLS*CELL+10, ROWS*CELL+10), border_radius=8)
        for y in range(ROWS):
            for x in range(COLS):
                p = (x,y)
                r = pygame.Rect(MAP_X+x*CELL, MAP_Y+y*CELL, CELL-1, CELL-1)
                if p not in w.visible:
                    color = UNKNOWN
                elif p in w.walls:
                    color = RUBBLE
                elif p in w.hazards:
                    color = FIRE
                else:
                    color = FLOOR
                pygame.draw.rect(self.screen, color, r, border_radius=2)
                if p in w.known_hazards:
                    level = w.known_hazard_levels.get(p, 1)
                    ring = (255, 220, 110) if level == 1 else (255, 150, 65) if level == 2 else (255, 75, 55)
                    pygame.draw.circle(self.screen, ring, r.center, 4 + level)
                if p in w.found:
                    pygame.draw.circle(self.screen, SURVIVOR, r.center, 7)
                    pygame.draw.circle(self.screen, (80, 48, 20), r.center, 7, 1)
                    self.text("+", r.centerx-4, r.centery-9, (65, 43, 20), self.small)
                if p == w.base:
                    pygame.draw.rect(self.screen, GREEN, r.inflate(-8,-8), border_radius=3)
                if p in w.visited and p not in w.found and p != w.base:
                    pygame.draw.circle(self.screen, (90, 135, 153), r.center, 2)
                pygame.draw.rect(self.screen, GRID, r, 1, border_radius=2)

        # Planned routes for each cooperating robot.
        for idx, route in enumerate(w.robot_paths):
            if len(route) > 1:
                pts = [(MAP_X+x*CELL+CELL//2, MAP_Y+y*CELL+CELL//2) for x,y in route]
                pygame.draw.lines(self.screen, w.robot_colors[idx], False, pts, 2)

        # Three distinct rescue agents.
        for idx, (rx, ry) in enumerate(w.robot_positions):
            center = (MAP_X+rx*CELL+CELL//2, MAP_Y+ry*CELL+CELL//2)
            pygame.draw.circle(self.screen, (18, 35, 52), center, 12)
            pygame.draw.circle(self.screen, w.robot_colors[idx], center, 9)
            self.text(str(idx+1), center[0]-4, center[1]-7, WHITE, self.small)

    def draw_panel(self):
        w = self.world
        x = PANEL_X
        pygame.draw.rect(self.screen, PANEL, (x, 18, PANEL_W, HEIGHT-36), border_radius=12)
        self.text("RESQBOT", x+18, 34, WHITE, self.heading)
        self.text("MODULAR RESCUE PLATFORM  |  V7", x+18, 62, MUTED, self.small)
        pygame.draw.line(self.screen, (59, 75, 94), (x+18, 88), (x+PANEL_W-18, 88), 1)

        self.text("MISSION STATUS", x+18, 104, MUTED, self.small)
        status_color = GREEN if w.complete else (SURVIVOR if w.running else WHITE)
        # Wrap status into two lines.
        words, lines, line = w.status.split(), [], ""
        for word in words:
            test = (line + " " + word).strip()
            if self.small.size(test)[0] > PANEL_W-38:
                lines.append(line); line = word
            else:
                line = test
        if line: lines.append(line)
        for i, line in enumerate(lines[:3]):
            self.text(line, x+18, 125+i*18, status_color, self.small)

        pygame.draw.line(self.screen, (59, 75, 94), (x+18, 184), (x+PANEL_W-18, 184), 1)
        self.text("MISSION METRICS", x+18, 198, MUTED, self.small)
        metrics = [
            ("Survivors detected", f"{len(w.found)} / {len(w.survivors)}", SURVIVOR),
            ("Survivors assisted", str(len(w.rescued)), GREEN),
            ("Known safe / visible cells", str(len(w.visible)), BLUE),
            ("Movement steps", str(w.steps), WHITE),
            ("Distance travelled", f"{w.distance} cells", WHITE),
            ("Hazards identified", str(len(w.known_hazards)), FIRE),
            ("Map coverage", f"{100*len(w.visible)/(COLS*ROWS):.1f}%", BLUE),
            ("Hazard changes", str(w.hazard_events), FIRE),
            ("Swarm communication links", f"{w.communication_links} / 3", BLUE),
            ("Battery levels R1 / R2 / R3",
             f"{int(w.robot_battery[0])}% / {int(w.robot_battery[1])}% / {int(w.robot_battery[2])}%", GREEN),
        ]
        for i, (label, value, color) in enumerate(metrics):
            yy = 204 + i*27
            self.text(label, x+18, yy, MUTED, self.small)
            self.text(value, x+18, yy+15, color, self.font)

        pygame.draw.line(self.screen, (59, 75, 94), (x+18, 490), (x+PANEL_W-18, 490), 1)
        self.text("CONTROLS", x+18, 502, MUTED, self.small)
        self.draw_button(pygame.Rect(x+18, 530, 112, 36), "Pause" if w.running else "Start", w.running)
        self.draw_button(pygame.Rect(x+142, 530, 112, 36), "New map")
        self.draw_button(pygame.Rect(x+18, 576, 112, 36), "Add rubble")
        self.draw_button(pygame.Rect(x+142, 576, 112, 36), "Reset")
        self.text("E = Export mission data", x+18, 620, MUTED, self.small)
        self.text("LEGEND", x+18, 640, MUTED, self.small)
        legend = [
            (ROBOT, "Rescue robot"),
            (RUBBLE, "Rubble / wall"),
            (FIRE, "Hazard zone"),
            (SURVIVOR, "Detected survivor"),
            (PATH, "Planned route"),
            (UNKNOWN, "Unexplored area"),
        ]
        for i, (color, label) in enumerate(legend):
            yy = 662 + i*17
            pygame.draw.rect(self.screen, color, (x+20, yy, 14, 14), border_radius=3)
            self.text(label, x+44, yy-1, MUTED, self.small)

        self.text("RESQBOT V7  |  Modular multi-agent rescue platform", 26, 27, MUTED, self.small)

    def handle_click(self, pos):
        x = PANEL_X
        if pygame.Rect(x+18,530,112,36).collidepoint(pos):
            self.world.running = not self.world.running
            self.world.status = "Autonomous mission running" if self.world.running else "Mission paused"
        elif pygame.Rect(x+142,530,112,36).collidepoint(pos):
            self.world.generate()
        elif pygame.Rect(x+18,576,112,36).collidepoint(pos):
            self.world.add_obstacle()
        elif pygame.Rect(x+142,576,112,36).collidepoint(pos):
            self.world.__init__()

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_SPACE:
                        self.world.running = not self.world.running
                        self.world.status = "Autonomous mission running" if self.world.running else "Mission paused"
                    elif event.key == pygame.K_n:
                        self.world.generate()
                    elif event.key == pygame.K_r:
                        self.world.__init__()
                    elif event.key == pygame.K_o:
                        self.world.add_obstacle()
                    elif event.key == pygame.K_e:
                        output = export_mission(self.world)
                        self.world.status = f"Mission data exported: {output.name}"
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self.handle_click(event.pos)

            if self.world.running:
                self.accumulator += dt
                if self.accumulator >= MOVE_INTERVAL:
                    self.world.multi_tick()
                    self.accumulator = 0

            self.screen.fill(BG)
            self.draw_map()
            self.draw_panel()
            pygame.display.flip()

        pygame.quit()


