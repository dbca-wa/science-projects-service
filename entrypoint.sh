#!/bin/bash
set -e

echo "=== SPMS Backend Startup ==="
echo "Starting at: $(date)"

# Run database migrations
echo ""
echo "=== Running Database Migrations ==="
python manage.py migrate --noinput

# Run one-time caretaker data migration (idempotent - safe to run multiple times)
echo ""
echo "=== Checking Caretaker Data Migration ==="
python manage.py migrate_caretaker_data

# Collect static files (if needed)
# echo ""
# echo "=== Collecting Static Files ==="
# python manage.py collectstatic --noinput

echo ""
echo "=== Starting Gunicorn ==="
echo "Listening on 0.0.0.0:8000"
echo ""

# Start gunicorn
exec gunicorn config.wsgi \
    --bind 0.0.0.0:8000 \
    --timeout 300 \
    --graceful-timeout 90 \
    --max-requests 2048 \
    --workers 4 \
    --preload
