# RESQBOT Development Roadmap

## V7 foundation
- Modular package structure and entry point
- Separate pathfinding module
- Three-agent swarm simulation retained
- JSON + CSV mission export
- Runtime logging and smoke tests

## Possible next modules
- `ai/task_allocator.py`: auction / utility-based task assignment
- `ai/exploration.py`: frontier scoring and map coverage
- `simulation/sensors/`: thermal, lidar and gas sensor models
- `simulation/communication.py`: radio range, latency and packet loss
- `simulation/power.py`: energy model and charging station strategy
- `analytics/`: mission KPI calculations and plots
- `ui/panels/`: dedicated robot, map and mission analytics panels
- `scenarios/`: reusable disaster maps and reproducible random seeds
