# Django Starter Template

A clean, reusable Django starter project intended to serve as a foundation for new Django web applications.

This repository contains the basic Django project structure, a starter application, URL routing, Django's built-in administration/authentication/session framework, SQLite development database configuration, and the standard WSGI/ASGI entry points.

> **Template status:** This is a minimal starter foundation. Application-specific business logic, models, authentication customisation, APIs, and production infrastructure can be added as a project grows.

## Features

- Django 6.1
- Standard Django project structure
- Starter application (`apps/core`)
- User application (`apps/users`)
- Django Admin
- Django authentication and session framework
- SQLite database for local development
- URL routing with application-level `urls.py`
- WSGI and ASGI entry points
- Django static-file configuration
- Basic password validation
- Django test framework scaffold

## Technology Stack

| Technology | Version / Usage |
|---|---|
| Python | 3.12+ |
| Django | 6.1 |
| Database | SQLite (development default) |
| Web interfaces | WSGI / ASGI |
| Version control | Git / GitHub |

## Project Structure

```text
Starter/
├── apps/
│   ├── __init__.py
│   ├── api/
│   ├── users/
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   ├── views.py
│   │   └── tests/
│   └── core/
│       ├── __init__.py
│       ├── admin.py
│       ├── apps.py
│       ├── models.py
│       ├── tests.py
│       ├── urls.py
│       └── views.py
│
├── config/
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── templates/
│
├── manage.py
├── requirements.txt
└── README.md
```

### `config/`

The main Django project configuration.

- `settings.py` — project settings and installed applications.
- `urls.py` — root URL configuration.
- `asgi.py` — ASGI entry point.
- `wsgi.py` — WSGI entry point.

### `apps/core/`

The initial reusable Django application.

- `views.py` — application views.
- `urls.py` — application URL routes.
- `models.py` — database models.
- `admin.py` — Django Admin registrations.
- `tests.py` — application tests.
- `apps.py` — Django application configuration.

### `apps/api/`

Reserved for API-specific endpoints and application logic.

### `apps/users/`

Responsible for user and account-related API concerns.

- `models.py` — user-domain data models.
- `serializers.py` — user data representations and request validation.
- `views.py` — user-related API request handling.
- `urls.py` — user API route definitions.
- `tests/` — user API and data behavior tests.

### `templates/`

Reserved for project-level HTML templates.

For example:

```text
templates/
├── base.html
├── home.html
└── ...
```

The current template folder is intentionally empty.

## Requirements

- Python 3.12 or newer
- `pip`
- Git
- A virtual environment (recommended)

Django 6.1 is currently pinned in `requirements.txt`.

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/<your-repository>.git
cd <your-repository>
```

### 2. Create a virtual environment

#### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

#### macOS / Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Upgrade pip

```bash
python -m pip install --upgrade pip
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

## Running the Project

Before starting the server, apply the initial migrations:

```bash
python manage.py migrate
```

Start the development server:

```bash
python manage.py runserver
```

Open:

```text
http://127.0.0.1:8000/
```

The starter application's current home route is:

```text
http://127.0.0.1:8000/app/
```

Django Admin is available at:

```text
http://127.0.0.1:8000/admin/
```

## Creating an Administrator

Create a Django superuser with:

```bash
python manage.py createsuperuser
```

Follow the prompts, then sign in through the Admin URL.

## URL Configuration

The root project currently exposes two routes:

| Route | Purpose |
|---|---|
| `/admin/` | Django administration |
| `/app/` | Starter application |

The `/app/` route is connected through `config/urls.py`:

```python
path('app/', include('apps.core.urls'))
```

The starter application's home view currently returns a simple HTTP response.

As the project develops, application routes should remain inside the relevant app's `urls.py` and be included from the root URL configuration.

## Database

The starter uses SQLite by default:

```text
db.sqlite3
```

SQLite is convenient for development and prototyping. For production applications, consider using a production database such as PostgreSQL.

After changing models:

```bash
python manage.py makemigrations
python manage.py migrate
```

## Static Files

Django's static-file system is enabled with:

```python
STATIC_URL = 'static/'
```

As the project grows, static assets can be organised into a dedicated `static/` directory and configured further for deployment.

## Testing

Run Django's test suite with:

```bash
python manage.py test
```

Add application-specific tests to:

```text
apps/core/tests.py
```

For larger projects, tests can later be split into a dedicated test package.

## Creating Additional Applications

Create a new application with:

```bash
python manage.py startapp <app_name>
```

For a larger project, a common structure is:

```text
apps/
├── accounts/
├── dashboard/
├── payments/
└── ...
```

After creating an app, add it to `INSTALLED_APPS` in `config/settings.py` and include its URL configuration where appropriate.

## Recommended Development Workflow

1. Create a new repository from this starter.
2. Rename `apps/core` to a meaningful application name if appropriate.
3. Update the project configuration and application names.
4. Create your models.
5. Create and apply migrations.
6. Add views and URL routes.
7. Add templates and static assets.
8. Add tests.
9. Configure environment-specific settings.
10. Review security settings before deployment.

## Environment & Secrets

The current starter stores `SECRET_KEY` directly in `config/settings.py`. **Do not reuse the current secret key for a real application.**

Before publishing this repository or using it for a real project:

- Generate a new secret key.
- Move secrets and environment-specific configuration into environment variables.
- Set `DEBUG = False` in production.
- Configure `ALLOWED_HOSTS`.
- Configure CSRF trusted origins where necessary.
- Never commit passwords, API keys, tokens, database credentials, or `.env` files.

A future improvement for this template is to introduce environment-based settings using a `.env` file and a package such as `django-environ` or `python-decouple`.

## Production Checklist

Before deploying a project created from this template:

```bash
python manage.py check --deploy
```

Also review:

- `DEBUG`
- `SECRET_KEY`
- `ALLOWED_HOSTS`
- HTTPS
- Secure cookies
- CSRF configuration
- Static file serving
- Database configuration
- Logging
- Error monitoring
- Database backups
- Dependency updates

The built-in development server (`runserver`) should not be used as the production web server.

## Using This Repository as a GitHub Template

This repository is intended to be reusable.

After pushing it to GitHub, enable **Template repository** in the repository settings. This allows a new Django project to be created from the starter without treating the starter itself as the application being developed.

When creating a project from the template:

1. Create a new repository from the template.
2. Clone the new repository locally.
3. Create a fresh virtual environment.
4. Install `requirements.txt`.
5. Replace or rename `apps/core` as needed.
6. Generate a new Django `SECRET_KEY`.
7. Configure environment-specific settings.
8. Run migrations.
9. Start development.

## Important Notes Before Publishing

The uploaded starter currently contains a local `venv/` directory and Python bytecode/cache files. **These should not be committed to GitHub.**

Your repository should generally exclude:

```text
venv/
__pycache__/
*.pyc
*.pyo
db.sqlite3
.env
```

Use a `.gitignore` file to enforce this.

The local virtual environment is not required in the repository because `requirements.txt` is the reproducible dependency definition.

## Known Cleanup Items

Before treating this as a polished GitHub template, the following should be addressed:

- Remove the local `venv/` directory from the Git repository.
- Remove Python `__pycache__` and `.pyc` files.
- Replace the hard-coded Django secret key with environment-based configuration.
- Consider adding a `.gitignore`.
- Consider renaming `apps/core` to a more intentional starter application name.
- Consider adding a base HTML template and static directory if this template is intended for server-rendered web applications.
- Consider separating development and production settings as the template becomes more sophisticated.

## License

Add your preferred license here.

For a personal starter template that you intend to reuse publicly, the MIT License is a common permissive choice. If you choose MIT, add a `LICENSE` file containing the appropriate license text.

---

## Maintainer

Maintained as a personal Django starter template for rapid project bootstrapping.

Built with Django.
