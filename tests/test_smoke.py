"""Basic tests for core geometry, planning and mission exports."""
import tempfile
import unittest
from pathlib import Path

from resqbot.core.geometry import inside, manhattan
from resqbot.ai.pathfinding import astar
from resqbot.ai.task_allocator import rank_survivors
from resqbot.simulation.world import RescueWorld
from resqbot.services.exporter import export_mission, mission_snapshot

class TestCore(unittest.TestCase):
    def test_geometry(self):
        self.assertTrue(inside(1, 1))
        self.assertFalse(inside(-1, 1))
        self.assertEqual(manhattan((1, 2), (4, 6)), 7)

    def test_astar(self):
        path = astar((1, 1), (4, 1), set(), {})
        self.assertEqual(path[0], (1, 1))
        self.assertEqual(path[-1], (4, 1))

    def test_world_initializes_three_agents(self):
        world = RescueWorld(seed=7)
        self.assertEqual(len(world.robot_positions), 3)
        self.assertEqual(len(world.robot_battery), 3)

    def test_seeded_worlds_are_reproducible(self):
        first = RescueWorld(seed=21)
        second = RescueWorld(seed=21)
        self.assertEqual(first.walls, second.walls)
        self.assertEqual(first.survivors, second.survivors)

    def test_task_allocator_prioritizes_critical(self):
        cells = [(8, 8), (2, 2), (3, 3)]
        triage = {(8, 8): "CRITICAL", (2, 2): "STABLE", (3, 3): "URGENT"}
        ranked = rank_survivors(cells, triage, (1, 1))
        self.assertEqual(ranked[0], (8, 8))

    def test_export_files(self):
        world = RescueWorld(seed=9)
        with tempfile.TemporaryDirectory() as folder:
            json_path = export_mission(world, folder)
            self.assertTrue(json_path.exists())
            self.assertTrue(json_path.with_name(json_path.stem + "_robots.csv").exists())
        snapshot = mission_snapshot(world)
        self.assertEqual(len(snapshot["robots"]), 3)

if __name__ == "__main__":
    unittest.main()
