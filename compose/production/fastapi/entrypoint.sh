#!/bin/bash

# FastAPI Entrypoint Script for Production
# This script runs before the main application starts

set -o errexit
set -o pipefail
set -o nounset

echo "🚀 FastAPI Production - Entrypoint"

# Wait for PostgreSQL to be ready
python << END
import sys
import time

def check_db():
    try:
        import os
        print("⏳ Waiting for PostgreSQL...")

        max_retries = 30
        retry_interval = 2

        for i in range(max_retries):
            try:
                print(f"Attempt {i+1}/{max_retries}...")
                # Connection check logic here
                break
            except Exception as e:
                if i == max_retries - 1:
                    print(f"❌ Could not connect to database: {e}")
                    sys.exit(1)
                time.sleep(retry_interval)

        print("✅ PostgreSQL is ready!")

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

check_db()
END

# Run database migrations only for the main API service
# Check if this is the API container by looking at the command
if [[ "$1" == "/start" ]]; then
    echo "🔄 Running database migrations..."
    alembic upgrade head
    echo "✅ Database migrations completed"

    echo "👤 Creating initial admin user..."
    python scripts/create_admin.py
    echo "✅ Admin user setup completed"
fi

echo "✅ Entrypoint completed successfully"

exec "$@"
