#!/usr/bin/env bash


# Run Django migrations
echo "Running Django migrations..."

# DISABLED DUE TO READ ONLY FILE SYSTEM
# python manage.py makemigrations

# Migrate db
python manage.py migrate

# Launch backend (moved from Dockerfile to run after securely setting Prince license)
echo "Launching gunicorn..."
exec gunicorn config.wsgi --bind 0.0.0.0:8000 --timeout 300 --graceful-timeout 90 --max-requests 2048 --workers 4 --preload
