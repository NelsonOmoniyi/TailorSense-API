# TailorSense API User Guide

**Base URL:** `http://127.0.0.1:8000`

This guide documents the interfaces that are actually implemented in the current project. It is intentionally aligned with the codebase, not with an earlier conceptual design.

## Current project reality

The current TailorSense app uses a mixed architecture:

- Public user access is handled by server-rendered Django pages for register and login.
- Signed-in user pages use Django session authentication.
- The only JSON API currently implemented in this project is the authenticated fabric inventory API.
- The core app fetches that API using the active user session and then passes the data to the web interface.

This means the project is not yet a full JWT-first JSON API service for every user action. The user account flow is still web-based for now, and the fabric feature is the first authenticated API exposed to the app.

## Authentication model

### Web app authentication

- Anonymous users can access `/` and `/login/` and `/register/`.
- After login, the app sets a Django session cookie.
- Protected pages such as `/home/` and `/fabrics/` rely on the user session.

### API authentication

- Browser-based API requests use the active session cookie.
- The API expects an authenticated Django user session, not a separate API key.
- For the current implementation, session authentication is the supported pattern for the fabric API.

## Implemented endpoints

### 1. Public web pages

| Method | Endpoint | Auth | Purpose |
|---|---|---|---|
| `GET` | `/` | None | Public landing page |
| `GET` / `POST` | `/login/` | None | Login page and authentication |
| `GET` / `POST` | `/register/` | None | Registration page and user creation |

### 2. Signed-in web pages

| Method | Endpoint | Auth | Purpose |
|---|---|---|---|
| `GET` | `/home/` | Session user | Signed-in dashboard shell |
| `POST` | `/signout/` | Session user | Logout action |
| `GET` | `/fabrics/` | Session user | Fabric dashboard page |

### 3. Fabric API

| Method | Endpoint | Auth | Purpose |
|---|---|---|---|
| `GET` | `/api/fabrics/list/` | Session-authenticated user | Return all fabrics available in the system |

## How the fabric API is used

The signed-in dashboard flow is:

1. A user logs in through Django's web login.
2. The browser keeps the session cookie.
3. The core app calls `/api/fabrics/list/` with that session attached.
4. The API returns the fabric list as JSON.
5. The view passes that data to the template.
6. The template renders the inventory in Bootstrap cards.

This keeps the UI and the data flow aligned with the current app architecture.

## Example request: fabric list

```http
GET /api/fabrics/list/
Cookie: sessionid=your-session-cookie
```

### Example response

```json
[
  {
    "id": 1,
    "name": "Cotton Twill",
    "category": "Cotton",
    "composition": "100% Cotton",
    "color": "Navy",
    "weight_gsm": 220,
    "price_per_meter": "12.50",
    "stock_units": 25,
    "supplier": "Local Mill",
    "created_at": "2026-09-18T12:00:00Z",
    "updated_at": "2026-09-18T12:00:00Z"
  }
]
```

## Expected response behavior

- `200 OK` when the user is authenticated and fabric records are found.
- Empty array `[]` when the user is authenticated but no fabrics exist yet.
- An authentication failure when the session is not valid.

## Future API expansion

The project may grow to include more JSON endpoints later, such as:

- user registration API
- user login API
- user profile API
- JWT token endpoints
- additional inventory and tailoring APIs

These are not currently implemented in this branch. This guide intentionally documents the live implementation rather than hypothetical features.

## Important guidance for developers

- Do not treat unimplemented routes as if they exist in production code.
- Keep this guide updated whenever new endpoints are added or old ones change.
- When a feature is intentionally web-only, it should be clearly labelled as such.
- Use session authentication for browser-driven app flows and reserve JWT-based APIs for true API clients when needed later.
