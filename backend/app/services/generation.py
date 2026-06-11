"""Pure floor-plan and DXF generation service."""

from pathlib import Path

from app.config import settings
from app.schemas.generation import (
    GeneratedRoomResult,
    GenerationCreateRequest,
    GenerationResult,
)
from core.drawing.engine import DXFGenerator
from core.electrical.room_catalog import room_spec_to_base_room
from core.generation.generator import FloorPlanGenerator
from core.generation.openings_placer import OpeningsPlacer
from core.generation.room_roles import resolve_room_presentation


class FloorPlanGenerationError(ValueError):
    """Expected failure when no valid procedural layout can be produced."""


def generate_project_artifact(
    request: GenerationCreateRequest,
    generation_id: str,
) -> GenerationResult:
    """Generate one DXF artifact without depending on HTTP or persistence."""
    if request.seed is None:
        raise ValueError("A normalized request with an effective seed is required.")

    dxf_filename = f"generation_{generation_id}.dxf"
    output_path = (Path(settings.output_dir) / dxf_filename).resolve()

    try:
        try:
            plan, graph, program = FloorPlanGenerator(
                master_seed=request.seed,
                width=request.width,
                length=request.length,
            ).generate(max_attempts=settings.max_generation_attempts)
        except ValueError as exc:
            raise FloorPlanGenerationError(str(exc)) from exc
        openings_by_room = OpeningsPlacer.generate_openings(plan, graph, program)
        generator = DXFGenerator()
        rooms: list[GeneratedRoomResult] = []

        for room_spec in plan.rooms:
            presentation = resolve_room_presentation(
                room_spec.room_type, program.category
            )
            room = room_spec_to_base_room(
                room_spec, display_name=presentation.display_name
            )
            room.apply_nbr5410_rules()

            room_openings = openings_by_room.get(room_spec.room_type, [])
            generator.draw_room_structure(room, openings=room_openings)
            generator.draw_lighting(room)
            generator.draw_appliances(room, openings=room_openings)

            rooms.append(
                GeneratedRoomResult(
                    room_type=room_spec.room_type,
                    room_role=presentation.room_role,
                    name=room.name,
                    x=room_spec.x,
                    y=room_spec.y,
                    width=room_spec.width,
                    length=room_spec.length,
                    area=round(room_spec.area, 2),
                    total_wattage=room.get_total_wattage(),
                    exterior_walls=sorted(room_spec.exterior_walls),
                )
            )

        generator.save(dxf_filename)
        return GenerationResult(
            seed=plan.seed,
            category=program.category,
            total_width=plan.total_width,
            total_length=plan.total_length,
            total_area=round(plan.total_area, 2),
            rooms=rooms,
            dxf_filename=dxf_filename,
        )
    except Exception:
        output_path.unlink(missing_ok=True)
        raise
