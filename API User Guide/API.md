# TailorSense API User Guide

**Base URL:** `http://127.0.0.1:8000`

The API uses one JWT authentication flow for web and mobile clients. Registration
and login are public. Protected endpoints use an access token in the
`Authorization` header. No API key or Django session cookie is required by the
API.

## Setup

```powershell
python manage.py migrate
python manage.py runserver
```

Always include the trailing slash in API URLs.

## Endpoints

| Method | Endpoint | Authentication | Purpose |
|---|---|---|---|
| `POST` | `/api/users/register/` | None | Create an account |
| `POST` | `/api/users/login/` | None | Issue access and refresh JWTs |
| `POST` | `/api/users/refresh/` | None | Issue a new access JWT |
| `GET` | `/api/users/profile/?email=...` | Bearer access JWT | Get the authenticated user |
| `POST` | `/api/users/logout/` | Bearer access JWT | Revoke the refresh JWT |

## 1. Register

```http
POST /api/users/register/
Content-Type: application/json
```

```json
{
  "full_name": "Alex Taylor",
  "email": "alex@example.com",
  "phone": "+1 555 123 4567",
  "password": "StrongPassword123!",
  "password_confirmation": "StrongPassword123!"
}
```

Registration does not require an access token, API key, or session cookie.

Successful response: `201 Created`

```json
{
  "id": 1,
  "email": "alex@example.com",
  "first_name": "Alex Taylor",
  "phone": "+1 555 123 4567"
}
```

## 2. Login

```http
POST /api/users/login/
Content-Type: application/json
```

```json
{
  "email": "alex@example.com",
  "password": "StrongPassword123!"
}
```

Login is public. The password is used only for this request and is never sent
with later API calls.

Successful response: `200 OK`

```json
{
  "user": {
    "id": 1,
    "email": "alex@example.com",
    "first_name": "Alex Taylor",
    "phone": "+1 555 123 4567"
  },
  "access": "<access-token>",
  "refresh": "<refresh-token>"
}
```

Store both tokens securely. Send the access token with protected requests:

```http
Authorization: Bearer <access-token>
```

The access token lasts 15 minutes. The refresh token lasts 7 days.

## 3. Refresh

```http
POST /api/users/refresh/
Content-Type: application/json
```

```json
{
  "refresh": "<refresh-token>"
}
```

Successful response:

```json
{
  "access": "<new-access-token>",
  "refresh": "<new-refresh-token>"
}
```

Replace the stored tokens when refresh-token rotation returns new values.

## 4. Profile

The email is supplied as a consistency check. The JWT remains the actual
authentication credential and identifies the user.

```http
GET /api/users/profile/?email=alex@example.com
Authorization: Bearer <access-token>
```

Successful response: `200 OK`

```json
{
  "id": 1,
  "email": "alex@example.com",
  "first_name": "Alex Taylor",
  "phone": "+1 555 123 4567"
}
```

The endpoint returns `403 Forbidden` if the query email does not match the
user identified by the access token.

## 5. Logout

Logout requires the access token and the refresh token. The access token
authenticates the request; the refresh token is revoked so it cannot be used
to create another access token.

```http
POST /api/users/logout/
Authorization: Bearer <access-token>
Content-Type: application/json
```

```json
{
  "email": "alex@example.com",
  "refresh": "<refresh-token>"
}
```

Successful response: `204 No Content`.

The API verifies that the email and refresh token belong to the user identified
by the access token. The client should also remove its locally stored tokens.

## Security Rules

- Registration and login do not require authentication.
- Never send a password after login.
- Never put JWTs in URLs, logs, or source control.
- Store tokens in secure browser or mobile storage.
- Use HTTPS outside local development.
- A JWT is the API credential; there is no separate API-key mechanism.
