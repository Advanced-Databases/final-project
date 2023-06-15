# Cassandra Scripts
Configuration for 3 cassandra nodes deployed in azure. Each node has the following IPs assigned within a VNET
* cassandra-1: 10.0.0.4
* cassandra-2: 10.0.0.5
* cassandra-3: 10.0.0.6

## Cassandra Installation
We followed the steps provided in the [https://cassandra.apache.org/doc/latest/cassandra/getting_started/installing.html](documentation). Using the method of installation with **Debian Packages**.

After setting that up, we copied each one of the settings available in this repo in the corresponding node and ran the script hardcopy.py to copy the configuration files to the adequate paths and restart the cassandra process so it can accept the new configuration.
