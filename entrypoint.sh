#!/bin/sh

# Check env for CONFIG_JSON
if [ -z "$CONFIG_JSON" ]; then
    echo "CONFIG_JSON is not set"
    exit 1
fi

# Put CONFIG_JSON into config.json
echo -e $CONFIG_JSON > /app/config.json

exec $@
