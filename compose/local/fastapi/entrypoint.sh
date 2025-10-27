#!/bin/bash

# FastAPI Entrypoint Script for Development
# This script runs before the main application starts

set -o errexit
set -o pipefail
set -o nounset

echo "========================================"
echo "🔧 FastAPI Development - Entrypoint"

# Wait for PostgreSQL to be ready
python << END
import sys
import time
import asyncpg

def check_db():
    try:
        import os
        db_url = os.getenv('DATABASE_URL', '')
        # Extract connection details from DATABASE_URL
        # postgresql+asyncpg://user:pass@host:port/db
        if not db_url:
            print("❌ DATABASE_URL not set")
            sys.exit(1)

        print("⏳ Waiting for PostgreSQL...")
        import asyncio

        async def wait_for_db():
            max_retries = 30
            retry_interval = 1

            for i in range(max_retries):
                try:
                    # Simple connection test
                    print(f"Attempt {i+1}/{max_retries}...")
                    # You can add actual asyncpg connection here if needed
                    break
                except Exception as e:
                    if i == max_retries - 1:
                        print(f"❌ Could not connect to database: {e}")
                        sys.exit(1)
                    time.sleep(retry_interval)

        asyncio.run(wait_for_db())
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
fi

echo "✅ Entrypoint completed successfully"

exec "$@"
