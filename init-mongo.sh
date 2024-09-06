#!/bin/bash
mongo1_container=$(docker ps --filter "name=mongo1" --format "{{.ID}}")
docker exec $mongo1_container mongosh --eval '
rs.status().ok === 1 ? print("Replica set already initialized.") : rs.initiate({_id: "rs0", members: [{_id: 0, host: "mongo1:27017"}, {_id: 1, host: "mongo2:27018"}, {_id: 2, host: "mongo3:27019"}]})
'
