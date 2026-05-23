"""Rotas da API v1 — Floor Plan."""

import os
from fastapi import APIRouter, HTTPException

from app.schemas.floor_plan import GenerateRequest, FloorPlanResponse, RoomResponse
from app.config import settings
from core.generation.generator import FloorPlanGenerator
from core.generation.openings_placer import OpeningsPlacer
from core.drawing.engine import DXFGenerator
from core.electrical.room_catalog import room_spec_to_base_room

router = APIRouter(prefix="/floor-plan", tags=["floor-plan"])


@router.post("/generate", response_model=FloorPlanResponse)
def generate_floor_plan(request: GenerateRequest) -> FloorPlanResponse:
    """Gera uma planta baixa elétrica completa.

    Executa o pipeline completo:
      1. Program (seleção de cômodos + topologia)
      2. Layout (BSP guiado)
      3. Openings (portas e janelas)
      4. DXF (desenho e exportação)
    """
    try:
        plan, graph, program = FloorPlanGenerator(
            master_seed=request.seed,
            width=request.width,
            length=request.length,
        ).generate(max_attempts=settings.max_generation_attempts)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    openings_dict = OpeningsPlacer.generate_openings(plan, graph)

    generator = DXFGenerator()
    rooms_response = []

    for room_spec in plan.rooms:
        room_obj = room_spec_to_base_room(room_spec)
        room_obj.apply_nbr5410_rules()

        room_openings = openings_dict.get(room_spec.room_type, [])
        generator.draw_room_structure(room_obj, openings=room_openings)
        generator.draw_lighting(room_obj)
        generator.draw_appliances(room_obj, openings=room_openings)

        rooms_response.append(RoomResponse(
            room_type=room_spec.room_type,
            name=room_obj.name,
            x=room_spec.x,
            y=room_spec.y,
            width=room_spec.width,
            length=room_spec.length,
            area=round(room_spec.area, 2),
            total_wattage=room_obj.get_total_wattage(),
            exterior_walls=sorted(room_spec.exterior_walls),
        ))

    dxf_filename = f"plan_s{request.seed}_w{request.width}_l{request.length}.dxf"
    generator.save(dxf_filename)

    return FloorPlanResponse(
        seed=plan.seed,
        category=program.category,
        total_width=plan.total_width,
        total_length=plan.total_length,
        total_area=round(plan.total_area, 2),
        rooms=rooms_response,
        dxf_filename=dxf_filename,
    )
