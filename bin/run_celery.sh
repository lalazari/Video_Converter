#!/bin/bash
until nc -z broker 5672; do
    echo "$(date) - waiting broker container to get up ..."
    sleep 1
done
# Spawn 1 worker on the background
celery -A celery_tasks --loglevel=info
