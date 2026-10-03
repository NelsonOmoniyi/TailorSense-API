# TailorSense

TailorSense is a Django application for personalized tailoring and fabric selection. The core app owns the browser UI and delegates account and fabric operations to JSON APIs.

## Project goals

- Keep the web app and API aligned with the same authenticated user model.
- Protect sensitive fabric inventory data behind authenticated routes.
- Let the core app fetch fabric data from the API and present it in the signed-in dashboard.
- Keep the codebase readable for other developers by using clear comments and app-level documentation.

## Technology stack

| Technology | Version / Usage |
|---|---|
| Python | 3.12+ |
| Django | 5.2.6 |
| Django REST Framework | 3.16.1 |
| Simple JWT | 5.5.1 |
| python-dotenv | 1.1.1 |
| requests | 2.32.3 |
| Database | SQLite for development |

## Project structure

```text
TailorSense/
├── apps/
│   ├── core/                 # All rendered pages and browser form handling
│   ├── fabrics/              # Fabric model and JSON API
│   └── users/                # Account profile and JSON API
├── config/                   # Django settings and project routing
├── templates/                # Shared and app-specific HTML templates
├── static/                   # Shared CSS and static assets
├── .env.example              # Local environment template
├── README.md                 # Project overview and developer setup
├── requirements.txt          # Python dependencies
├── manage.py                 # Django entry point
├── db.sqlite3                # Local SQLite database
├── LICENSE                   # Project license
├── TailorSense_API_Structure_Reference_Guide.docx
└── API User Guide/
    └── API.md                # API reference for the TailorSense app
```

## The apps and what they do

- `apps/core` — owns all HTML pages and browser-facing form handling, and calls the APIs.
- `apps/users` — stores account profile data and provides registration, login, and signout APIs.
- `apps/fabrics` — stores fabric inventory data and provides the fabric API.
- `config` — central Django settings and root URL configuration.
- `templates` — reusable Bootstrap layout and page templates.

The authenticated workspace shell lives in `templates/base.html`. It owns the shared sidebar, search bar, notification menu, account menu, and responsive mobile navigation. Home content lives in `templates/home.html`; Fabrics, Measurements, Styles, and Recommendations each own a `dashboard.html` template in their respective template directories. Measurements, Styles, and Recommendations currently show empty states until their persistence models and APIs are implemented.

## Authentication pattern

- Core renders the public and signed-in pages and handles browser forms.
- The user API provides registration, login, and signout operations.
- The fabric API provides list and add operations and requires an authenticated session.
- Core delegates form operations to APIs using the active session cookies.

## Current API surface

- `POST /api/users/register/` — creates an account and phone profile.
- `POST /api/users/login/` — authenticates credentials and establishes a Django session.
- `POST /api/users/signout/` — ends the authenticated Django session.
- `GET /api/fabrics/list/` — returns the fabric catalog for an authenticated session.
- `POST /api/fabrics/add/` — validates and creates a fabric.

Core-rendered routes include `/`, `/login/`, `/register/`, `/home/`, `/profile/`, `/measurements/`, `/fabrics/`, `/styles/`, `/recommendations/`, `/orders/`, and `/settings/`.
For API request and response formats, refer to [API User Guide/API.md](API%20User%20Guide/API.md).

## Local setup

### 1. Create a virtual environment

Windows:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Create the local environment file

```powershell
Copy-Item .env.example .env
```

Then update the values in `.env`:

```env
DJANGO_SECRET_KEY=replace-with-a-unique-local-secret-key
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost
```

### 4. Run migrations and the app

```bash
python manage.py migrate
python manage.py runserver
```

## Main routes

| Route | Purpose |
|---|---|
| `/` | Public landing page |
| `/login/` | Web login page |
| `/register/` | Web registration page |
| `/home/` | Signed-in home page |
| `/profile/` | Account profile page |
| `/measurements/` | Measurement workspace |
| `/fabrics/` | Authenticated fabric dashboard |
| `/styles/` | Style catalog workspace |
| `/recommendations/` | Recommendation workspace |
| `/orders/` | Order and activity history |
| `/settings/` | Workspace settings |
| `/api/users/register/` | User registration API |
| `/api/users/login/` | User login API |
| `/api/users/signout/` | User signout API |
| `/api/fabrics/list/` | Protected fabric inventory API |
| `/api/fabrics/add/` | Protected fabric creation API |
| `/admin/` | Django administration |

## Fabric API contract

The fabric inventory API is intentionally protected because it is meant for signed-in users only.

Example request:

```http
GET /api/fabrics/list/
Cookie: sessionid=...
```

Example response:

```json
[
  {
    "id": 1,
    "fabric_name": "Cotton Twill",
    "fiber_category": "Natural",
    "fiber": "Cotton",
    "fabric_type": "Twill",
    "composition": "100% Cotton",
    "construction": "Woven",
    "weight": "220 gsm",
    "stretch": "none",
    "structure": "Twill",
    "breathability": "high",
    "opacity": "medium",
    "created_at": "2026-09-18T12:00:00Z",
    "updated_at": "2026-09-18T12:00:00Z"
  }
]
```

## Comments and maintainability

This project keeps comments in the most important app and code blocks so future developers can understand the intent of the architecture without digging through the full project history. Each major feature area now includes docstrings or inline comments explaining what it does and why it exists.

## Notes

- Keep `.env` local and private.
- Do not commit real secrets or production values.
- The current fabric feature is designed for the already-authenticated user flow.
- Bootstrap is used in the shared templates to keep the UI consistent across pages.


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
