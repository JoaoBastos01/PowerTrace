"""Pure floor-plan and DXF generation service."""

from pathlib import Path

from app.config import settings
from app.schemas.generation import (
    GeneratedCircuitResult,
    GeneratedLoadPointResult,
    GeneratedLoadSummary,
    GeneratedRoomResult,
    GeneratedRoomLoadSummary,
    GeneratedSpecificOutletResult,
    GenerationCreateRequest,
    GenerationResult,
    RoomGenerationInput,
)
from core.drawing.engine import DXFGenerator
from core.electrical.appliances import ApplianceSource, ApplianceType
from core.electrical.base import BaseRoom
from core.electrical.room_catalog import room_spec_to_base_room
from core.electrical.tue_overrides import (
    TUEOverride,
    TUEOverrideError,
    apply_tue_overrides,
)
from core.generation.generator import FloorPlanGenerator
from core.generation.openings_placer import OpeningsPlacer
from core.generation.room_roles import resolve_room_presentation


class FloorPlanGenerationError(ValueError):
    """Expected failure when no valid procedural layout can be produced."""


class GenerationInputError(ValueError):
    """Expected failure caused by incompatible generation overrides."""


def build_tue_overrides(room_input: RoomGenerationInput) -> list[TUEOverride]:
    """Translate validated API input into domain override commands."""
    return [
        TUEOverride(
            key=outlet.id,
            name=outlet.name,
            quantity=outlet.quantity,
            power_w=outlet.power_w,
            voltage=outlet.voltage,
            power_factor=outlet.power_factor,
            enabled=outlet.enabled,
            source=ApplianceSource(outlet.source),
        )
        for outlet in room_input.specific_outlets
    ]


def build_specific_outlet_results(
    room: BaseRoom,
) -> list[GeneratedSpecificOutletResult]:
    """Expose the effective dedicated loads used by calculations and drawing."""
    return [
        GeneratedSpecificOutletResult(
            key=appliance.key,
            name=appliance.name,
            power_w=appliance.wattage,
            voltage=appliance.voltage,
            power_factor=appliance.pf,
            source=appliance.source.value,
        )
        for appliance in room.appliances
        if appliance.type == ApplianceType.DEDICATED
        and appliance.key is not None
    ]


def build_load_point_results(
    room: BaseRoom,
    room_type: str,
) -> tuple[list[GeneratedLoadPointResult], dict[int, GeneratedLoadPointResult]]:
    """Build stable public load identifiers for one generated room."""
    counters = {
        ApplianceType.LIGHTING: 0,
        ApplianceType.GENERAL: 0,
        ApplianceType.DEDICATED: 0,
    }
    results: list[GeneratedLoadPointResult] = []
    by_appliance: dict[int, GeneratedLoadPointResult] = {}

    for appliance in room.appliances:
        counters[appliance.type] += 1
        key = appliance.key or (
            f"{room_type}_{appliance.type.value}_{counters[appliance.type]}"
        )
        result = GeneratedLoadPointResult(
            key=key,
            name=appliance.name,
            load_type=appliance.type.value,
            power_w=appliance.wattage,
            voltage=appliance.voltage,
            power_factor=appliance.pf,
            source=appliance.source.value,
        )
        results.append(result)
        by_appliance[id(appliance)] = result

    return results, by_appliance


def build_load_summary(
    load_points: list[GeneratedLoadPointResult],
) -> GeneratedRoomLoadSummary:
    """Aggregate room loads by the categories presented in the dashboard."""

    def summarize(load_type: str) -> GeneratedLoadSummary:
        matches = [
            point for point in load_points if point.load_type == load_type
        ]
        return GeneratedLoadSummary(
            count=len(matches),
            total_power_w=sum(point.power_w for point in matches),
        )

    return GeneratedRoomLoadSummary(
        lighting=summarize(ApplianceType.LIGHTING.value),
        general_outlets=summarize(ApplianceType.GENERAL.value),
        specific_outlets=summarize(ApplianceType.DEDICATED.value),
        total_power_w=sum(point.power_w for point in load_points),
    )


def build_circuit_results(
    room: BaseRoom,
    room_type: str,
    load_points_by_appliance: dict[int, GeneratedLoadPointResult],
    first_sequence: int,
) -> list[GeneratedCircuitResult]:
    """Dimension and serialize all circuits produced for one room."""
    results: list[GeneratedCircuitResult] = []

    for offset, circuit in enumerate(room.build_circuits()):
        try:
            dimension = circuit.dimension()
        except ValueError as exc:
            raise GenerationInputError(
                f"Não foi possível dimensionar o circuito "
                f"'{circuit.circuit_id}': {exc}"
            ) from exc

        circuit_load_points = [
            load_points_by_appliance[id(appliance)]
            for appliance in circuit.load_points
        ]
        circuit_type = circuit_load_points[0].load_type
        results.append(
            GeneratedCircuitResult(
                id=f"C{first_sequence + offset:02d}",
                name=circuit.circuit_id,
                room_type=room_type,
                room_name=room.name,
                circuit_type=circuit_type,
                voltage=circuit.voltage,
                power_factor=circuit.pf,
                load_count=len(circuit_load_points),
                total_power_w=dimension.total_wattage,
                current_a=dimension.current,
                design_current_a=dimension.design_current,
                breaker_a=dimension.breaker,
                wire_gauge_mm2=dimension.wire.gauge_mm2,
                wire_max_current_a=dimension.wire.max_current,
                wire_resistance_ohm_km=dimension.wire.resistance,
                load_points=circuit_load_points,
            )
        )

    return results


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

        room_inputs = {room.room_key: room for room in request.rooms}
        generated_room_keys = {room.room_type for room in plan.rooms}
        unknown_room_keys = sorted(room_inputs.keys() - generated_room_keys)
        if unknown_room_keys:
            unknown_rooms = ", ".join(unknown_room_keys)
            raise GenerationInputError(
                f"Room overrides reference rooms not present in the generated "
                f"plan: {unknown_rooms}."
            )

        openings_by_room = OpeningsPlacer.generate_openings(plan, graph, program)
        generator = DXFGenerator()
        rooms: list[GeneratedRoomResult] = []
        circuits: list[GeneratedCircuitResult] = []

        for room_spec in plan.rooms:
            presentation = resolve_room_presentation(
                room_spec.room_type, program.category
            )
            room_input = room_inputs.get(room_spec.room_type)
            display_name = (
                room_input.display_name
                if room_input is not None and room_input.display_name is not None
                else presentation.display_name
            )
            room = room_spec_to_base_room(
                room_spec, display_name=display_name
            )
            room.apply_nbr5410_rules()
            if room_input is not None:
                try:
                    apply_tue_overrides(
                        room,
                        build_tue_overrides(room_input),
                    )
                except TUEOverrideError as exc:
                    raise GenerationInputError(str(exc)) from exc

            load_points, load_points_by_appliance = build_load_point_results(
                room,
                room_spec.room_type,
            )
            load_summary = build_load_summary(load_points)
            room_circuits = build_circuit_results(
                room,
                room_spec.room_type,
                load_points_by_appliance,
                len(circuits) + 1,
            )
            circuits.extend(room_circuits)

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
                    load_points=load_points,
                    load_summary=load_summary,
                    specific_outlets=build_specific_outlet_results(room),
                )
            )

        generator.save(dxf_filename)
        return GenerationResult(
            seed=plan.seed,
            category=program.category,
            total_width=plan.total_width,
            total_length=plan.total_length,
            total_area=round(plan.total_area, 2),
            total_power_w=sum(room.total_wattage for room in rooms),
            rooms=rooms,
            circuits=circuits,
            dxf_filename=dxf_filename,
        )
    except Exception:
        output_path.unlink(missing_ok=True)
        raise
