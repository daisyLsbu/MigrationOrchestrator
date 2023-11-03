# MigrationOrchestrator
Orchestrates the migration of containers from the over-utilized host to a resource available host in the network.
The data stored in timeseries influx DB is read continuously in a moving average for each of the host in the network.
The resource utilization is converted to scalar and compared to the preset threshold.
For the over utilized hosts, its docker data is checked to identify the container/s to be migrated.
The available resources in the network is checked to identify the destination host/s.
The transmission time from the source host to destination hosts are checked to select the destination host.
The docker is used to host the containers, docker apis are used to aid migration from source to destination host. 
