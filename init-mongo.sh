#!/bin/bash

# Check if MongoDB is up
#echo "Waiting for MongoDB to be available..."
#until nc -z mongo1 27017; do
#  sleep 1
#done

echo "MongoDB is up, initializing replica set..."

# Run the initialization script
mongo1_container=$(docker ps --filter "name=mongo1" --format "{{.ID}}")
docker exec $mongo1_container mongosh --eval '
rs.initiate({
  _id: "rs0",
  members: [
    {_id: 0, host: "mongo1:27017"},
    {_id: 1, host: "mongo2:27018"},
    {_id: 2, host: "mongo3:27019"}
  ]
})
'

echo "Replica set initialization script executed."
