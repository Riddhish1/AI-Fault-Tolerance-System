#!/bin/bash
set -e

# Wait for InfluxDB to start
until curl -s http://localhost:8086/health > /dev/null; do
  echo "Waiting for InfluxDB to start..."
  sleep 1
done

# Create the database
echo "Creating telegraf database..."
curl -X POST "http://localhost:8086/query" --data-urlencode "q=CREATE DATABASE telegraf"

echo "InfluxDB initialization completed." 