# Fluxutilmon
Flux Utilization Monitor

The Flux Utilization Monitor (utilmon) is a tool that monitors the utilization of Flux nodes. It collects data about the number of Docker containers running on each node, as well as the amount of CPU, RAM, and SSD storage used by those containers. It also provides information about the total number of nodes and the number of nodes that are not being utilized.

The data collected by utilmon is stored in JSON files. The docker_count_*.json files contain information about the number of Docker containers running on each node, while the utilization_*.json files contain information about the CPU, RAM, and SSD utilization of the nodes.