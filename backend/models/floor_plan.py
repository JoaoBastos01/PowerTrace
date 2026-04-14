"""Modelos de dados para o FloorPlan gerado proceduralmente."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import FrozenSet, List


@dataclass(frozen=True)
class RoomConfig:
    """Configuração estática de um tipo de cômodo.

    Define as restrições geométricas, a exigência de luz natural e os
    parâmetros de probabilidade usados pelo pool de geração.

    Atributos:
        room_type             -- Identificador do tipo ('bedroom', 'kitchen', …).
        min_area              -- Área mínima permitida (m²).
        max_area              -- Área máxima permitida (m²).
        min_dimension         -- Menor dimensão (lado) permitida (m) — controla o aspecto.
        requires_natural_light-- Se True, o cômodo precisa de ≥1 parede exterior.
                                 Layouts que violem isso são rejeitados pelo BSP.
        base_probability      -- Probabilidade de inclusão [0.0–1.0].
                                 1.0 = sempre presente na planta.
        area_threshold        -- Área total mínima da planta (m²) para que
                                 este cômodo seja elegível para inclusão.
        weight                -- Peso relativo no corte BSP.
                                 Cômodos maiores devem ter peso proporcional
                                 à sua área-alvo típica.
    """
    room_type:              str
    min_area:               float
    max_area:               float
    min_dimension:          float
    requires_natural_light: bool
    base_probability:       float
    area_threshold:         float
    weight:                 float


@dataclass
class RoomSpec:
    """Especificação geométrica de um cômodo na planta gerada.

    Produzida pelo BSP e consumida tanto pelo drawing engine quanto pelo
    OpeningPlacer. O campo `exterior_walls` rastreia quais das 4 paredes
    ainda são externas após os cortes BSP.

    Atributos:
        room_type      -- Tipo do cômodo ('bedroom', 'kitchen', …).
        x              -- Coordenada X do canto SW (origem).
        y              -- Coordenada Y do canto SW (origem).
        width          -- Largura em metros (eixo X).
        length         -- Comprimento em metros (eixo Y).
        exterior_walls -- Subconjunto de {'S','E','N','W'} com as paredes externas.
                          Começa como {'S','E','N','W'} e perde paredes a cada
                          corte BSP que cria uma parede compartilhada.
    """
    room_type:      str
    x:              float
    y:              float
    width:          float
    length:         float
    exterior_walls: FrozenSet[str] = field(
        default_factory=lambda: frozenset({'S', 'E', 'N', 'W'})
    )

    @property
    def area(self) -> float:
        return self.width * self.length

    @property
    def origin(self) -> tuple:
        return (self.x, self.y)


@dataclass
class FloorPlan:
    """Planta completa gerada pelo FloorPlanGenerator.

    Agrega os metadados da geração e a lista de cômodos posicionados.
    É o objeto transferido entre o gerador, o OpeningPlacer e o DXFGenerator.

    Atributos:
        seed         -- Seed usada para gerar esta planta (reprodutibilidade).
        total_width  -- Largura total da planta (m).
        total_length -- Comprimento total da planta (m).
        rooms        -- Lista de RoomSpec posicionados no plano.
    """
    seed:         int
    total_width:  float
    total_length: float
    rooms:        List[RoomSpec] = field(default_factory=list)

    @property
    def total_area(self) -> float:
        return self.total_width * self.total_length
