# 🛡️ Enhanced Fault Tolerance System

![License](https://img.shields.io/badge/license-MIT-blue)
![Docker](https://img.shields.io/badge/Docker-ready-brightgreen)
![Status](https://img.shields.io/badge/status-active-success)

A distributed fault-tolerance system that simulates 3 independent nodes with monitoring, fault simulation, recovery capabilities, and process migration using CRIU.

<p align="center">
  <img src="https://user-images.githubusercontent.com/36799599/175767966-220f8184-d58f-4d1d-8a1f-6881290b6c80.png" alt="Fault Tolerance Illustration" width="600">
</p>

## 📋 Table of Contents

- [Prerequisites](#-prerequisites)
- [Quick Start](#-quick-start)
- [Simulating Faults](#-simulating-faults)
- [Process Migration with CRIU](#-process-migration-with-criu)
- [Architecture](#-architecture)
- [Monitoring](#-monitoring)
- [Future Work](#-future-work)
- [Contributing](#-contributing)
- [License](#-license)

## 🔧 Prerequisites

- [Docker](https://www.docker.com/get-started)
- [Docker Compose](https://docs.docker.com/compose/install/)

## 🚀 Quick Start

1. Clone this repository
   ```bash
   git clone https://github.com/Riddhish1/AI-Fault-Tolerance-System.git
   cd AI-Fault-Tolerance-System
   ```

2. Run the system:
   ```bash
   docker-compose up --build
   ```

3. Access Grafana at http://localhost:3000
   - Username: `admin`
   - Password: `admin`

<details>
<summary>View screenshot of Grafana dashboard</summary>
<br>
<p align="center">
  <img src="https://user-images.githubusercontent.com/36799599/175767972-8016778c-0af7-4035-a5a4-b2134dda4f7e.png" alt="Grafana Dashboard" width="800">
</p>
</details>

## 🔄 Simulating Faults

To simulate a fault on any node:

```bash
docker exec node1 python3 /app/shared/simulate_faults.py
```

For an interactive fault simulation experience:

```bash
docker exec node1 python3 /app/shared/simulate_faults.py --interactive
```

Replace `node1` with `node2` or `node3` to simulate faults on other nodes.

<details>
<summary>Available fault simulation options</summary>

| Option | Fault Type | Description |
|--------|------------|-------------|
| 1 | CPU Stress | Simulates high CPU load |
| 2 | Memory Leak | Simulates gradual memory consumption |
| 3 | Disk Fill | Fills disk space rapidly |
| 4 | Process Kill | Kills the target process |
| 5 | Force Migration | Triggers process migration |

</details>

## 🔄 Process Migration with CRIU

This system implements process migration between nodes using CRIU (Checkpoint/Restore In Userspace). When a node experiences high resource usage or imminent failure, the system will:

1. Checkpoint the running process using CRIU
2. Transfer the checkpoint to a healthy node
3. Restore the process on the new node, maintaining state and data

To trigger a process migration manually:

```bash
docker exec node1 python3 /app/shared/simulate_faults.py --interactive
```

Then select option 5 (Force Migration).

<details>
<summary>How Process Migration Works</summary>

1. The source node creates a checkpoint of the running process using CRIU
2. The checkpoint is compressed and transferred to the target node via ZeroMQ
3. The target node decompresses and restores the process
4. The process continues execution from exactly where it left off, with all state preserved

All process state is preserved during migration, including:
- Memory contents
- Open file descriptors
- Process execution state
- Task queue and processed items
</details>

## 🏗️ Architecture

<p align="center">
  <img src="https://user-images.githubusercontent.com/36799599/175767970-f3d0a5c0-8b0f-48a6-af61-b9c3b1bdc79a.png" alt="System Architecture" width="700">
</p>

- 3 independent nodes running in Docker containers
- Each node runs:
  - A dummy service (simulated workload)
  - Telegraf agent (monitoring)
  - ZeroMQ-based communication
  - Fault recovery system
  - CRIU for process checkpointing and migration
- InfluxDB for metrics storage
- Grafana for visualization

## 📊 Monitoring

The system monitors:

| Metric | Description |
|--------|-------------|
| CPU usage | Per-node and per-process CPU utilization |
| Memory usage | Memory consumption patterns |
| Disk usage | Storage utilization and I/O operations |
| Process status | Health and state of key processes |
| Fault events | Detection and logging of system faults |
| Recovery actions | Automatic recovery operation logs |
| Process migrations | Success/failure of migrations |

## 🔮 Future Work

- [ ] Integration of ML models for predictive fault detection
- [ ] Enhanced recovery strategies
- [ ] More sophisticated consensus mechanisms
- [ ] Additional fault simulation scenarios
- [ ] Extended monitoring metrics
- [ ] Multi-process migration coordination

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
