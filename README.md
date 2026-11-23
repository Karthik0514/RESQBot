# RESQBOT V7 — Modular Autonomous Rescue Robotics Platform

RESQBOT V7 is a laptop-only, 2D disaster-response robotics simulation. It retains the three-robot cooperative swarm from V6 and reorganizes the code into a maintainable multi-module Python project.

## 1. Requirements
- Windows 10/11
- Python 3.10 or newer
- VS Code (recommended)

## 2. Install and launch
Open the extracted project folder in VS Code. In the integrated terminal:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python main.py
```

If PowerShell blocks virtual-environment activation, run the install and launch commands without activating `.venv`, or use `run_windows.bat`.

## 3. Controls
- `SPACE`: Start / pause mission
- `N`: Generate a new disaster map
- `R`: Reset simulation
- `O`: Add rubble near the lead robot
- `E`: Export current mission data to JSON and CSV
- `ESC`: Quit

## 4. Project structure

```text
RESQBOT_V7/
├── main.py
├── requirements.txt\n├── pyproject.toml
├── run_windows.bat
├── config/
│   └── default.json
├── docs/
│   ├── ARCHITECTURE.md
│   └── ROADMAP.md
├── exports/                 (created when exporting)
├── logs/                    (created at runtime)
├── tests/
│   └── test_smoke.py
└── resqbot/
    ├── core/
    │   ├── config.py
    │   └── geometry.py
    ├── ai/
    │   ├── pathfinding.py\n│   └── task_allocator.py
    ├── simulation/
    │   └── world.py
    ├── ui/
    │   └── app.py
    └── services/
        ├── exporter.py
        └── logging_service.py
```

## 5. Data exports
Press `E` during a mission or while paused. RESQBOT writes:
- `exports/mission_<timestamp>.json`: full mission snapshot, survivor records, hazard records and robot states.
- `exports/mission_<timestamp>_robots.csv`: robot-by-robot telemetry suitable for Excel and analysis.

## 6. Run tests
```powershell
python -m unittest discover -s tests -v
```

## 7. Current capabilities
- Three cooperating simulated rescue robots
- Shared survivor and hazard knowledge
- Risk-aware A* pathfinding\n- Separate urgency-and-distance task-allocation policy
- Evolving hazard zones and dynamic replanning
- Synthetic thermal survivor detection and priority labels
- Simulated battery consumption, automatic return/recharge, and temporary breakdowns
- Mission status, coverage and swarm telemetry
- JSON/CSV export and runtime logs

## Important limitations
All maps, rubble, fire, survivors, sensors, radio links, battery consumption, temporary failures, detection confidence and triage labels are synthetic. Triage is not a medical assessment. "Assisted" means a simulated robot reached and marked a survivor cell; it does not physically rescue anyone. This is an academic simulation, not a deployable rescue system.
