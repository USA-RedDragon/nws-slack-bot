#!/bin/sh

trap "kill -TERM -$$" SIGINT SIGTERM EXIT

# Check env for CONFIG_JSON
if [ -z "$CONFIG_JSON" ]; then
    echo "CONFIG_JSON is not set"
    exit 1
fi

# Put CONFIG_JSON into config.json
echo -e $CONFIG_JSON > /app/config.json

gunicorn --worker-tmp-dir /dev/shm -D -w 2 -b 0.0.0.0:3000 'src.server:app' --log-file=/dev/shm/gunicorn.log
python -m src.main 2>&1 | tee /dev/null &
tail -f /dev/shm/gunicorn.log
