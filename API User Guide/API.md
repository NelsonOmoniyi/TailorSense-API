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

Profile creation uses type codes, not database IDs. Every measurement is a
linear dimension measured with a tape measure, so the only supported units are
`cm` and `in`; the catalog contains no mass or weight types:

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

> **Note on units:** Tailoring measurements are all linear, so `cm` and `in` are the only accepted units. Body weight was removed deliberately — a tape measure cannot capture mass and no pattern draft uses it.

### 6. Recommendations API

| Method | Endpoint | Auth | Purpose |
|---|---|---|---|
| `POST` | `/api/v1/recommendations/` | Valid project session or JWT | Rank active styles for a profile, fabric, and garment category |

The measurement profile must belong to the authenticated user. The selected fabric is an existing record in the shared catalogue. `category` is the slug of an active garment returned by `/api/v1/garments/`. An optional `occasion` must match an existing occasion name (case-insensitive). `limit` is optional, defaults to 10, and must be between 1 and 20. Unsupported keys, including `preferences`, are rejected.

```http
POST /api/v1/recommendations/
Content-Type: application/json
Cookie: sessionid=your-session-cookie
```

```json
{
  "measurement_profile_id": 12,
  "fabric_id": 7,
  "category": "gowns",
  "occasion": "casual",
  "limit": 10
}
```

Illustrative successful response (IDs, score, descriptions, and image URLs depend on actual records):

```json
{
  "category": "gowns",
  "results": [
    {
      "style_id": 24,
      "name": "Flare Gown",
      "description": "A style description from the catalogue.",
      "score": 91.1,
      "reasons": [
        "The recorded fabric suitability for this style is good.",
        "All reviewed recommendation measurements are available.",
        "The profile and style have matching recorded sizing categories.",
        "This style is associated with the selected Casual occasion."
      ],
      "fabric_compatibility": {
        "suitability": "good",
        "notes": "Suitable for a lightweight finish."
      },
      "measurement_check": {
        "status": "complete",
        "specification_status": "reviewed",
        "required_count": 2,
        "required_available_count": 2,
        "optional_count": 0,
        "optional_available_count": 0,
        "missing_measurements": [],
        "conditional_requirements": []
      },
      "missing_measurements": [],
      "images": [
        {
          "id": 31,
          "image": "http://127.0.0.1:8000/media/styles/flare-gown.jpg",
          "view_type": "front",
          "alt_text": "Front view of the gown",
          "is_primary": true,
          "display_order": 0,
          "created_at": "2026-09-18T12:00:00Z"
        }
      ]
    }
  ],
  "missing_measurements": [],
  "excluded_for_measurements": [],
  "count": 1
}
```

#### Eligibility and ranking

- Only active styles in the selected active garment category with an active style/fabric relationship are considered.
- `unsuitable` and inactive relationships are excluded. A missing relationship is not treated as compatibility.
- If both the profile and style have a sizing-category value and those values differ, the style is excluded. If either is blank, the style may be listed, but its reason explicitly states that sizing-category compatibility could not be verified.
- Measurement specification states are `not_configured`, `draft`, `reviewed`, and `validated`. Only reviewed or validated specifications can gate eligibility or contribute to measurement-completeness scoring. Styles without an approved specification remain possible candidates, but their measurement readiness is explicitly unknown and does not receive a completeness score.
- A style is excluded for missing required measurements only when those requirements belong to a reviewed/validated specification and are for recommendation completeness (`recommendation` or `both`). The response-level `missing_measurements` lists distinct missing required codes/names across excluded matching styles; `excluded_for_measurements` identifies each excluded style, its `incomplete` check status, and its reviewed specification state. Missing optional recommendation measurements are retained in results and reduce completeness.
- Requirements marked `drafting` do not affect recommendations. Conditional requirements are returned with their condition and are marked unresolved; the API does not interpret free text or decide whether the condition applies.
- Result `measurement_check.status` may be `not_configured`, `draft`, `complete`, `optional_missing`, `conditional_unresolved`, or `no_recommendation_requirements`. Excluded styles have `measurement_check.status` set to `incomplete`. The result includes required/optional checklist counts, available counts, missing measurements, and conditional requirements. A `complete` checklist means only that the reviewed recommendation checklist's applicable measurements are recorded; it is not a fit assessment.
- The Agbada pilot checklist is recorded as `reviewed` on the 12 active Agbada styles, with the supplied reviewer and review date. The reviewer confirmed the Sokoto Kembe and custom-embroidery conditions apply to every active Agbada style, so those requirements participate in completeness checks; the original conditions and confirmation remain in their notes. The optional Fila measurement remains optional. This checklist has not been validated in practice.
- Fabric scores are `excellent` 100, `good` 80, and `acceptable` 60. Each result includes `fabric_compatibility.suitability` and the stored link notes. Measurement completeness is calculated only from reviewed/validated recommendation requirements. A requested occasion contributes 100 when associated and 0 otherwise.
- The provisional weights are fabric 40, measurements 30, and occasion 20. Unavailable criteria are omitted and the remaining weights are normalized. The score is rounded to one decimal place; ties are broken by style name and ID.
- Results include the existing ordered StyleImage records, with primary images first. A style appears only once.

Validation errors return `400`; this includes unknown profile/fabric/category/occasion values, a profile not owned by the caller, unsupported preferences, and limits outside 1–20. Authentication failures return the project's DRF permission response (`401` or `403`, depending on the authentication class). A valid request with no eligible styles returns `200` with `results: []` and `count: 0`.

The recommendations dashboard at `/recommendations/` uses the same API. Scores describe recorded catalogue compatibility and checklist completeness, not a guaranteed fit, validated pattern draft, or body-shape assessment. Fabric records have no owner or quantity, and styles have no material-consumption estimates; the API does not claim the user owns enough fabric to make a style. Recommendation history and unsupported user preferences are not implemented.

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
    "weight": "220 gsm",
    "stretch": "none",
    "drape": "soft",
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
