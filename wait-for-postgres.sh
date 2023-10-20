#!/bin/sh

# Check the value of the 'debug' environment variable
if [ "$debug" = "true" ]; then
  # Debug mode: Use 'localhost' as the host
  host="localhost"
else
  # Production mode: Use 'PRODUCTION_HOST' as the host
  host="$PRODUCTION_HOST"
fi

# Check if PostgreSQL is available on the specified host
until PGPASSWORD="$POSTGRES_PASSWORD" pg_isready -h "$host" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB"; do
  echo "Waiting for PostgreSQL to start..."
  sleep 1
done

echo "PostgreSQL is available."