# PowerTrace

PowerTrace is a Python/FastAPI service for procedural residential floor-plan generation and electrical design support. It combines:

- API endpoints and schemas in `app/`
- Procedural layout generation in `core/generation/`
- Electrical room, circuit, appliance, and Brazilian standards logic in `core/electrical/`
- DXF-oriented drawing helpers in `core/drawing/`
- Domain transfer models in `models/`
- Compatibility or earlier service implementations in `services/`
- Unit and stress tests in `tests/`

## Runtime Flow

1. `app/main.py` creates the FastAPI application and includes the floor-plan router.
2. `app/api/v1/routes/floor_plan.py` receives generation requests.
3. `core/generation/generator.py` orchestrates program selection, topology-aware layout, validation, and retries.
4. `core/generation/openings_placer.py` places doors/windows after a valid layout exists.
5. `core/electrical/` applies electrical room and standards rules.
6. `core/drawing/` renders room structure, lighting, appliances, and saves DXF output.

## Tech Lead Notes

- Treat `core/` as the main domain layer unless the team intentionally re-adopts `services/`.
- Keep standard-related calculations covered by tests before changing NBR 5410 or NBR 8995 behavior.
- Do not commit generated DXF output, caches, virtual environments, or local secret values.
- The current documentation redacts `.env` values by design.
