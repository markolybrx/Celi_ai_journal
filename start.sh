#!/bin/bash

# Start the Celery worker in the background
celery -A app.celery_app worker --loglevel=info &

# Start the Gunicorn server with Gevent (Async)
# -k gevent: Enables asynchronous handling for multiple users
# --timeout 120: Gives Gemini time to think without crashing
exec gunicorn app:app -k gevent --bind 0.0.0.0:$PORT --timeout 120
