#!/bin/bash

# Start Telegraf
telegraf --config /app/node/telegraf.conf &

# Start the dummy service
python3 /app/shared/dummy_service.py &

# Start the recovery manager
python3 /app/shared/recovery.py &

# Keep container running
tail -f /dev/null 