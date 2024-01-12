# MigrationOrchestrator
Orchestrates the migration of containers from the over-utilised host to a resource available host in the network.
The data stored in time-series influx DB is read continuously in a moving average for each of the host in the network.
The resource utilisation is converted to scalar and compared to the preset threshold.
For the over utilised hosts, its docker data is checked to identify the container/s to be migrated.
The available resources in the network is checked to identify the destination host/s.
The transmission time from the source host to destination hosts are checked to select the destination host.
The docker is used to host the containers, docker apis are used to aid migration from source to destination host. 

Once a suitable destination host has been selected, it will start transferring the docker image of the identified containers after stopping the container.
ssh is used to transfer the image between hosts as implemented in connectRemote.py

### Prerequisites:
1. The orchestration framework should have access to all relevant information about the infrastructure (eg., IP addresses of machines, their capacity, current load).
2. Each machine must run a daemon that provides information about CPU usage, memory usage, etc
3. There should be an API for querying these metrics. This can be done using any language


