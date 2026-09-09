# TailorSense

TailorSense is a Django application for personalized tailoring and style recommendations. Users will be able to enter measurements and receive suggested styles and designs.

The current API supports user registration, web session login, and JWT authentication for future mobile clients. The living API reference is [docs/API.md](docs/API.md).

## Technology Stack

| Technology | Version / Usage |
|---|---|
| Python | 3.12+ |
| Django | 5.2.6 |
| Django REST Framework | 3.16.1 |
| Simple JWT | 5.5.1 |
| python-dotenv | 1.1.1 |
| Database | SQLite for development |

## Project Structure

```text
TailorSense/
├── apps/
│   ├── core/                 # Landing and authenticated web pages
│   └── users/                # Account API and authentication
│       ├── models.py
│       ├── serializers.py
│       ├── services.py
│       ├── urls.py
│       ├── views.py
│       └── tests/
├── config/                   # Django settings and root routes
├── docs/API.md               # Living API reference
├── static/                   # CSS and images
├── templates/                # Server-rendered HTML
├── .env.example              # Safe environment-variable template
├── manage.py
├── requirements.txt
└── README.md
```

### Main responsibilities

- `apps/users/models.py` — user profile database model.
- `apps/users/serializers.py` — request validation and safe response representations.
- `apps/users/services.py` — account creation and authentication business logic.
- `apps/users/views.py` — API request and response handling.
- `apps/users/urls.py` — user API route definitions.
- `config/settings.py` — environment, DRF, and JWT configuration.
- `config/urls.py` — root routes, including user and token endpoints.
- `docs/API.md` — endpoint contracts, examples, authentication, and planned API areas.

## Installation

Requirements: Python 3.12+, `pip`, and Git.

### Windows

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### macOS or Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Local Environment And Secrets

Secrets should not be placed inside the virtual environment. The virtual environment contains installed packages; the `.env` file contains local configuration and secrets.

Each developer creates a private local `.env` file from the committed example:

```powershell
Copy-Item .env.example .env
```

Generate a unique local Django key:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

Put the generated value in `.env`:

```text
DJANGO_SECRET_KEY=generated-value-here
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost
```

`.env` is ignored by Git. Team members do not need to share your local key. Each developer gets a separate local key, sessions, and JWT signing context. A deployed environment must use its own secret stored in the hosting provider's secret manager.

## Database And Running

Create and apply migrations:

```powershell
python manage.py makemigrations
python manage.py migrate
```

Start the development server:

```powershell
python manage.py runserver
```

Available local routes:

| Route | Purpose |
|---|---|
| `/` | Public landing page |
| `/home/` | Authenticated home page |
| `/admin/` | Django administration |
| `/api/users/` | User account API |
| `/api/token/` | Mobile JWT login |
| `/api/token/refresh/` | Mobile JWT refresh |

## Testing

Run the Django test suite:

```powershell
python manage.py test
```

Run configuration checks:

```powershell
python manage.py check
```

## Security Notes

- Never commit `.env`, passwords, JWTs, or production secrets.
- Use HTTPS outside local development.
- Set `DJANGO_DEBUG=False` in deployed environments.
- Configure `DJANGO_ALLOWED_HOSTS` for the deployed domain.
- Review CSRF, secure cookies, rate limiting, logging, and backups before production.
- Protected endpoints must verify both authentication and ownership of personal data.

For endpoint request and response details, use [docs/API.md](docs/API.md). Update that document whenever an endpoint, field, authentication rule, or token policy changes.
