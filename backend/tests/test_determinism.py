import json
import os
import subprocess
import sys

from core.drawing.engine import DXFGenerator
from core.electrical.room_catalog import room_spec_to_base_room
from core.generation.generator import FloorPlanGenerator
from core.generation.openings_placer import OpeningsPlacer


PLAN_SIGNATURE_SCRIPT = r"""
import json

from core.generation.generator import FloorPlanGenerator
from core.generation.openings_placer import OpeningsPlacer

plan, graph, program = FloorPlanGenerator(master_seed=42, width=8.0, length=12.0).generate(
    max_attempts=300
)
openings = OpeningsPlacer.generate_openings(plan, graph)

signature = {
    "program": {
        "category": program.category,
        "rooms": program.rooms,
        "topology": program.topology,
    },
    "rooms": [
        {
            "room_type": room.room_type,
            "x": round(room.x, 8),
            "y": round(room.y, 8),
            "width": round(room.width, 8),
            "length": round(room.length, 8),
            "exterior_walls": sorted(room.exterior_walls),
        }
        for room in plan.rooms
    ],
    "openings": {
        room_type: [
            {
                "wall": opening.wall,
                "offset": round(opening.offset, 8),
                "width": round(opening.width, 8),
                "kind": opening.kind,
                "swing": opening.swing,
            }
            for opening in room_openings
        ]
        for room_type, room_openings in sorted(openings.items())
    },
}

print(json.dumps(signature, sort_keys=True))
"""


def _signature_with_hash_seed(hash_seed: int) -> dict:
    env = os.environ.copy()
    env["PYTHONHASHSEED"] = str(hash_seed)
    result = subprocess.run(
        [sys.executable, "-c", PLAN_SIGNATURE_SCRIPT],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    return json.loads(result.stdout)


def test_generation_signature_is_stable_across_hash_seeds():
    signatures = [_signature_with_hash_seed(seed) for seed in range(1, 6)]

    assert signatures == [signatures[0]] * len(signatures)


def _generate_dxf(output_file: str) -> bytes:
    plan, graph, _ = FloorPlanGenerator(master_seed=42, width=8.0, length=12.0).generate(
        max_attempts=300
    )
    openings = OpeningsPlacer.generate_openings(plan, graph)
    generator = DXFGenerator()

    for room_spec in plan.rooms:
        room = room_spec_to_base_room(room_spec)
        room.apply_nbr5410_rules()
        room_openings = openings.get(room_spec.room_type, [])
        generator.draw_room_structure(room, openings=room_openings)
        generator.draw_lighting(room)
        generator.draw_appliances(room, openings=room_openings)

    path = generator.save(output_file)
    with open(path, "rb") as file:
        return file.read()


def test_dxf_bytes_are_stable_for_same_parameters(tmp_path, monkeypatch):
    monkeypatch.setattr("app.config.settings.output_dir", str(tmp_path))

    assert _generate_dxf("first.dxf") == _generate_dxf("second.dxf")
