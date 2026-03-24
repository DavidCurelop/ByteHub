# ByteHub

Django e-commerce training project with custom user model, pages, accounts, and store apps.

## 🚀 Quick Start with Docker (Populated Database)

The easiest way to get started is with Docker Compose, which automatically sets up PostgreSQL and loads seed data:

```powershell
# Clone and navigate
git clone <repo-url>
cd ByteHub

# Start with populated database
docker compose up --build
```

Visit **http://localhost:8000** — the database will be ready with sample categories and users!

For detailed Docker instructions, see [DOCKER_SETUP.md](./DOCKER_SETUP.md).

---

## Prerequisites

- Python 3.12+
- Docker Desktop (for PostgreSQL with Docker Compose)
- Git

## Project Structure

- Repository root: contains Docker and env files
- Django project root: `ByteHub/` (contains `manage.py`)
- Virtual environment: `ByteHubEnv/`

## 1. Clone and Enter Repository

```powershell
git clone <repo-url>
cd ByteHub
```

## 2. Create/Activate Virtual Environment

If `ByteHubEnv/` already exists, activate it:

```powershell
& ".\ByteHubEnv\Scripts\Activate.ps1"
```

If it does not exist:

```powershell
py -m venv ByteHubEnv
& ".\ByteHubEnv\Scripts\Activate.ps1"
```

## 3. Install Python Dependencies

```powershell
pip install -r requirements.txt
```

## 4. Configure Environment Variables

Create `.env` at repository root using `.env.example` as base:

```dotenv
# Generate a strong key with:
# python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
DJANGO_SECRET_KEY=change_me_to_a_long_random_secret
DEBUG=true
USE_POSTGRES=true
POSTGRES_DB=bytehub
POSTGRES_USER=bytehub_user
POSTGRES_PASSWORD=change_me
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5433
POSTGRES_CONN_MAX_AGE=60
```

Notes:
- `DJANGO_SECRET_KEY` is **required** in all environments. The app will refuse to start without it.
- `DEBUG` defaults to `false` when unset. Set `DEBUG=true` **explicitly** in your local `.env` for development.
- Port `5433` is used to avoid conflicts with a local PostgreSQL on `5432`.
- Django loads `.env` automatically from settings.

## 5. Start PostgreSQL with Docker

From repository root:

```powershell
docker compose up -d postgres
docker compose ps
```

## 6. Run Migrations

From Django root (`ByteHub/`):

```powershell
cd .\ByteHub
py manage.py migrate
```

## 7. (Optional) Load Seeded Data

A fixture file is included at `ByteHub/dev_seed.json` for **development only**.
It seeds categories, sample users (all `@example.com`), and products.
No superuser is included — run `py manage.py createsuperuser` to create one.

From Django root (`ByteHub/`):

```powershell
py manage.py loaddata dev_seed.json
```

### Dev Seed Credentials

| Email | Password | Role |
|---|---|---|
| `user1@example.com` | `pass1234!` | Regular user |
| `store.manager@example.com` | `manager123!` | Admin (`is_admin=true`, `is_staff=true` — can access `/admin/`) |

> **Note:** These accounts are for **development only**. Never load this fixture in production.

## 8. Run Development Server

From Django root (`ByteHub/`):

```powershell
py manage.py runserver
```

Open:
- http://127.0.0.1:8000/

## Full-Stack Docker Compose

`docker-compose.yml` includes both a `postgres` service and a `web` service that builds and
runs the Django app. The `web` service:
- Always uses PostgreSQL (enforced via environment)
- Auto-runs migrations on startup (dev convenience)
- **Auto-loads seed data from `ByteHub/dev_seed.json`** (set `LOAD_FIXTURE_DATA=true`)

From repository root:

```powershell
# Start both Postgres and the Django web server with seed data
docker compose up --build

# Or start in the background
docker compose up -d --build

# Stop all services
docker compose down

# Reset database and start fresh
docker compose down -v
docker compose up --build
```

Open:
- http://localhost:8000/

### Environment Variables

By default, docker-compose loads `.env` with these settings:
- `USE_POSTGRES=true`: Always uses PostgreSQL in containers
- `LOAD_FIXTURE_DATA=true`: Auto-loads `ByteHub/dev_seed.json`

To disable seed data loading, either:
1. Edit `.env` and set `LOAD_FIXTURE_DATA=false`, or
2. Run: `docker compose up -e LOAD_FIXTURE_DATA=false`

> **Note:** The `web` service in `docker-compose.yml` forces `USE_POSTGRES=true` via its
> `environment` block, so Compose always uses PostgreSQL regardless of your `.env` file.
> Ensure `POSTGRES_PASSWORD` is set in your `.env` before starting Compose.

### Seed Data Reference

The `ByteHub/dev_seed.json` fixture includes:
- **5 Categories**: Electronics, Laptops, Smartphones, Accessories, Gaming
- **Sample Users**: Test accounts with `@example.com` emails
- **Products**: Sample products across categories

See [DOCKER_SETUP.md](./DOCKER_SETUP.md) for details on sharing databases, creating custom seed data, and production deployments.

## SQLite Fallback (without Docker)

Set this in `.env`:

```dotenv
USE_POSTGRES=false
```

Then run:

```powershell
cd .\ByteHub
py manage.py migrate
py manage.py runserver
```

## Common Commands

From repository root:

```powershell
docker compose down
docker compose up -d postgres
```

From Django root (`ByteHub/`):

```powershell
py manage.py makemigrations
py manage.py migrate
py manage.py createsuperuser
py manage.py shell
```

## Troubleshooting

- Error: `role "bytehub_user" does not exist`
  - Ensure Docker container is running and app points to port `5433`.
  - Recreate DB container if needed:

```powershell
docker compose down -v
docker compose up -d postgres
```

- Error: `ModuleNotFoundError: No module named 'dotenv'`

```powershell
pip install python-dotenv
```

- Error: `ImproperlyConfigured: DJANGO_SECRET_KEY environment variable must be set`
  - Copy `.env.example` to `.env` and set a value for `DJANGO_SECRET_KEY`.

- Data not visible in app after DB edits
  - Confirm app and DB client are connected to same host/port/database.
  - Refresh the browser page.
