#!/bin/bash

# Copy ML model to app directory if not already there
cp -n /my_model.keras /app/ 2>/dev/null || true

# Start Telegraf
telegraf --config /app/node/telegraf.conf &

# Start the dummy service
python3 /app/shared/dummy_service.py &

# Start the recovery manager
python3 /app/shared/recovery.py &

# Start the ML fault detector
python3 /app/shared/ml_fault_detector.py &

# Keep container running
tail -f /dev/null 