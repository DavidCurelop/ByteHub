#!/bin/bash

# Exit on any error
set -e

# Wait for PostgreSQL to be ready using Python
echo "Waiting for database to be ready..."
python << 'EOF'
import os
import time
import psycopg

max_retries = 30
retry_count = 0

db_config = {
    'dbname': os.getenv('POSTGRES_DB', 'bytehub'),
    'user': os.getenv('POSTGRES_USER', 'bytehub_user'),
    'password': os.getenv('POSTGRES_PASSWORD'),
    'host': os.getenv('POSTGRES_HOST', 'postgres'),
    'port': int(os.getenv('POSTGRES_PORT', '5432')),
}

while retry_count < max_retries:
    try:
        conn = psycopg.connect(**db_config)
        conn.close()
        print("Database is ready!")
        break
    except Exception as e:
        retry_count += 1
        if retry_count >= max_retries:
            print(f"Database failed to respond after {max_retries} attempts")
            raise
        print(f"Attempt {retry_count}/{max_retries}: Waiting for database... ({str(e)[:50]})")
        time.sleep(1)
EOF

echo "Running database migrations..."
python manage.py migrate --noinput

# Check if we should load fixture data
if [ "$LOAD_FIXTURE_DATA" = "true" ]; then
    echo "Loading fixture data from dev_seed.json..."
    python manage.py loaddata dev_seed.json || {
        echo "Warning: Could not load dev_seed.json. Continuing without fixture data."
    }
else
    echo "Fixture data loading disabled. Set LOAD_FIXTURE_DATA=true to enable."
fi

echo "Initialization complete! Starting Django server..."

# Start Django development server
exec python manage.py runserver 0.0.0.0:8000
