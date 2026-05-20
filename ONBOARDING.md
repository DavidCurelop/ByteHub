# ByteHub — Guía de Onboarding

Bienvenido al equipo 👋 Este documento te lleva de cero a tener el proyecto corriendo localmente en el menor tiempo posible.

---

## Requisitos previos

Antes de clonar el repositorio asegúrate de tener instalado:

- **Python 3.12+** — [python.org/downloads](https://www.python.org/downloads/)
- **Docker Desktop** — [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop/)
- **Git** — [git-scm.com](https://git-scm.com/)
- **Acceso al repositorio** en GitHub (`DavidCurelop/ByteHub`)

> Si no tienes acceso al repo, pídele al líder del proyecto que te agregue como colaborador.

---

## Paso 1 — Clonar el repositorio

```bash
git clone https://github.com/DavidCurelop/ByteHub.git
cd ByteHub
```

---

## Paso 2 — Configurar variables de entorno

Copia el archivo de ejemplo y edítalo:

```bash
cp .env.example .env
```

Abre `.env` y completa los valores. Los campos obligatorios son:

| Variable | Cómo obtenerla |
|----------|---------------|
| `DJANGO_SECRET_KEY` | Genera una con el comando de abajo |
| `POSTGRES_HOST` | Panel de Supabase → Project Settings → Database → Host |
| `POSTGRES_DB` | Panel de Supabase → normalmente `postgres` |
| `POSTGRES_USER` | Panel de Supabase → `postgres` o el usuario configurado |
| `POSTGRES_PASSWORD` | Panel de Supabase → la contraseña de tu proyecto |
| `POSTGRES_PORT` | `5432` (conexión directa) o `6543` (pooler) |

Para generar la `DJANGO_SECRET_KEY`:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

> ⚠️ Nunca commitees el archivo `.env`. Ya está en `.gitignore`.

---

## Paso 3 — Levantar el proyecto

### Opción A — Docker (recomendada)

La forma más rápida. Levanta el servidor con la BD de Supabase y carga datos de prueba automáticamente:

```bash
docker compose up --build
```

Abre [http://localhost:8000](http://localhost:8000) y listo.

### Opción B — Local con entorno virtual

Si preferís correr Django directamente sin Docker:

```bash
# Crear y activar entorno virtual
python -m venv ByteHubEnv

# Windows
.\ByteHubEnv\Scripts\Activate.ps1

# macOS / Linux
source ByteHubEnv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Correr migraciones y servidor
cd ByteHub
python manage.py migrate
python manage.py runserver
```

---

## Paso 4 — Cargar datos de prueba

Si no usaste Docker (que lo hace automáticamente), cargá el seed manualmente:

```bash
cd ByteHub
python manage.py loaddata dev_seed.json
```

Esto crea categorías, productos y los siguientes usuarios de prueba:

| Email | Contraseña | Rol |
|-------|-----------|-----|
| `user1@example.com` | `pass1234!` | Usuario regular |
| `store.manager@example.com` | `manager123!` | Admin — accede a `/admin/` |

> ⚠️ Estos usuarios son **solo para desarrollo local**. No usar en producción.

---

## Paso 5 — Verificar que todo funciona

| URL | Qué debería ver |
|-----|----------------|
| `http://localhost:8000/` | Página principal de la tienda |
| `http://localhost:8000/store/` | Catálogo de productos |
| `http://localhost:8000/accounts/` | Login / registro |
| `http://localhost:8000/admin/` | Panel de administración (con credenciales de manager) |

---

## Estructura del proyecto

```
ByteHub/                  ← raíz del repo
├── ByteHub/              ← proyecto Django
│   ├── manage.py
│   ├── pages/            ← vistas públicas e informativas
│   ├── accounts/         ← autenticación y perfil de usuario
│   └── store/            ← catálogo, productos y categorías
├── Dockerfile
├── docker-compose.yml
├── entrypoint.sh
├── requirements.txt
└── .env.example
```

Para entender la arquitectura completa, revisá [ARCHITECTURE.md](./ARCHITECTURE.md).

---

## Base de datos — Supabase

El proyecto usa **Supabase** como base de datos principal. Pedile al líder del proyecto acceso al proyecto de Supabase para poder ver las tablas, ejecutar queries y gestionar migraciones.

Las migraciones se aplican con:

```bash
cd ByteHub
python manage.py makemigrations  # solo si modificaste un modelo
python manage.py migrate
```

---

## Flujo de trabajo con Git

```bash
# Siempre partí desde main actualizado
git checkout main
git pull

# Creá tu rama con un nombre descriptivo
git checkout -b feature/nombre-de-la-feature

# Commitea seguido con mensajes claros
git add .
git commit -m "feat: descripción corta del cambio"

# Subí tu rama y abrí un Pull Request
git push origin feature/nombre-de-la-feature
```

Antes de abrir un PR asegurate de que las migraciones estén incluidas si modificaste modelos.

---

## Comandos útiles del día a día

```bash
# Servidor de desarrollo
python manage.py runserver

# Crear migraciones después de cambiar un modelo
python manage.py makemigrations

# Aplicar migraciones
python manage.py migrate

# Crear superusuario propio
python manage.py createsuperuser

# Abrir shell de Django (útil para probar queries)
python manage.py shell

# Levantar solo el servidor con Docker
docker compose up

# Reconstruir imagen (tras cambios en requirements.txt)
docker compose up --build

# Bajar todos los servicios
docker compose down
```

---

## Solución de problemas comunes

**`DJANGO_SECRET_KEY environment variable must be set`**
→ Copiá `.env.example` a `.env` y completá la variable.

**`connection refused` o error de conexión a BD**
→ Verificá que `POSTGRES_HOST`, `POSTGRES_USER` y `POSTGRES_PASSWORD` en `.env` coincidan con los del proyecto en Supabase.

**`ModuleNotFoundError: No module named 'X'`**
→ Asegurate de tener el entorno virtual activado y corré `pip install -r requirements.txt`.

**Cambios en el código no se reflejan con Docker**
→ El volumen monta el repo en vivo, debería verse automáticamente. Si no, reiniciá con `docker compose restart web`.

---

## ¿Tenés dudas?

Consultá primero:
1. Este documento y [ARCHITECTURE.md](./ARCHITECTURE.md)
2. El [README.md](./README.md) del repo
3. Al líder del proyecto

---

*Repositorio: [github.com/DavidCurelop/ByteHub](https://github.com/DavidCurelop/ByteHub)*
