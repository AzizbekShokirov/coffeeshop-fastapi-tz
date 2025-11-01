# Coffee Shop API - User Management Module

A production-ready FastAPI application for managing coffee shop users with authentication, authorization, and verification.

## Features

- ✅ User registration and authentication (JWT)
- ✅ Email/SMS verification system
- ✅ Role-based access control (User, Admin)
- ✅ Automatic cleanup of unverified users
- ✅ Async architecture with PostgreSQL
- ✅ Containerized with Docker
- ✅ Background tasks with Celery + Flower monitoring
- ✅ Redis caching and message broker
- ✅ Production-ready with Nginx reverse proxy
- ✅ Database migrations with Alembic
- ✅ Comprehensive logging system (colored console + file logs)

## Tech Stack

- **Framework**: FastAPI 0.115+
- **Database**: PostgreSQL 16 with SQLAlchemy (async)
- **Authentication**: JWT (access + refresh tokens)
- **Password Hashing**: Bcrypt via Passlib
- **Background Tasks**: Celery + Redis
- **Task Monitoring**: Celery Flower
- **Cache/Broker**: Redis 7
- **Web Server**: Nginx (production)
- **Package Manager**: UV (modern, fast Python package manager)
- **Containerization**: Docker & Docker Compose
- **Migrations**: Alembic

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.12+ (for local development)

### 🚀 Development Environment

### Docker Commands (Development)

```bash
# Start all services (PostgreSQL, Redis, API, Celery Worker, Beat, Flower)
docker compose -f local.yml up -d

# Build and start
docker compose -f local.yml up -d --build

# View logs
docker compose -f local.yml logs -f          # All services
docker compose -f local.yml logs -f fastapi      # API only
docker compose -f local.yml logs -f celery_worker   # Celery worker

# Stop services
docker compose -f local.yml down            # Stop containers
docker compose -f local.yml down -v         # Stop and remove volumes (⚠️ This deletes the database!)

# Restart services
docker compose -f local.yml restart fastapi
docker compose -f local.yml restart celery_worker

# Access container shells
docker compose -f local.yml exec fastapi bash           # API container
docker compose -f local.yml exec postgres psql -U postgres  # Database
docker compose -f local.yml exec redis redis-cli    # Redis

# Access the application
# API: http://localhost:8000
# API Docs: http://localhost:8000/docs
# Flower (Celery monitoring): http://localhost:5555 (admin:admin)
```

### 🚀 Production Environment

#### Docker Commands

```bash
# Build and start production environment
docker compose -f production.yml up -d --build

# View logs
docker compose -f production.yml logs -f          # All services
docker compose -f production.yml logs -f fastapi      # API only
docker compose -f production.yml logs -f nginx    # Nginx logs

# Stop services
docker compose -f production.yml down            # Stop containers
docker compose -f production.yml down -v         # Stop and remove volumes

# Restart services
docker compose -f production.yml restart fastapi
docker compose -f production.yml restart nginx

# Access container shells
docker compose -f production.yml exec fastapi bash
docker compose -f production.yml exec postgres psql -U postgres

# Access the application
# API: https://your-domain.com (via Nginx)
# API Docs: https://your-domain.com/docs
```

## API Endpoints

### Authentication (`/api/v1/auth`)

- `POST /auth/signup` - Register a new user
- `POST /auth/login` - Login and receive JWT tokens
- `POST /auth/refresh` - Refresh access token
- `POST /auth/verify` - Verify user email/phone
- `POST /auth/resend-verification` - Resend verification code

### User Management (`/api/v1/users`, `/api/v1/me`)

- `GET /users/me` - Get current authenticated user
- `GET /users` - List all users (Admin only)
- `GET /users/{id}` - Get user by ID (Admin only)
- `PATCH /users/{id}` - Update user details
- `DELETE /users/{id}` - Delete user (Admin only)

## Project Structure

```text
coffeeshop-fastapi-tz/
├── .envs/                      # Environment variables directory
│   ├── local/                  # Development environment variables
│   │   ├── .env.local          # API and security settings
│   │   └── .env.database       # Database credentials
│   └── production/             # Production environment variables
│       ├── .env.production     # API and security settings
│       └── .env.database       # Database credentials
├── alembic/                    # Database migrations
│   ├── versions/               # Migration files
│   ├── env.py                  # Alembic environment
│   └── script.py.mako          # Migration template
├── compose/                    # Docker configurations
│   ├── development/
│   │   ├── fastapi/
│   │   │   ├── celery/
│   │   │   │   ├── beat/
│   │   │   │   │   └── start   # Celery beat script
│   │   │   │   ├── flower/
│   │   │   │   │   └── start   # Flower monitoring script
│   │   │   │   └── worker/
│   │   │   │       └── start   # Celery worker script
│   │   │   ├── Dockerfile      # Dev container image
│   │   │   ├── entrypoint.sh   # Container startup script
│   │   │   └── start           # API start script
│   │   └── postgres/
│   │       ├── maintenance/
│   │       │   └── _sourced/   # Backup/restore helper scripts
│   │       ├── Dockerfile      # PostgreSQL container
│   │       └── postgresql.conf # PostgreSQL configuration
│   └── production/
│       ├── fastapi/
│       │   ├── celery/
│       │   │   ├── beat/
│       │   │   │   └── start   # Celery beat script
│       │   │   └── worker/
│       │   │       └── start   # Celery worker script
│       │   ├── Dockerfile      # Prod container (multi-stage)
│       │   ├── entrypoint.sh   # Prod startup script
│       │   └── start           # Prod API start script
│       ├── nginx/
│       │   ├── ssl/            # SSL certificates directory
│       │   ├── Dockerfile      # Nginx container
│       │   └── nginx.conf      # Nginx configuration
│       └── postgres/
│           ├── maintenance/
│           │   └── _sourced/   # Backup/restore helper scripts
│           ├── Dockerfile      # PostgreSQL container
│           └── postgresql.conf # PostgreSQL configuration
├── logs/                       # Application logs
├── src/                        # Application source code
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   ├── auth.py     # Authentication endpoints
│   │       │   └── users.py    # User management endpoints
│   │       └── router.py       # API v1 router
│   ├── core/
│   │   ├── config.py           # Application settings
│   │   ├── database.py         # Database connection
│   │   ├── dependencies.py     # Dependency injection (auth, db)
│   │   ├── logging.py          # Logging configuration
│   │   ├── middleware.py       # Custom middleware
│   │   └── security.py         # JWT and password utilities
│   ├── models/
│   │   └── user.py             # SQLAlchemy User model
│   ├── repositories/
│   │   └── user_repository.py  # Data access layer
│   ├── schemas/
│   │   └── user.py             # Pydantic schemas for validation
│   ├── services/
│   │   ├── auth_service.py     # Business logic for auth
│   │   └── user_service.py     # Business logic for users
│   ├── tasks/
│   │   └── celery_app.py       # Celery configuration
│   └── main.py                 # FastAPI application entry point
├── tests/                      # Test suite
│   └── api/
│       └── v1/
│           ├── test_auth.py    # Auth endpoint tests
│           └── test_users.py   # User endpoint tests
├── .dockerignore               # Docker ignore patterns
├── .gitattributes              # Git attributes
├── .gitignore                  # Git ignore patterns
├── .pre-commit-config.yaml     # Pre-commit hooks configuration
├── .python-version             # Python version specification
├── alembic.ini                 # Alembic configuration
├── local.yml                   # Development docker-compose
├── production.yml              # Production docker-compose
├── pyproject.toml              # Python dependencies (UV)
├── README.md                   # This file
└── uv.lock                     # UV lock file
```

## Architecture

### Layered Architecture

1. **API Layer** (`src/api/`)
   - Handles HTTP requests/responses
   - Input validation via Pydantic
   - Route definitions

2. **Service Layer** (`src/services/`)
   - Business logic
   - Orchestrates operations between repositories
   - Handles transactions

3. **Repository Layer** (`src/repositories/`)
   - Data access abstraction
   - Database queries
   - ORM operations

4. **Model Layer** (`src/models/`)
   - SQLAlchemy ORM models
   - Database schema definitions

### Task Processing with Celery

- **Celery Worker**: Processes asynchronous tasks
- **Celery Beat**: Schedules periodic tasks (e.g., cleanup unverified users)
- **Celery Flower**: Web-based monitoring tool for Celery

## Production Considerations

This project includes production-ready configurations:

1. **Multi-stage Docker builds** - Optimized image sizes
2. **Nginx reverse proxy** - With rate limiting and SSL support
3. **Non-root container user** - Security hardening
4. **Health checks** - For all services
5. **Restart policies** - Automatic recovery
6. **Security options** - Read-only filesystem, tmpfs for temp files
7. **Resource limits** - CPU and memory constraints

For production deployment:

1. Update environment variables in `.envs/production/`
2. Add SSL certificates to `compose/production/nginx/ssl/`
3. Update `nginx.conf` with your domain
4. Run `docker compose -f production.yml up -d --build`

## License

MIT

## Author

Azizbek Shokirov - [GitHub](https://github.com/AzizbekShokirov)
