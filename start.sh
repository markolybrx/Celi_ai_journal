#!/bin/bash

# 1. Start the Celery Worker (The Chef)
# --concurrency=1 limits it to 1 task at a time (Crucial for Free Tier)
# The '&' at the end makes it run in the background
celery -A celery_worker.celery_app worker --loglevel=info --concurrency=1 &

# 2. Start the Web Server (The Waiter)
# This runs in the foreground and keeps the Render service alive
gunicorn app:app
