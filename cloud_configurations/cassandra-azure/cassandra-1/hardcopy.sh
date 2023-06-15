sudo cp ~/cassandra_settings/cassandra.yaml /etc/cassandra/cassandra.yaml
sudo cp ~/cassandra_settings/cassandra-rackdc.properties /etc/cassandra/cassandra-rackdc.properties
# cp ~/cassandra_settings/cqlshrc ~/.cassandra/cqlshrc

sudo service cassandra stop
sudo rm -f /var/log/cassandra/system.log
sudo rm -rf /var/lib/cassandra/*
sudo service cassandra restart

# tail -100 /var/log/cassandra/system.log