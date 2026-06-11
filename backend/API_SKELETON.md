# PowerTrace API

## Authentication

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`

All project and generation routes require a bearer token. Users can access
only their own projects, generation metadata, and generated files.

## Project And Generation Routes

- `GET /api/v1/projects`
- `POST /api/v1/projects`
- `GET /api/v1/projects/{project_id}`
- `POST /api/v1/projects/{project_id}/generations`
- `GET /api/v1/projects/{project_id}/generations/{generation_id}`
- `GET /api/v1/projects/{project_id}/generations/{generation_id}/download`

Generation is synchronous in the current API. The POST creates a `pending`
record, executes the generator, and finishes as `generated` or `failed`.

## Generation Payload

```json
{
  "width": 8.0,
  "length": 12.0,
  "seed": 42,
  "rooms": [],
  "output_format": "dxf"
}
```

`seed` may be omitted. The effective random seed is returned and persisted.
`rooms` must remain empty until room and TUE overrides are implemented.

## Successful Response

```json
{
  "project_id": "project-uuid",
  "generation_id": "generation-uuid",
  "status": "generated",
  "seed": 42,
  "message": "Floor plan generated successfully.",
  "download_url": "/api/v1/projects/project-uuid/generations/generation-uuid/download",
  "error_message": null
}
```

Known generator failures return `422` with the persisted `generation_id`.
Unexpected failures return `500` without exposing internal details.

## Next Milestone

Implement `rooms` and `specific_outlets` overrides:

1. Match request room keys to generated rooms.
2. Disable selected default TUEs.
3. Add custom dedicated loads.
4. Reflect changes in circuits, result metadata, and DXF output.
