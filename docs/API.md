# TailorSense API

**Status:** Current development reference  
**Base URL:** `http://127.0.0.1:8000`  
**Format:** JSON  
**Last reviewed:** 2026-09-09

## Introduction

TailorSense is a measurement-based style application. Users will enter their measurements and receive suggested styles and designs.

This document is designed to let a developer immediately test the API with **Postman**, connect it to a **web application**, or connect it to a **mobile application**.

## Quick Start: Copy These Requests

This section is the fastest way to use the API. Start the server, then follow
the instructions for the client you are using. The URLs, headers, bodies,
successful responses, and common errors are provided below without requiring
additional project knowledge.

```powershell
python manage.py runserver
python manage.py migrate
```

Use this base URL for local testing:

```text
http://127.0.0.1:8000
```

### A. Registration: `POST /api/users/register/`

#### Postman: exact setup

| Postman area | Value |
|---|---|
| Method | `POST` |
| URL | `http://127.0.0.1:8000/api/users/register/` |
| Authorization | `No Auth` |
| Params | Leave empty |
| Header | `Content-Type: application/json` |
| Body | **raw** -> **JSON**, then paste the JSON below |

```json
{
  "full_name": "Alex Taylor",
  "email": "alex@example.com",
  "phone": "+1 555 123 4567",
  "password": "StrongPassword123!",
  "password_confirmation": "StrongPassword123!"
}
```

Click **Send**. Expected success:

```text
201 Created
```

```json
{
  "id": 1,
  "email": "alex@example.com",
  "first_name": "Alex Taylor",
  "phone": "+1 555 123 4567"
}
```

Example error when the email is already registered:

```text
400 Bad Request
```

```json
{
  "email": [
    "An account with this email already exists."
  ]
}
```

#### Web application: exact JavaScript

```javascript
const response = await fetch('/api/users/register/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    full_name: 'Alex Taylor',
    email: 'alex@example.com',
    phone: '+1 555 123 4567',
    password: 'StrongPassword123!',
    password_confirmation: 'StrongPassword123!'
  })
});

const data = await response.json();

if (!response.ok) {
  console.error(data); // Validation error details
} else {
  console.log(data); // Created user
}
```

No authorization, session cookie, API key, or JWT is required to register.

#### Mobile application: exact request shape

```javascript
const response = await fetch('https://api.example.com/api/users/register/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    full_name: 'Alex Taylor',
    email: 'alex@example.com',
    phone: '+1 555 123 4567',
    password: 'StrongPassword123!',
    password_confirmation: 'StrongPassword123!'
  })
});

const data = await response.json();
```

The mobile app receives the same success and error responses shown above.

### B. Web Login: `POST /api/users/login/`

Use this endpoint for the current web application. It creates a Django
`sessionid` cookie.

#### Postman: exact setup

| Postman area | Value |
|---|---|
| Method | `POST` |
| URL | `http://127.0.0.1:8000/api/users/login/` |
| Authorization | `No Auth` |
| Params | Leave empty |
| Header | `Content-Type: application/json` |
| Body | **raw** -> **JSON**, then paste the JSON below |

```json
{
  "email": "alex@example.com",
  "password": "StrongPassword123!"
}
```

Click **Send**. Expected success:

```text
200 OK
```

```json
{
  "id": 1,
  "email": "alex@example.com",
  "first_name": "Alex Taylor",
  "phone": "+1 555 123 4567"
}
```

Postman should save a `sessionid` cookie. If the credentials are wrong:

```text
400 Bad Request
```

```json
{
  "detail": "Invalid email or password."
}
```

#### Web application: exact JavaScript

```javascript
const response = await fetch('/api/users/login/', {
  method: 'POST',
  credentials: 'include',
  headers: {
    'Content-Type': 'application/json',
    'X-CSRFToken': csrfToken
  },
  body: JSON.stringify({
    email: 'alex@example.com',
    password: 'StrongPassword123!'
  })
});

const data = await response.json();

if (!response.ok) {
  console.error(data); // Login error
} else {
  console.log(data); // Logged-in user
}
```

`credentials: 'include'` allows the browser to save and send the `sessionid`
cookie. `csrfToken` must be the CSRF token supplied by Django.

#### Mobile application

Do not use this session endpoint for the mobile app. Use the JWT endpoint below.

### C. Mobile Login: `POST /api/token/`

Use this endpoint for the mobile application. It returns JWT access and refresh
tokens instead of a browser session.

#### Postman: exact setup

| Postman area | Value |
|---|---|
| Method | `POST` |
| URL | `http://127.0.0.1:8000/api/token/` |
| Authorization | `No Auth` |
| Params | Leave empty |
| Header | `Content-Type: application/json` |
| Body | **raw** -> **JSON**, then paste the JSON below |

```json
{
  "username": "alex@example.com",
  "password": "StrongPassword123!"
}
```

Expected success:

```text
200 OK
```

```json
{
  "access": "<access-token>",
  "refresh": "<refresh-token>"
}
```

Invalid credentials return `401 Unauthorized`.

#### Web application

The web application should normally use `/api/users/login/` and a session. If
the web client uses JWT instead, it must store tokens securely and send the
access token as a Bearer token. Do not put tokens in URLs.

#### Mobile application: exact JavaScript request shape

```javascript
const tokenResponse = await fetch('https://api.example.com/api/token/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    username: 'alex@example.com',
    password: 'StrongPassword123!'
  })
});

const tokens = await tokenResponse.json();

if (!tokenResponse.ok) {
  console.error(tokens); // Login error
} else {
  // Store these in iOS Keychain, Android Keystore, or equivalent secure storage.
  const accessToken = tokens.access;
  const refreshToken = tokens.refresh;
}
```

The field is named `username` because Simple JWT uses that field by default.
In TailorSense, the username value is the user's email address.

### D. Get Current User: `GET /api/users/me/`

This endpoint is protected. It requires either a valid web session or a valid
JWT access token.

#### Postman using JWT: exact setup

| Postman area | Value |
|---|---|
| Method | `GET` |
| URL | `http://127.0.0.1:8000/api/users/me/` |
| Params | Leave empty |
| Body | Leave empty |
| Authorization | **Bearer Token**, paste the `access` token from `/api/token/` |

Postman will send:

```http
Authorization: Bearer <access-token>
```

Expected success:

```text
200 OK
```

```json
{
  "id": 1,
  "email": "alex@example.com",
  "first_name": "Alex Taylor",
  "phone": "+1 555 123 4567"
}
```

Without a session or token:

```text
401 Unauthorized
```

```json
{
  "detail": "Authentication credentials were not provided."
}
```

#### Web application: exact JavaScript

```javascript
const response = await fetch('/api/users/me/', {
  method: 'GET',
  credentials: 'include'
});

const user = await response.json();

if (!response.ok) {
  console.error(user); // Authentication error
} else {
  console.log(user); // Current signed-in user
}
```

The browser uses the `sessionid` cookie created by `/api/users/login/`.

#### Mobile application: exact JavaScript

```javascript
const response = await fetch('https://api.example.com/api/users/me/', {
  method: 'GET',
  headers: {
    'Authorization': `Bearer ${accessToken}`
  }
});

const user = await response.json();
```

The mobile app must use the access token, not the refresh token, for this request.

### D1. Refresh A Mobile Token: `POST /api/token/refresh/`

When the mobile access token expires, call:

| Postman area | Value |
|---|---|
| Method | `POST` |
| URL | `http://127.0.0.1:8000/api/token/refresh/` |
| Authorization | `No Auth` |
| Params | Leave empty |
| Header | `Content-Type: application/json` |
| Body | **raw** -> **JSON** |

```json
{
  "refresh": "<refresh-token>"
}
```

Success response:

```text
200 OK
```

```json
{
  "access": "<new-access-token>"
}
```

An invalid or expired refresh token returns `401 Unauthorized`. Replace the old
access token with the new one before calling `/api/users/me/` again.

## Start The API

From the project folder:

```powershell
Copy-Item .env.example .env
python manage.py migrate
python manage.py runserver
```

The server is then available at:

```text
http://127.0.0.1:8000
```

For a deployed server, replace the base URL with the deployment's HTTPS URL.

## Endpoint List

| Method | Endpoint | Authentication | Main use |
|---|---|---|---|
| `POST` | `/api/users/register/` | None | Create an account |
| `POST` | `/api/users/login/` | None | Web login and session creation |
| `POST` | `/api/token/` | None | Mobile login and JWT creation |
| `POST` | `/api/token/refresh/` | None | Get a new mobile access token |
| `GET` | `/api/users/me/` | Session or JWT | Get the signed-in user |
| `POST` | `/api/users/logout/` | Session or JWT | End a web session |

Always include the trailing `/` in the endpoint URL.

## Authentication And Security

There are two supported authentication methods:

- **Web application:** Django session cookie, normally `sessionid`.
- **Mobile application:** JWT access token sent as `Authorization: Bearer <token>`.

Registration, web login, and token login do not require previous authentication. `/me/` and `/logout/` require a valid session or access token.

### Web security

- Use `credentials: 'include'` in browser JavaScript so the session cookie is sent.
- Browser-changing requests must include Django's CSRF token in `X-CSRFToken`.
- Use HTTPS outside local development.

### Mobile security

- Send the access token with every protected request.
- Store access and refresh tokens in secure storage such as iOS Keychain or Android Keystore.
- Never put tokens in logs, source control, or plain-text shared preferences.
- Do not send a password with every request; send it only to registration or login.
- Access tokens last 15 minutes. Refresh tokens last 7 days.
- When an access token expires, use the refresh token to obtain another access token.

### Not required

- No API key is required by the current API.
- No JWT is required for the web session flow.
- No session cookie is required for the mobile JWT flow.

## 1. Register A User

### Request

```text
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

### Input fields

| Field | Type | Required | Rules |
|---|---|---:|---|
| `full_name` | string | Yes | Maximum 150 characters |
| `email` | string | Yes | Must be a valid, unused email address |
| `phone` | string | Yes | Maximum 20 characters |
| `password` | string | Yes | Minimum 8 characters and must pass password validation |
| `password_confirmation` | string | Yes | Must match `password` |

### Success response

**Status:** `201 Created`

```json
{
  "id": 1,
  "email": "alex@example.com",
  "first_name": "Alex Taylor",
  "phone": "+1 555 123 4567"
}
```

The password is never returned.

### Error responses

**Status:** `400 Bad Request`

```json
{
  "email": [
    "An account with this email already exists."
  ]
}
```

Other possible validation errors include invalid email, missing fields, weak password, and mismatched passwords.

### Postman

1. Create a `POST` request to `http://127.0.0.1:8000/api/users/register/`.
2. Select **Body > raw > JSON**.
3. Paste the request JSON above.
4. Select **Send**.
5. Confirm the response status is `201 Created`.

### Web application

```javascript
const response = await fetch('/api/users/register/', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    full_name: 'Alex Taylor',
    email: 'alex@example.com',
    phone: '+1 555 123 4567',
    password: 'StrongPassword123!',
    password_confirmation: 'StrongPassword123!'
  })
});

const data = await response.json();
```

### Mobile application

Use the same `POST` request and JSON body. The mobile app does not need a session or JWT to register. After registration, obtain JWTs through `/api/token/`.

## 2. Web Login And Session

Use this endpoint when testing the current browser-based web application.

### Request

```text
POST /api/users/login/
Content-Type: application/json
```

```json
{
  "email": "alex@example.com",
  "password": "StrongPassword123!"
}
```

### Success response

**Status:** `200 OK`

```json
{
  "id": 1,
  "email": "alex@example.com",
  "first_name": "Alex Taylor",
  "phone": "+1 555 123 4567"
}
```

A successful response also creates a Django `sessionid` cookie. The browser must send that cookie with protected requests.

### Error response

**Status:** `400 Bad Request`

```json
{
  "detail": "Invalid email or password."
}
```

### Postman

1. Create a `POST` request to `http://127.0.0.1:8000/api/users/login/`.
2. Select **Body > raw > JSON**.
3. Send the email and password JSON above.
4. Open Postman's **Cookies** section and confirm that a `sessionid` cookie was saved.
5. Use that same Postman session for `/api/users/me/`.

### Web application

```javascript
const response = await fetch('/api/users/login/', {
  method: 'POST',
  credentials: 'include',
  headers: {
    'Content-Type': 'application/json',
    'X-CSRFToken': csrfToken
  },
  body: JSON.stringify({
    email: 'alex@example.com',
    password: 'StrongPassword123!'
  })
});

const data = await response.json();
```

`csrfToken` must be obtained from the Django CSRF cookie or a page that provides a CSRF token. The browser stores the session cookie after successful login.

### Mobile application

Do not use this endpoint for the mobile app. Use `/api/token/` so the mobile app receives JWTs instead of depending on browser cookies.

## 3. Mobile Login: Obtain JWTs

### Request

```text
POST /api/token/
Content-Type: application/json
```

```json
{
  "username": "alex@example.com",
  "password": "StrongPassword123!"
}
```

The field is currently named `username` because this is the standard Simple JWT endpoint. TailorSense stores the user's email as the username.

### Success response

**Status:** `200 OK`

```json
{
  "access": "<access-token>",
  "refresh": "<refresh-token>"
}
```

### Error response

**Status:** `401 Unauthorized`

```json
{
  "detail": "No active account found with the given credentials"
}
```

### Postman

1. Create a `POST` request to `http://127.0.0.1:8000/api/token/`.
2. Select **Body > raw > JSON**.
3. Send the email in the `username` field.
4. Copy the returned `access` token.
5. Use it as a Bearer token for `/api/users/me/`.

### Web application

A web application may use this endpoint, but the current web flow is session-based. If using JWT in a browser, keep the token out of URLs and prefer secure, HttpOnly cookie handling implemented by the backend.

### Mobile application

```javascript
const response = await fetch('https://api.example.com/api/token/', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    username: 'alex@example.com',
    password: 'StrongPassword123!'
  })
});

const tokens = await response.json();
// Store tokens.access and tokens.refresh in secure mobile storage.
```

## 4. Refresh A Mobile Access Token

### Request

```text
POST /api/token/refresh/
Content-Type: application/json
```

```json
{
  "refresh": "<refresh-token>"
}
```

### Success response

**Status:** `200 OK`

```json
{
  "access": "<new-access-token>"
}
```

### Error response

**Status:** `401 Unauthorized`

```json
{
  "detail": "Token is invalid or expired",
  "code": "token_not_valid"
}
```

### Postman

Send the refresh token in the JSON body. Copy the new `access` value and replace the old access token in future requests.

### Web application

This endpoint is not needed when the web application uses the normal session flow.

### Mobile application

Call this endpoint when a protected request returns `401 Unauthorized` because the access token has expired. Replace the stored access token and retry the original request.

## 5. Get The Current User

### Request

```text
GET /api/users/me/
```

Use one of these authentication methods:

```http
Authorization: Bearer <access-token>
```

or a valid browser/Postman `sessionid` cookie.

### Success response

**Status:** `200 OK`

```json
{
  "id": 1,
  "email": "alex@example.com",
  "first_name": "Alex Taylor",
  "phone": "+1 555 123 4567"
}
```

### Error response

**Status:** `401 Unauthorized`

```json
{
  "detail": "Authentication credentials were not provided."
}
```

### Postman

- For mobile testing, use **Authorization > Bearer Token** and paste the access token.
- For web testing, use the saved `sessionid` cookie.
- Send the request and confirm the user JSON is returned.

### Web application

```javascript
const response = await fetch('/api/users/me/', {
  method: 'GET',
  credentials: 'include'
});

const user = await response.json();
```

### Mobile application

```javascript
const response = await fetch('https://api.example.com/api/users/me/', {
  headers: {
    Authorization: `Bearer ${accessToken}`
  }
});

const user = await response.json();
```

## 6. Logout

### Request

```text
POST /api/users/logout/
```

Send either the session cookie or a valid Bearer access token.

### Success response

**Status:** `204 No Content`

There is no response body.

### Error response

**Status:** `401 Unauthorized`

```json
{
  "detail": "Authentication credentials were not provided."
}
```

### Postman

Send the request using the saved session cookie or Bearer access token. A successful request returns `204`.

### Web application

```javascript
await fetch('/api/users/logout/', {
  method: 'POST',
  credentials: 'include',
  headers: {'X-CSRFToken': csrfToken}
});
```

### Mobile application

The current endpoint clears a Django session. A mobile app must also delete its locally stored access and refresh tokens. JWTs are not immediately revoked by this endpoint and expire according to their configured lifetime.

## Common HTTP Responses

| Status | Meaning |
|---:|---|
| `200 OK` | Request succeeded and returned data |
| `201 Created` | Account was created |
| `204 No Content` | Request succeeded without response data |
| `400 Bad Request` | Input is invalid or web credentials are incorrect |
| `401 Unauthorized` | No valid session/token was supplied, or a JWT is invalid/expired |
| `403 Forbidden` | Request failed a security or permission check, commonly CSRF |
| `404 Not Found` | URL does not exist |
| `405 Method Not Allowed` | Endpoint does not support the chosen HTTP method |

## Current Security Requirements

The following rules must be followed by any client:

1. Use HTTPS in staging and production.
2. Never commit `.env`, `DJANGO_SECRET_KEY`, passwords, sessions, or JWTs.
3. Use a unique Django secret key for every local developer and deployment environment.
4. Keep mobile tokens in secure device storage.
5. Send only the access token, not the refresh token, to normal protected endpoints.
6. Treat `401` as a signal to refresh the access token or send the user to login.
7. Protected future endpoints must verify that requested measurements and designs belong to the authenticated user.
8. Add rate limiting to login and registration before production.

## Implementation Reference

The endpoint definitions are maintained in:

- `config/urls.py` — token and root API routes.
- `apps/users/urls.py` — user API routes.
- `apps/users/views.py` — user API behavior.
- `apps/users/serializers.py` — input and output fields.
- `apps/users/services.py` — account creation and authentication operations.
- `config/settings.py` — session authentication, JWT authentication, and token lifetimes.

Update this document whenever an endpoint, request field, response, error, authentication rule, or security requirement changes.
