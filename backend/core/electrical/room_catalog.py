"""Catálogo de conversão RoomSpec → BaseRoom.

Centraliza o mapeamento de room_type (string do gerador BSP) para a
classe concreta de BaseRoom correspondente. Essa lógica pertence ao
domínio elétrico — é ela que faz a ponte entre a geometria pura
(RoomSpec) e a modelagem de cargas (BaseRoom + NBR 5410).
"""

from models.floor_plan import RoomSpec
from .rooms import Kitchen, Bedroom, Bathroom, BathroomSocial, Living, Corridor, Garage, LivingKitchen
from .base import BaseRoom

# Mapeamento de room_type → classe BaseRoom concreta.
# Tipos com sufixo numérico (bedroom_1, bathroom_2, …) são tratados
# pelo prefixo via room_spec_to_base_room().
ROOM_CLASS_MAP = {
    "kitchen":          Kitchen,
    "bedroom_1":        Bedroom,
    "bedroom_2":        Bedroom,
    "bedroom_3":        Bedroom,
    "bathroom_1":       Bathroom,
    "bathroom_2":       Bathroom,
    "bathroom_social":  BathroomSocial,
    "living":           Living,
    "corridor":         Corridor,
    "garage":           Garage,
    "living_kitchen":   LivingKitchen,
}


def room_spec_to_base_room(room_spec: RoomSpec, display_name: str | None = None) -> BaseRoom:
    """Converte um RoomSpec gerado pelo BSP em uma instância concreta de BaseRoom.

    Parâmetros:
        room_spec -- RoomSpec com geometria e tipo do cômodo.

    Retorna:
        Instância de BaseRoom (subclasse concreta) com geometria copiada
        do RoomSpec e exterior_walls transferidos.

    Levanta:
        ValueError -- se o room_type não estiver no catálogo.
    """
    room_class = ROOM_CLASS_MAP.get(room_spec.room_type)
    if not room_class:
        raise ValueError(f"Tipo de cômodo desconhecido: {room_spec.room_type}")

    room_obj = room_class(
        name=display_name or room_spec.room_type.replace("_", " ").title(),
        width=room_spec.width,
        length=room_spec.length,
        origin=room_spec.origin,
    )
    # Copia exterior_walls para que o DXFGenerator saiba desenhar
    # a parede externa com espessura correta.
    room_obj.exterior_walls = room_spec.exterior_walls
    return room_obj
