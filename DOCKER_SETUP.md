# Docker Setup & Populated Database

This project is configured to run with **PostgreSQL** using Docker Compose, with automatic database initialization and seed data loading.

## Quick Start

### Prerequisites
- Docker and Docker Compose installed
- The `.env` file is configured (default values are provided)

### Running with Populated Database

```bash
# Build and start all services (PostgreSQL + Django)
docker compose up --build

# The application will:
# 1. Start PostgreSQL database
# 2. Run migrations
# 3. Load seed data from dev_seed.json
# 4. Start Django development server at http://localhost:8000
```

### Running Without Seed Data

If you want to run migrations without loading the seed fixture:

```bash
docker compose up --build -e LOAD_FIXTURE_DATA=false
```

Or edit `.env` and set `LOAD_FIXTURE_DATA=false` before running compose.

## Architecture

### Containers

- **postgres:16-alpine**: PostgreSQL database
- **web**: Django application with entrypoint script

### Database Configuration

The database persists in a Docker volume (`bytehub_postgres_data`), so data survives container restarts.

**Default credentials** (from `.env`):
- User: `bytehub_user`
- Password: `12345678`
- Database: `bytehub`
- Port (host): `5433`

### Entrypoint Script (`entrypoint.sh`)

The `entrypoint.sh` script automatically:

1. **Waits for database**: Retries connection for up to 30 seconds
2. **Runs migrations**: Applies all pending database migrations
3. **Loads fixtures** (if `LOAD_FIXTURE_DATA=true`): Loads `ByteHub/dev_seed.json`
4. **Starts server**: Runs Django development server

## Seed Data

The `ByteHub/dev_seed.json` file contains:

- **5 Product Categories**: Electronics, Laptops, Smartphones, Accessories, Gaming
- **Sample Users**: Pre-created test accounts

### Using Custom Seed Data

To use different seed data:

1. Replace `ByteHub/dev_seed.json` with your fixture file
2. Rebuild and start: `docker compose up --build`

### Creating Seed Data

Export current database as a fixture:

```bash
# From inside the container or with local Python environment
python manage.py dumpdata --indent 2 > ByteHub/dev_seed.json
```

## Sharing via GitHub

1. **Commit the seed file**:
   ```bash
   git add ByteHub/dev_seed.json
   git commit -m "chore: add seed data"
   git push
   ```

2. **Sharing instructions** (for other developers):
   ```bash
   git clone <repo>
   cd ByteHub
   docker compose up --build
   ```

The database will be automatically populated when containers start.

## Local Development (Without Docker)

To use SQLite locally:

1. Edit `.env` and set `USE_POSTGRES=false`
2. Run migrations:
   ```bash
   python manage.py migrate
   ```
3. Load seed data (optional):
   ```bash
   python manage.py loaddata ByteHub/dev_seed.json
   ```

## Troubleshooting

### Database connection errors

If you see "connection refused" errors:

1. Ensure PostgreSQL container is running: `docker compose ps`
2. Wait a bit longer and manually try health check:
   ```bash
   docker compose exec postgres pg_isready -U bytehub_user -d bytehub
   ```
3. Check container logs:
   ```bash
   docker compose logs postgres
   docker compose logs web
   ```

### Fixture loading failed

If seed data doesn't load:

1. Check that `ByteHub/dev_seed.json` exists
2. Verify fixture format: `python manage.py loaddata --dry-run ByteHub/dev_seed.json`
3. Review container logs: `docker compose logs web`

### Reset database

To start fresh:

```bash
# Stop containers and remove volumes
docker compose down -v

# Rebuild and start
docker compose up --build
```

## Production Considerations

For production deployments:

1. **Environment variables**: Override `.env` values in your deployment platform
2. **Migrations**: Run migrations as a separate step before scaling app servers:
   ```bash
   docker compose run --rm web python manage.py migrate
   ```
3. **No auto-fixture loading**: Set `LOAD_FIXTURE_DATA=false` in production
4. **Backup database**: Use regular PostgreSQL backups, not `.json` fixtures

---

**Questions?** Check [Django Fixture Documentation](https://docs.djangoproject.com/en/6.0/howto/initial-data/)
