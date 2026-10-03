# TailorSense API User Guide

**Base URL:** `http://127.0.0.1:8000`

This guide documents the interfaces that are actually implemented in the current project. It is intentionally aligned with the codebase, not with an earlier conceptual design.

## Current project reality

The core app owns all server-rendered HTML and browser form handling. It delegates account and fabric operations to JSON APIs. Authentication uses Django sessions.

## Authentication model

### Browser authentication

- Anonymous users can access `/` and `/login/` and `/register/`.
- Core submits login to the user API and relays the resulting session cookie to the browser.
- Protected pages such as `/home/` and `/fabrics/` rely on the user session.

### API authentication

- Core passes the active session cookie when calling authenticated APIs.
- Fabric and measurement profile operations plus signout require a valid authenticated Django session.
- Measurement type lookup requires an authenticated Django session so the dashboard uses the same access boundary.
- Registration and login are public JSON API endpoints.

## Implemented endpoints

### 1. Core-rendered pages

| Method | Endpoint | Auth | Purpose |
|---|---|---|---|
| `GET` | `/` | None | Public landing page |
| `GET` / `POST` | `/login/` | None | Login page; form delegates to the user API |
| `GET` / `POST` | `/register/` | None | Registration page; form delegates to the user API |

### 2. Signed-in web pages

| Method | Endpoint | Auth | Purpose |
|---|---|---|---|
| `GET` | `/home/` | Session user | Signed-in dashboard shell |
| `POST` | `/signout/` | Session user | Signout action; delegates to the user API |
| `GET` | `/fabrics/` | Session user | Fabric dashboard page |

### 3. User API

| Method | Endpoint | Auth | Purpose |
|---|---|---|---|
| `POST` | `/api/users/register/` | None | Create an account and phone profile |
| `POST` | `/api/users/login/` | None | Authenticate email/password and establish a session |
| `POST` | `/api/users/signout/` | Session user | Invalidate the current session |

Registration request fields: `fullname`, `email`, `phone`, `password`, and `repeat_password`.
Login request fields: `email` and `password`.

### 4. Fabric API

| Method | Endpoint | Auth | Purpose |
|---|---|---|---|
| `GET` | `/api/fabrics/list/` | Session-authenticated user | Return all fabrics available in the system |
| `POST` | `/api/fabrics/add/` | Session-authenticated user | Validate and create a fabric |

### 5. Measurements API

| Method | Endpoint | Auth | Purpose |
|---|---|---|---|
| `GET` | `/api/measurements/types/` | Session-authenticated user | Return reusable measurement types and stable codes |
| `GET` | `/api/measurements/profiles/` | Session-authenticated user | Return only the signed-in user's profiles and measurement rows |
| `POST` | `/api/measurements/profiles/` | Session-authenticated user | Atomically create a profile and its measurement rows |

Profile creation uses type codes, not database IDs:

```json
{
  "name": "Everyday Measurements",
  "gender": "female",
  "unit": "cm",
  "measurements": [
    {"measurement_type": "height", "value": "165", "unit": "cm"},
    {"measurement_type": "bust", "value": "94", "unit": "cm"},
    {"measurement_type": "dress_length", "value": "140", "unit": "cm"}
  ]
}
```

The API creates the profile for the authenticated user and stores each entry as an individual `Measurement` row. Duplicate type codes in one profile are rejected. The Measurements dashboard obtains the type catalog and current user's profile list through these endpoints.

## How the fabric API is used

The signed-in dashboard flow is:

1. Core submits the login form to the user API.
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

## Expected response behavior

- `200 OK` when the user is authenticated and fabric records are found.
- Empty array `[]` when the user is authenticated but no fabrics exist yet.
- An authentication failure when the session is not valid.

## Important guidance for developers

- Do not treat unimplemented routes as if they exist in production code.
- Keep this guide updated whenever new endpoints are added or old ones change.
- When a feature is intentionally web-only, it should be clearly labelled as such.
- Use session authentication for browser-driven app flows and reserve JWT-based APIs for true API clients when needed later.
