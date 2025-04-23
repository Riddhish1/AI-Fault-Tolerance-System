# Enhanced Fault Tolerance MVP

A distributed fault-tolerance system that simulates 3 independent nodes with monitoring, fault simulation, recovery capabilities, and process migration using CRIU.

## Prerequisites

- Docker
- Docker Compose

## Quick Start

1. Clone this repository
2. Run the system:
   ```bash
   docker-compose up --build
   ```

3. Access Grafana at http://localhost:3000
   - Username: admin
   - Password: admin

## Simulating Faults

To simulate a fault on any node:

```bash
docker exec node1 python3 /app/shared/simulate_faults.py
```

For an interactive fault simulation experience:

```bash
docker exec node1 python3 /app/shared/simulate_faults.py --interactive
```

Replace `node1` with `node2` or `node3` to simulate faults on other nodes.

## Process Migration with CRIU

This system implements process migration between nodes using CRIU (Checkpoint/Restore In Userspace). When a node experiences high resource usage or imminent failure, the system will:

1. Checkpoint the running process using CRIU
2. Transfer the checkpoint to a healthy node
3. Restore the process on the new node, maintaining state and data

To trigger a process migration manually:

```bash
docker exec node1 python3 /app/shared/simulate_faults.py --interactive
```

Then select option 5 (Force Migration).

### How Process Migration Works

1. The source node creates a checkpoint of the running process using CRIU
2. The checkpoint is compressed and transferred to the target node via ZeroMQ
3. The target node decompresses and restores the process
4. The process continues execution from exactly where it left off, with all state preserved

All process state is preserved during migration, including:
- Memory contents
- Open file descriptors
- Process execution state
- Task queue and processed items

## Architecture

- 3 independent nodes running in Docker containers
- Each node runs:
  - A dummy service (simulated workload)
  - Telegraf agent (monitoring)
  - ZeroMQ-based communication
  - Fault recovery system
  - CRIU for process checkpointing and migration
- InfluxDB for metrics storage
- Grafana for visualization

## Monitoring

The system monitors:
- CPU usage
- Memory usage
- Disk usage
- Process status
- Fault events
- Recovery actions
- Process migrations

## Future Work

- Integration of ML models for predictive fault detection
- Enhanced recovery strategies
- More sophisticated consensus mechanisms
- Additional fault simulation scenarios
- Extended monitoring metrics
- Multi-process migration coordination 