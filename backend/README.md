# PowerTrace Backend

PowerTrace is a FastAPI service for persistent residential floor-plan
generation and electrical DXF output.

## Setup

1. Copy `.env.example` to `.env` and replace all placeholder secrets.
2. Install the package with `python -m pip install -e .`.
3. Apply migrations with `python -m alembic upgrade head`.
4. Start the API with `uvicorn app.main:app --reload`.

Application startup also applies pending Alembic migrations.

## Authentication

The API uses persistent user accounts and short-lived HS256 bearer tokens.
Passwords are hashed with Argon2.

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`

Project and generation routes require:

```text
Authorization: Bearer <access_token>
```

## Swagger Generation Flow

Open `http://127.0.0.1:8000/docs`, authenticate, and execute:

1. `POST /api/v1/projects` to create a project.
2. `POST /api/v1/projects/{project_id}/generations`:

```json
{
  "width": 8.0,
  "length": 12.0,
  "seed": 42,
  "rooms": [],
  "output_format": "dxf"
}
```

3. Use the returned `generation_id` with
   `GET /api/v1/projects/{project_id}/generations/{generation_id}`.
4. Execute the returned `download_url` to download the DXF.

When `seed` is omitted, the API generates and persists a reproducible 32-bit
seed. Room and specific-outlet overrides are reserved for the next release;
`rooms` must currently be empty.

Generation states:

- `pending`: the record exists and generation has not completed.
- `generated`: the DXF and result metadata are available.
- `failed`: generation ended with an error and no download is available.

The former `POST /api/v1/floor-plan/generate` route was removed in API
version `0.3.0`.

## Bootstrap And Migration

Set `BOOTSTRAP_USER_EMAIL`, `BOOTSTRAP_USER_NAME`, and
`BOOTSTRAP_USER_PASSWORD` before migrating a database with legacy projects.
The first migration transfers those projects to the bootstrap account.

## Tests

```powershell
$env:TMP='C:\tmp'
$env:TEMP='C:\tmp'
python -m pytest
```
