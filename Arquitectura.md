# ByteHub — Arquitectura del Proyecto

> Tienda de tecnología para componentes y periféricos de PC, construida como proyecto de entrenamiento con Django.

---

## Stack Tecnológico

| Capa | Tecnología |
|------|-----------|
| Backend | Python 3.12 + Django |
| Base de datos (principal) | Supabase (PostgreSQL gestionado) |
| Base de datos (fallback) | SQLite |
| Contenedores | Docker + Docker Compose |
| Frontend | HTML / Templates Django |
| Lenguajes | Python 63 % · HTML 36 % · Otros 1 % |

---

## Estructura del Repositorio

```
ByteHub/                        ← Raíz del repositorio
├── ByteHub/                    ← Raíz del proyecto Django (contiene manage.py)
│   ├── manage.py
│   ├── dev_seed.json           ← Fixture de datos de desarrollo
│   └── <apps Django>
│       ├── pages/              ← App de páginas estáticas
│       ├── accounts/           ← App de autenticación y usuarios
│       └── store/              ← App principal de la tienda
├── Dockerfile                  ← Imagen Python 3.12-slim
├── docker-compose.yml          ← Servicios: postgres + web
├── entrypoint.sh               ← Script de arranque (migraciones + fixture)
├── requirements.txt            ← Dependencias Python
├── .env.example                ← Plantilla de variables de entorno
├── .dockerignore
├── .gitignore
├── DOCKER_SETUP.md
└── README.md
```

---

## Apps de Django

### `pages`
Maneja las páginas informativas del sitio (inicio, about, etc.). No requiere autenticación.

### `accounts`
Gestión de usuarios con modelo de usuario personalizado (`custom user model`). Incluye registro, login, logout y perfiles.

### `store`
Núcleo del e-commerce. Gestiona el catálogo de productos y categorías. Incluye las 5 categorías del seed: Electronics, Laptops, Smartphones, Accessories, Gaming.

---

## Infraestructura con Docker

```
┌──────────────────────────────────────────────────────┐
│                  Docker Compose                       │
│                                                       │
│  ┌──────────────┐          ┌────────────────────────┐ │
│  │   web        │─────────▶│   Supabase (cloud)     │ │
│  │  (Django)    │  remoto  │   PostgreSQL gestionado │ │
│  │  :8000       │          └────────────────────────┘ │
│  └──────────────┘                                     │
│         │                                             │
│         ▼                                             │
│   entrypoint.sh                                       │
│   - migrate                                           │
│   - loaddata (opt)                                    │
└──────────────────────────────────────────────────────┘
```

> El `docker-compose.yml` incluye un servicio `postgres` local activable con el profile `localdb` (útil para desarrollo sin conexión), pero la base de datos real del proyecto es **Supabase**.

### Servicio `web`
- Construido desde el `Dockerfile` local
- Trabaja en `/app/ByteHub` (raíz Django)
- Monta el repositorio en `/app` (hot-reload en desarrollo)
- Ejecuta `entrypoint.sh` al arrancar:
  - Corre migraciones automáticamente
  - Carga `dev_seed.json` si `LOAD_FIXTURE_DATA=true`

---

## Dockerfile

```
python:3.12-slim
  └── crea usuario sin privilegios (appuser:appgroup)
  └── instala requirements.txt
  └── copia código fuente
  └── WORKDIR /app/ByteHub
  └── EXPOSE 8000
  └── ENTRYPOINT entrypoint.sh
```

El contenedor corre como usuario no-root por seguridad.

---

## Variables de Entorno

| Variable | Descripción | Default |
|----------|-------------|---------|
| `DJANGO_SECRET_KEY` | Clave secreta de Django (requerida) | — |
| `DEBUG` | Modo debug | `false` |
| `USE_POSTGRES` | Activa PostgreSQL (false → SQLite) | `true` |
| `POSTGRES_DB` | Nombre de la base de datos | `bytehub` |
| `POSTGRES_USER` | Usuario de PostgreSQL | `bytehub_user` |
| `POSTGRES_PASSWORD` | Contraseña de PostgreSQL | `bytehub_dev_password` |
| `POSTGRES_HOST` | Host de Supabase (connection pooler o direct) | URL de Supabase |
| `POSTGRES_PORT` | Puerto de conexión | `5432` / `6543` (pooler) |
| `POSTGRES_CONN_MAX_AGE` | Tiempo máximo de conexión (s) | `60` |
| `LOAD_FIXTURE_DATA` | Carga seed al iniciar contenedor | `true` |

---

## Flujo de Datos

```
Browser
  │
  ▼
Django (puerto 8000)
  │
  ├── /            → pages app (vistas públicas)
  ├── /accounts/   → accounts app (auth, perfil)
  ├── /store/      → store app (catálogo, productos)
  └── /admin/      → Django Admin
          │
          ▼
     Supabase (PostgreSQL cloud)
     └── Esquema Django ORM
         ├── Usuarios (custom user model)
         ├── Productos
         └── Categorías
```

---

## Datos de Seed (Desarrollo)

El fixture `dev_seed.json` incluye:

- **5 categorías**: Electronics, Laptops, Smartphones, Accessories, Gaming
- **Usuarios de prueba** (`@example.com`)
- **Productos** de muestra por categoría

| Email | Contraseña | Rol |
|-------|-----------|-----|
| `user1@example.com` | `pass1234!` | Usuario regular |
| `store.manager@example.com` | `manager123!` | Admin (`is_admin=true`, acceso a `/admin/`) |

> ⚠️ Estos datos son **solo para desarrollo**. No cargar en producción.

---

## Modos de Ejecución

### Docker (recomendado)
```bash
docker compose up --build
# → http://localhost:8000 con BD y seed listos
```

### Local apuntando a Supabase
```bash
# Configurar .env con credenciales de Supabase
cd ByteHub && py manage.py migrate && py manage.py runserver
```

### SQLite (sin Docker)
```bash
# En .env: USE_POSTGRES=false
cd ByteHub && py manage.py migrate && py manage.py runserver
```

---

## CI / GitHub Actions

El repositorio incluye configuración en `.github/` para workflows de GitHub Actions (detalles en el directorio `.github/`).


<img width="2804" height="2464" alt="image" src="https://github.com/user-attachments/assets/8d9b22e4-d91b-480f-9f34-c5f7815fae3b" />


---

*Repositorio: [github.com/DavidCurelop/ByteHub](https://github.com/DavidCurelop/ByteHub)*
