#!/bin/bash
celery -A celery_worker.celery_app worker --loglevel=info --concurrency=1 &
gunicorn app:app
