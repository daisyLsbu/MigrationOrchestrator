# MigrationOrchestrator

> A self-contained Python reactive migration engine for Docker containers — continuously reads time-series host metrics from InfluxDB, identifies over-utilised nodes using a scalar threshold, selects the best migration destination based on available resources and network RTT, and executes live container migration over SSH. Designed to be used independently or as the decision-and-execution layer in a larger distributed orchestration pipeline.

---

## Overview

**MigrationOrchestrator** implements **reactive container migration**: it monitors the resource health of every host in a network through a rolling read of InfluxDB data, and automatically migrates Docker containers away from over-utilised hosts to hosts with available capacity — without any manual intervention.

The migration decision pipeline has three distinct, independently extensible stages: **detection** (identifying stressed hosts via a scalar threshold), **selection** (choosing the best destination using resource availability and RTT), and **execution** (transferring the container image via SSH and restoring it on the destination host). Each stage is implemented in a separate module, making the orchestrator straightforward to adapt to different thresholds, scoring strategies, or transfer mechanisms.

---

## How It Works

```
InfluxDB (telemetrydata bucket)
        │
        │  query: Device measurement, last 24h
        │  fields: cpu_percent, vm_percent, storage_percent
        ▼
migrationAgent.py — readFromDB()
        │
        │  convert to scalar: cpu + vm + storage
        │  compare against threshold (default: 150)
        ▼
    victim_set ──── hosts above threshold (source)
    dest_set   ──── remaining hosts (potential destinations)
        │
        │  if victim_set is not empty:
        │    fetch live /combined data from all hosts (currentData.py)
        │    check container resource usage on victim hosts
        │    check available vm_free on destination hosts
        │    fetch RTT from victim to all destination hosts
        ▼
    migrateVictimCntr()
        │
        │  for each flagged container:
        │    match against destination resource availability
        │    select destination with lowest RTT (selectBestRTTValue)
        ▼
connectRemote.py
        │
        ├── sshmigrate(srcIP, cntrId)   → checkpoint container on source
        ├── sshcopy(srcIP, destIP, ...)  → SCP image to destination
        └── sshrestore(destIP)           → restore container on destination
```

The loop runs continuously (`while 1`) in `startmonitoring()`, re-evaluating all hosts at every iteration.

---

## Migration Decision Logic

### 1. Scalar Threshold Detection

Resource utilisation across three dimensions (CPU, virtual memory, storage) is collapsed into a single scalar value:

```
scalar = cpu_percent + vm_percent + storage_percent
```

If the scalar exceeds the configured `threshold` (default: `150`), the host is added to `victim_set` and removed from `dest_set`. The threshold is a single constant at the top of `migrationAgent.py` and can be adjusted without touching any other logic.

### 2. Container Selection

For each victim host, the live `/combined` telemetry endpoint is polled to get real-time container stats. Any container whose combined resource demand (`cpu_usage + nw_usage + memory_usage`) exceeds `2000` is flagged for migration.

### 3. Destination Selection

Candidate destination hosts are those remaining in `dest_set` after victim removal. The orchestrator checks each destination's `vm_free` against the container's resource demand and builds a shortlist of eligible hosts. From that shortlist, the host with the **lowest round-trip time** to the victim is selected as the migration target.

### 4. Migration Execution (connectRemote.py)

Migration is a three-step remote operation executed over SSH using `paramiko` and `scp`:

| Step | Function | Description |
|---|---|---|
| 1 | `sshmigrate(srcIP, cntrId)` | SSH to source; runs `migrateVictim.py` to checkpoint and export the container image |
| 2 | `sshcopy(srcIP, destIP, ...)` | SCP the exported image (`ubuntu-test.img`) from source to destination |
| 3 | `sshrestore(destIP)` | SSH to destination; runs `restoreimage.py` to load and start the container |

---

## Features

- **Continuous monitoring loop** — polls InfluxDB in a tight loop, evaluating all hosts at each cycle
- **Scalar threshold scoring** — compresses multi-dimensional utilisation into a single comparable value; threshold is a single configurable constant
- **Resource-aware destination selection** — filters destination hosts by available memory before considering RTT
- **RTT-based destination ranking** — selects the lowest-latency eligible destination to minimise migration transfer time
- **Container-level flagging** — only containers exceeding a resource demand threshold are migrated, avoiding unnecessary disruption to idle workloads
- **Live data refresh** — when victims are detected, current telemetry is fetched directly from host endpoints (not from stale InfluxDB data) for accurate resource state at migration time
- **SSH-based image transfer** — uses `paramiko` and `scp` for remote container checkpoint, copy, and restore; no proprietary tooling required

---

## Prerequisites

Before running the orchestrator, the following must be in place across the network:

1. **InfluxDB** accessible from the orchestrator node, with telemetry data already being written to the `telemetrydata` bucket (e.g. by [MonitoringApplication](https://github.com/daisyLsbu/MonitoringApplication))
2. **TelemetryApplication** running on each host and reachable via HTTP, exposing the `/combined` endpoint
3. **Docker Engine** installed on all hosts, with the Docker API accessible
4. **SSH access** from the orchestrator to all hosts (username/password as configured in `connectRemote.py`)
5. **`migrateVictim.py`** and **`restoreimage.py`** present on the respective source and destination hosts (provided by the Docker setup and container API project)
6. **`data/nodes.csv`** listing all hosts in the network (same format as MonitoringApplication)

---

## Getting Started

### Installation

```bash
git clone https://github.com/daisyLsbu/MigrationOrchestrator.git
cd MigrationOrchestrator
pip install -r requirements.txt
```

### Configuration

**1. InfluxDB credentials** — update the connection details in `migrationAgent.py`:

```python
token = "<your-influxdb-token>"
org   = "LSBU"
url   = "http://localhost:8086"
```

**2. Migration threshold** — adjust the scalar threshold in `migrationAgent.py` to match your infrastructure's acceptable utilisation level:

```python
threshold = 150   # sum of cpu_percent + vm_percent + storage_percent
```

A threshold of `150` corresponds approximately to an average of 50% across the three resource dimensions. Lower it to trigger migration earlier; raise it to tolerate higher load before intervening.

**3. SSH credentials** — update the username and password in `connectRemote.py` to match your host configuration:

```python
ssh.connect(srcIP, 22, 'ubuntu', 'ubuntu')
```

**4. Host list** — ensure `data/nodes.csv` lists all hosts in the network, matching the format used by MonitoringApplication:

```csv
ip,port,api
192.168.1.10,5000,combined
192.168.1.11,5000,combined
```

### Running the orchestrator

```bash
python migrationAgent.py
```

The orchestrator starts its continuous monitoring loop immediately, reading from InfluxDB and evaluating hosts at each cycle.

---

## Used In

This application has been used as **Part 5 — the reactive migration decision and execution layer** in the following project in this account:

### [reactiveAndPredictiveMigration](https://github.com/daisyLsbu/reactiveAndPredictiveMigration)

---

## Dependencies

| Library | Purpose |
|---|---|
| `influxdb-client` | Query InfluxDB for host metric time-series data |
| `aiohttp` | Async HTTP client for live telemetry polling (`currentData.py`) |
| `asyncio` | Python async event loop |
| `paramiko` | SSH client for remote command execution on hosts |
| `scp` | SCP file transfer over SSH for container image copying |
| `pandas` | CSV parsing for the host list |

Install all dependencies:

```bash
pip install -r requirements.txt
```

> **Note:** SSH access from the orchestrator node to all monitored hosts must be configured and validated before running. The `migrateVictim.py` and `restoreimage.py` scripts must be present on the source and destination hosts respectively.

---

## License

Licensed under the [GNU General Public License v3.0](LICENSE).
