# ByteHub

Django e-commerce training project with custom user model, pages, accounts, and store apps.

## Prerequisites

- Python 3.14+
- Docker Desktop (for PostgreSQL path)
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
- Port `5433` is used to avoid conflicts with local PostgreSQL on `5432`.
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

A fixture file is included at `ByteHub/data_migration.json` for **development only**.
It seeds categories, sample users (all `@example.com`), and products.
The admin seed account (`admin@bytehub.com`) is a superuser — **do not load this
fixture in production or shared environments**.

From Django root (`ByteHub/`):

```powershell
py manage.py loaddata data_migration.json
```

## 8. Run Development Server

From Django root (`ByteHub/`):

```powershell
py manage.py runserver
```

Open:
- http://127.0.0.1:8000/

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

- Data not visible in app after DB edits
  - Confirm app and DB client are connected to same host/port/database.
  - Refresh the browser page.
