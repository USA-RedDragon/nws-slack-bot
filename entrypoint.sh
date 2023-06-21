#!/bin/sh

set -xe

cd /app

# Check env for CONFIG_JSON
if [ -z "$CONFIG_JSON" ]; then
    echo "CONFIG_JSON is not set"
    exit 1
fi

# Put CONFIG_JSON into config.json
echo -e $CONFIG_JSON > /app/config.json

touch /tmp/gunicorn.log
gunicorn --worker-tmp-dir /dev/shm -D --log-file=/tmp/gunicorn.log -w 2 -b 0.0.0.0:3000 src.server:app
python -m src.main 2>&1 | tee /dev/null &
exec tail -f /tmp/gunicorn.log
