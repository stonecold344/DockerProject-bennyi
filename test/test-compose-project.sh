#!/bin/bash

echo -e "\n\n\n-----------------------------------------------------------------------------------------------------------------"
echo "Test Case I: There are at least 5 containers running as part of a Docker Compose project"
echo -e "-----------------------------------------------------------------------------------------------------------------"

RUNNING_CONTAINERS=$(docker ps --filter "status=running" --filter "label=com.docker.compose.project" -q | wc -l)

docker ps --filter "status=running" --filter "label=com.docker.compose.project"

if [ "$RUNNING_CONTAINERS" -lt "5" ]; then
  echo "Found less then 5 running containers"
  exit 1
fi

echo -e "\n✅ Found at least 5 running containers"

echo -e "\n\n\n-----------------------------------------------------------------------------------------------------------------"
echo "Test Case II: There are 3 running MongoDB containers"
echo -e "-----------------------------------------------------------------------------------------------------------------"

# List all running MongoDB containers
MONGO_CONTAINERS=$(docker ps --filter "status=running" --filter "label=type=mongo" --format '{{.ID}}')

# Count the number of MongoDB containers
NUM_CONTAINERS=$(echo "$MONGO_CONTAINERS" | wc -l | tr -d ' ')

# Debug output
echo "Found MongoDB containers: $MONGO_CONTAINERS"
echo "Number of MongoDB containers: $NUM_CONTAINERS"

# Check if exactly 3 MongoDB containers are running
if [ "$NUM_CONTAINERS" -ne 3 ]; then
  echo "Three running mongo containers were not found"
  exit 1
fi

echo -e "\n✅ Found 3 running mongo containers"

echo -e "\n\n\n-----------------------------------------------------------------------------------------------------------------"
echo "Test Case III: Mongo cluster was initialized"
echo -e "-----------------------------------------------------------------------------------------------------------------"

SOME_MONGO_CONTAINER_ID=$(echo "$MONGO_CONTAINER_IDS" | head -n 1)

echo "Connecting to container $SOME_MONGO_CONTAINER_ID and check the replicaSet status:"

rs_status=$(docker exec $SOME_MONGO_CONTAINER_ID mongosh --eval "rs.status()" --quiet)

echo "$rs_status"


# Check if "set" property configured
if  grep -q '"set"' <<< "$rs_status"; then
    echo "Replica set not initialized (The 'set' field is missing)"
    exit 1
fi

echo -e "\n✅ Mongo replicaSet was initialized properly"

echo -e "\n\n\n-----------------------------------------------------------------------------------------------------------------"
echo "Test Case IV: Polybot service is available from the host machine"
echo -e "-----------------------------------------------------------------------------------------------------------------"

response_code=$(curl -s -o /dev/null -w "%{http_code}" localhost:8443)

if [ "$response_code" -ne 200 ]; then
  echo "The polybot service is not available on port 8443 from the host machine"
  exit 1
fi

echo -e "\n✅ The polybot service is available"

