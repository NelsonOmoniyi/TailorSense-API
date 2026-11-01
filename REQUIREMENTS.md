# TailorSense Requirements and Structure

This document records the recommendations feature requirements and the repository structure inspected for its implementation. `requirements.txt` remains the Python dependency manifest; application behavior and product requirements belong here.

## Project purpose

TailorSense is a Django and Django REST Framework application serving server-rendered web pages and authenticated API clients. The recommendations feature returns transparent, deterministic style suggestions based on an authenticated user's saved measurement profile, a fabric from the shared catalogue, and an active garment category.

## Current repository structure

```text
config/                 Django settings and root URL configuration
apps/core/              Authenticated browser pages, templates' data adapter, and form handlers
apps/users/             Accounts, session identity checks, and user API
apps/measurements/      User-owned profiles, measurement types, and measurement values
apps/fabrics/           Shared fabric catalogue and fabric API
apps/styles/            Garment categories, styles, occasions, images, suitability links,
                        and style measurement requirements
apps/recommendations/   Recommendation request API, service coordination, and ranking engine
templates/              Server-rendered page templates, including recommendations/dashboard.html
static/                 Shared page styling and assets
API User Guide/API.md   API and browser workflow documentation
requirements.txt        Python package dependencies
```

The browser-facing pages are routed through `apps.core`; versioned catalogue and recommendation APIs are exposed under `/api/v1/`. The recommendation dashboard obtains its selectable profiles, fabrics, and active garment categories through the existing APIs and submits its request to the Recommendations API.

## Repository audit

### Existing data and relationships

- `MeasurementProfile` belongs to one user and stores a free-form gender/sizing category and display unit.
- `Measurement` associates a profile with one reusable `MeasurementType`; values use `cm` or `in`.
- `Style` belongs to a `Garment`, may have `Occasion` associations, and stores its own free-form gender, fit type, description, and active flag.
- `StyleFabric` links a style to the shared `Fabric` catalogue and records suitability, notes, and active status.
- `StyleMeasurementRequirement` links a style to existing measurement types and records whether each item is required, optional, conditional, used for recommendation completeness, pattern drafting, or both, and any measurement instructions.
- `Style.measurement_specification_status` distinguishes `not_configured`, `draft`, `reviewed`, and `validated` checklists. Review/validation provenance is stored on the style; the normal style API exposes it read-only.
- `StyleImage` stores ordered style images and the primary-image flag.
- No recommendation history or feedback model was present; none is added.

### Data and contract findings

- The current `Fabric` model includes `fabric_name`, `fiber_category`, `weight`, `stretch`, `drape`, `breathability`, `opacity`, and an optional image. It has neither a user owner nor an available-quantity field.
- Style/fabric suitability choices are `excellent`, `good`, `acceptable`, and `unsuitable`. Only active links with the first three values can support a recommendation.
- Garment categories and occasions are existing records, not new recommendation taxonomies. Category input is an active `Garment.slug`; occasion input is matched case-insensitively to an existing `Occasion.name`.
- The existing style records do not define an allowed fit-preference contract. `preferences` and arbitrary extra request fields are therefore rejected rather than silently ignored.
- The database snapshot inspected read-only contained 127 fabrics, 16 garment records, 188 styles, 552 style/fabric links, 360 images, and 29 style measurement requirements. It recorded migrations only through `fabrics.0007_fabric_image` and `styles.0003_alter_style_slug_style_unique_style_slug`, while the repository contains later fabric and style catalogue seed migrations. The catalogue rows exist in that snapshot despite the seed migrations not being recorded as applied. The schema fields inspected matched the current models; this migration-history discrepancy means the snapshot is not treated as authoritative or used as a writable test database.
- The active category records in the snapshot include `kaftan`, `trousers`, `shirts`, `agbada`, `gowns`, `skirts`, and `blouses`. This differs from the intended singular `Blouse` label. The endpoint preserves the existing record and accepts its actual slug rather than performing a broad data migration. Older seed categories remain inactive.
- The catalogue audit found 160 active styles across active garments; before the Agbada pilot migration, only 2 of those styles had any style-specific measurement requirements, and active Agbada's 12 styles had none. Existing requirements are therefore not evidence of comprehensive or approved checklists.
- The user-supplied Agbada checklist is now seeded as draft requirements on each of the 12 active Agbada styles. It includes Agbada length/span, neck, Buba length/sleeve, chest, Sokoto length/waist, conditional thigh circumference for Sokoto Kembe, optional Fila circumference, and separate conditional embroidery width/depth fields. User-provided method text and source labels are stored per requirement. These specifications remain draft, do not gate or score recommendations, and need a named reviewer/date before approval; conditional applicability is not automatically inferred.
- The shared fabric records do not establish personal ownership or quantity. There are no inventory or consumption-estimate models; style/fabric compatibility is not a claim that the user owns enough fabric.

## Product and implementation requirements

1. Reuse the current Django app layout, models, migration history, authentication rules, API conventions, and image storage. Do not add duplicate profile, measurement, fabric, style, occasion, image, or recommendation-history models.
2. Provide `POST /api/v1/recommendations/` for web and mobile clients. Require the existing authenticated project session or verified JWT permission.
3. Accept `measurement_profile_id`, `fabric_id`, an active garment `category` slug, optional recorded `occasion`, and optional `limit` (default 10, range 1–20). Do not accept unsupported preferences.
4. Scope profile lookup to the authenticated user. Invalid, missing, or foreign profile IDs must not expose another user's profile or measurements.
5. Consider only active styles in the requested active category with an active explicit style/fabric link. Exclude `unsuitable` links and styles with no recorded relationship; do not infer suitability from generic fabric properties.
6. Exclude a candidate when both profile and style sizing-category values are recorded and conflict. If either value is absent, do not claim the compatibility was verified; include that limitation in the explanation.
7. Treat measurement completeness as unknown for `not_configured` and `draft` specifications. Only reviewed/validated recommendation-purpose requirements may exclude styles for missing required measurements or affect the completeness score. Return missing type codes/names and excluded style identity; preserve optional measurements as eligible checklist gaps.
8. Use only a deterministic, independently testable, rule-based score. Never infer exact fit, classify body shape, or make subjective appearance judgments.
9. Score fabric suitability using recorded values (excellent 100, good 80, acceptable 60). Score measurement completeness only from reviewed/validated recommendation-purpose requirements. When an occasion is requested, score recorded occasion association as 100 or no association as 0. Normalize over only the available criteria; unavailable or unreviewed criteria do not receive invented points.
10. Use provisional weights of 40 for fabric suitability, 30 for measurement completeness, and 20 for an explicitly requested occasion. The unsupported 10-point preference criterion is omitted, and the score is normalized over evaluated criteria. Round to one decimal place and rank by descending score, then style name and ID for deterministic ties.
11. Return one entry per style, its description, score, evidence-based reasons, optional missing measurements, and available ordered images (primary first). Return an empty result list when no candidates are eligible.
12. Keep business logic in the recommendation engine and service, not in the API view. Use related-object loading to avoid per-result database queries.
13. Make the existing recommendations browser page usable with the same API and data, while keeping API validation and ranking authoritative.
14. Add automated tests for authentication, profile ownership, request validation, eligibility, ranking, occasion behavior, missing measurements, images, empty results, and browser submission.
15. Do not introduce ML packages, external AI services, infrastructure, destructive database commands, or fabricated quantity/fit data. Schema changes must be additive, migration-backed, and preserve existing catalogue rows.
16. Keep the API guide aligned with actual behavior, including the distinction between unreviewed and approved specifications and the limits of checklist completeness.

## Recommendation behavior

- Eligibility is evaluated before scoring. A high score cannot override an inactive style/link, unsuitable or missing fabric link, contradictory recorded sizing categories, or a missing required measurement in an approved checklist.
- No database compatibility record means no confirmed match; fabric attributes are not used as an undocumented fallback.
- Only `reviewed` and `validated` style specifications can establish recommendation completeness; absent and `draft` specifications are unknown, not complete. Existing requirement rows are migrated to `draft`.
- Only `recommendation` and `both` purpose requirements can gate or score. Drafting-only requirements are ignored for recommendation completeness. Free-text conditions remain unresolved and are shown for manual decision; they are not automatically evaluated.
- Required measurements are checked by measurement-type identity. The engine does not compare numeric values to a pattern or claim a guaranteed fit. A `complete` checklist means the recorded applicable checklist entries exist, not that a garment fits.
- A selected occasion influences ranking, but does not make an otherwise eligible style ineligible.
- The result score is normalized over evaluated criteria. Measurement requirements are omitted from scoring when a style has none; occasion is omitted when the request does not select one.
- History, user preferences, fabric ownership, fabric quantity, and garment-consumption estimates are deferred.

## Acceptance checklist

- [x] Reuse the existing profile, fabric, style, suitability, occasion, requirement, and image models.
- [x] Register a Recommendations API at the versioned route and require authentication.
- [x] Enforce profile ownership without exposing another user's data.
- [x] Filter by active style/category and explicit active fabric suitability.
- [x] Report missing required measurements and score optional completeness transparently.
- [x] Surface specification review state, exclude only against reviewed/validated requirements, and show conditional requirements without automatic interpretation.
- [x] Return explicit fabric suitability and stored compatibility notes.
- [x] Rank deterministically with normalized scores and explanations.
- [x] Return image data without duplicating styles.
- [x] Expose empty results and validation failures explicitly.
- [x] Provide a web form that submits to the same API.
- [x] Document data limitations and the actual API contract.
- [x] Add isolated automated coverage; do not write to the local catalogue snapshot.

## Manual verification

1. Start the Django development server with the project's configured virtual environment.
2. Sign in, create a measurement profile, and open `/recommendations/`.
3. Select a profile, fabric, and active garment category, then request recommendations.
4. Confirm the results show recorded fabric suitability, measurement checklist status (including unknown/draft), missing measurement information, and available style images.
5. For API verification, send an authenticated JSON `POST` to `/api/v1/recommendations/` using the request shape documented in `API User Guide/API.md`.
