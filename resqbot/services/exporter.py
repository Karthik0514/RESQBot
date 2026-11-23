"""Mission snapshot exporters (JSON + CSV)."""
import csv
import json
from datetime import datetime
from pathlib import Path
from resqbot.core.config import COLS, ROWS

def mission_snapshot(world):
    return {
        "schema_version": "1.0",
        "exported_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "mission": {
            "status": world.status,
            "running": world.running,
            "complete": world.complete,
            "steps": world.steps,
            "distance_cells": world.distance,
            "map_coverage_percent": round(100 * len(world.visible) / (COLS * ROWS), 2),
            "survivors_total": len(world.survivors),
            "survivors_detected": len(world.found),
            "survivors_assisted": len(world.rescued),
            "hazards_known": len(world.known_hazards),
            "hazard_events": world.hazard_events,
            "communication_links": world.communication_links,
        },
        "robots": [
            {
                "robot_id": f"R{i+1}",
                "position": list(world.robot_positions[i]),
                "home": list(world.robot_homes[i]),
                "steps": world.robot_steps[i],
                "battery_percent": round(world.robot_battery[i], 1),
                "returning_to_recharge": world.robot_returning[i],
                "failure_ticks_remaining": world.robot_failure_ticks[i],
            }
            for i in range(3)
        ],
        "survivors": [
            {
                "position": list(pos),
                "detected": pos in world.found,
                "assisted": pos in world.rescued,
                "synthetic_priority": world.triage.get(pos, "UNKNOWN"),
                "synthetic_detection_confidence": world.detection_confidence.get(pos),
            }
            for pos in sorted(world.survivors)
        ],
        "hazards": [
            {"position": list(pos), "intensity": world.hazard_levels.get(pos, 1)}
            for pos in sorted(world.hazards)
        ],
    }

def export_mission(world, output_dir="exports"):
    folder = Path(output_dir)
    folder.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    snapshot = mission_snapshot(world)
    json_path = folder / f"mission_{stamp}.json"
    csv_path = folder / f"mission_{stamp}_robots.csv"
    json_path.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(snapshot["robots"][0].keys()))
        writer.writeheader()
        writer.writerows(snapshot["robots"])
    return json_path
