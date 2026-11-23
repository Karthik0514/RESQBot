# RESQBOT V7 Architecture

```text
main.py
└── resqbot/
    ├── core/          Shared configuration and grid geometry
    ├── ai/            Reusable AI algorithms (A* pathfinding)
    ├── simulation/   Disaster world, agents, hazards, mission loop
    ├── ui/            Pygame command-centre interface
    └── services/      Mission export and application logging
config/                Default project configuration
docs/                  Architecture and development notes
tests/                 Automated smoke/unit tests
exports/               Generated JSON and CSV mission data
logs/                  Runtime log output
```

## Design principles
- Keep rendering separate from simulation state.
- Keep reusable algorithms in `ai/`.
- Put persistent output in `exports/`, never inside source modules.
- Add new sensors, robot types, planners, and mission objectives as separate modules.
- Keep synthetic demonstration data clearly labelled.

## Current simulation boundary
The environment, thermal detections, survivor triage labels, radio links, battery drain, fire spread, and temporary robot failures are simulated. The system is not connected to physical sensors or real rescue hardware.
