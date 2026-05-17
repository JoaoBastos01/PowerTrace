"""Fase 1: Program — Seleção de cômodos e definição de topologia.

Este módulo implementa o conceito de "programa de necessidades" da
arquitetura: antes de desenhar qualquer planta, definimos QUAIS cômodos
existem e COMO eles se conectam (topologia).

A topologia é definida por templates pré-configurados para cada categoria
de casa (kitnet, small, medium, large). Cômodos opcionais são incluídos
ou não com base em um orçamento de área (budget constraint), garantindo
que casas pequenas não fiquem superlotadas.

Design:
    ProgramGenerator.generate(area, rng) -> HouseProgram
    O HouseProgram contém tudo que as fases seguintes precisam:
    - rooms: {room_type: target_area_m2}
    - topology: {room_type: [vizinhos]}
    - category: "kitnet" | "small" | "medium" | "large"
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple

from models.floor_plan import RoomConfig


# ──────────────────────────────────────────────────────────────────────
# Catálogo de cômodos (configurações reutilizáveis de cada tipo)
# ──────────────────────────────────────────────────────────────────────

ROOM_CATALOG: Dict[str, RoomConfig] = {
    "living": RoomConfig(
        room_type="living", min_area=8.0, max_area=25.0,
        min_dimension=2.5, requires_natural_light=True,
        base_probability=1.0, area_threshold=0.0, weight=15.0,
    ),
    "kitchen": RoomConfig(
        room_type="kitchen", min_area=4.0, max_area=15.0,
        min_dimension=1.5, requires_natural_light=True,
        base_probability=1.0, area_threshold=0.0, weight=7.0,
    ),
    "living_kitchen": RoomConfig(
        room_type="living_kitchen", min_area=10.0, max_area=22.0,
        min_dimension=2.5, requires_natural_light=True,
        base_probability=1.0, area_threshold=0.0, weight=16.0,
    ),
    "bathroom_1": RoomConfig(
        room_type="bathroom_1", min_area=2.5, max_area=6.0,
        min_dimension=1.2, requires_natural_light=False,
        base_probability=1.0, area_threshold=0.0, weight=3.5,
    ),
    "bathroom_2": RoomConfig(
        room_type="bathroom_2", min_area=2.5, max_area=5.0,
        min_dimension=1.2, requires_natural_light=False,
        base_probability=1.0, area_threshold=0.0, weight=3.0,
    ),
    "bedroom_1": RoomConfig(
        room_type="bedroom_1", min_area=7.0, max_area=20.0,
        min_dimension=2.5, requires_natural_light=True,
        base_probability=1.0, area_threshold=0.0, weight=10.0,
    ),
    "bedroom_2": RoomConfig(
        room_type="bedroom_2", min_area=7.0, max_area=16.0,
        min_dimension=2.5, requires_natural_light=True,
        base_probability=1.0, area_threshold=0.0, weight=9.0,
    ),
    "bedroom_3": RoomConfig(
        room_type="bedroom_3", min_area=7.0, max_area=14.0,
        min_dimension=2.5, requires_natural_light=True,
        base_probability=1.0, area_threshold=0.0, weight=8.0,
    ),
    "corridor": RoomConfig(
        room_type="corridor", min_area=2.0, max_area=6.0,
        min_dimension=1.0, requires_natural_light=False,
        base_probability=1.0, area_threshold=0.0, weight=2.5,
    ),
    "garage": RoomConfig(
        room_type="garage", min_area=10.0, max_area=20.0,
        min_dimension=2.5, requires_natural_light=False,
        base_probability=1.0, area_threshold=0.0, weight=12.0,
    ),
}


# ──────────────────────────────────────────────────────────────────────
# Templates de topologia por categoria de casa
# ──────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class TopologyTemplate:
    """Template de topologia para uma categoria de casa.

    Cada template define:
    - required: cômodos obrigatórios (sempre presentes)
    - optional: cômodos opcionais com probabilidade (incluídos se o
      orçamento de área permitir E o rng decidir)
    - topology: grafo de adjacência requerida entre cômodos
      (bidirecional — se A lista B, B deve listar A)
    """
    required: tuple
    optional: tuple  # ((room_type, probability), ...)
    topology: Dict[str, tuple]


HOUSE_TEMPLATES: Dict[str, TopologyTemplate] = {
    # ── Kitnet (< 35m²) ─────────────────────────────────────────
    # Sala e cozinha integradas + banheiro. Mínimo absoluto.
    "kitnet": TopologyTemplate(
        required=("living_kitchen", "bathroom_1"),
        optional=(),
        topology={
            "living_kitchen": ("bathroom_1",),
            "bathroom_1": ("living_kitchen",),
        },
    ),

    # ── Pequena (35–60m²) ────────────────────────────────────────
    # Living é o hub central. Sem corredor (área não justifica).
    "small": TopologyTemplate(
        required=("living", "kitchen", "bathroom_1", "bedroom_1"),
        optional=(
            ("bedroom_2", 0.6),
        ),
        topology={
            "living": ("kitchen", "bathroom_1", "bedroom_1", "bedroom_2"),
            "kitchen": ("living",),
            "bathroom_1": ("living",),
            "bedroom_1": ("living",),
            "bedroom_2": ("living",),
        },
    ),

    # ── Média (60–100m²) ─────────────────────────────────────────
    # Corredor distribui a zona íntima. Suíte opcional.
    "medium": TopologyTemplate(
        required=("living", "kitchen", "corridor", "bathroom_1", "bedroom_1", "bedroom_2"),
        optional=(
            ("bedroom_3", 0.15),
            ("bathroom_2", 0.35),
        ),
        topology={
            "living": ("kitchen", "corridor"),
            "kitchen": ("living",),
            "corridor": ("bathroom_1", "bedroom_1", "bedroom_2", "bedroom_3"),
            "bathroom_1": ("corridor",),
            "bedroom_1": ("corridor", "bathroom_2"),
            "bedroom_2": ("corridor",),
            "bedroom_3": ("corridor",),
            "bathroom_2": ("bedroom_1",),
        },
    ),

    # ── Grande (> 100m²) ─────────────────────────────────────────
    # Tudo da média + garagem e 3° quarto obrigatório.
    "large": TopologyTemplate(
        required=("living", "kitchen", "corridor", "bathroom_1",
                  "bedroom_1", "bedroom_2", "bedroom_3", "garage"),
        optional=(
            ("bathroom_2", 0.7),
        ),
        topology={
            "living": ("kitchen", "corridor", "garage"),
            "kitchen": ("living",),
            "corridor": ("bathroom_1", "bedroom_1", "bedroom_2", "bedroom_3"),
            "bathroom_1": ("corridor",),
            "bedroom_1": ("corridor", "bathroom_2"),
            "bedroom_2": ("corridor",),
            "bedroom_3": ("corridor",),
            "bathroom_2": ("bedroom_1",),
            "garage": ("living",),
        },
    ),
}


# ──────────────────────────────────────────────────────────────────────
# HouseProgram — output da Fase 1
# ──────────────────────────────────────────────────────────────────────

@dataclass
class HouseProgram:
    """Briefing completo da casa: cômodos + topologia + áreas alvo.

    Este objeto contém TUDO que as fases seguintes (Layout e Openings)
    precisam. Nenhuma decisão arquitetural fica para depois.

    Atributos:
        category -- Classificação da casa ("kitnet", "small", "medium", "large").
        rooms    -- Mapa {room_type: target_area_m2} com áreas alvo.
        topology -- Grafo de adjacência {room_type: [vizinhos]}.
    """
    category: str
    rooms: Dict[str, float]
    topology: Dict[str, List[str]]

    @property
    def topology_edges(self) -> Set[Tuple[str, str]]:
        """Retorna o conjunto de arestas únicas da topologia (sem duplicatas)."""
        edges = set()
        for room, neighbors in self.topology.items():
            for neighbor in neighbors:
                edge = tuple(sorted([room, neighbor]))
                edges.add(edge)
        return edges

    @property
    def root_room(self) -> str:
        """Retorna o cômodo raiz da topologia (living ou living_kitchen)."""
        if "living" in self.rooms:
            return "living"
        return "living_kitchen"


# ──────────────────────────────────────────────────────────────────────
# ProgramGenerator — orquestra a Fase 1
# ──────────────────────────────────────────────────────────────────────

class ProgramGenerator:
    """Gera o HouseProgram baseado na área total e um RNG determinístico.

    Pipeline interno:
        1. Classifica a casa por área
        2. Seleciona cômodos obrigatórios do template
        3. Tenta incluir opcionais usando budget constraint
        4. Aloca áreas proporcionais ao weight de cada cômodo
        5. Poda a topologia removendo cômodos não selecionados
    """

    # Margem de conforto (m²) exigida para cada cômodo opcional.
    # Impede que a casa fique apertada ao incluir um cômodo extra.
    COMFORT_MARGIN = 4.0

    @staticmethod
    def classify(area: float) -> str:
        """Classifica a casa em uma categoria baseada na área total."""
        if area < 35:
            return "kitnet"
        elif area < 60:
            return "small"
        elif area < 100:
            return "medium"
        else:
            return "large"

    @staticmethod
    def generate(total_area: float, rng: random.Random) -> HouseProgram:
        """Gera o programa completo da casa.

        Parâmetros:
            total_area -- Área total da planta em m².
            rng        -- RNG determinístico (do SeedContext).

        Retorna:
            HouseProgram pronto para ser consumido pelo Layout e Openings.

        Levanta:
            ValueError -- Se a área é insuficiente para os cômodos obrigatórios.
        """
        category = ProgramGenerator.classify(total_area)
        template = HOUSE_TEMPLATES[category]

        # 1. Selecionar cômodos obrigatórios
        selected = list(template.required)

        # 2. Calcular orçamento residual
        budget = total_area - sum(ROOM_CATALOG[r].min_area for r in selected)

        if budget < 0:
            raise ValueError(
                f"Área de {total_area}m² insuficiente para casa '{category}'. "
                f"Mínimo necessário: {sum(ROOM_CATALOG[r].min_area for r in selected)}m²."
            )

        # 3. Tentar incluir opcionais (greedy, por ordem de prioridade)
        for room_type, probability in template.optional:
            config = ROOM_CATALOG[room_type]
            cost = config.min_area + ProgramGenerator.COMFORT_MARGIN

            if budget >= cost and rng.random() < probability:
                selected.append(room_type)
                budget -= config.min_area

        # 4. Alocar áreas proporcionais ao weight
        rooms = ProgramGenerator._allocate_areas(selected, total_area)

        # 5. Podar topologia (remover cômodos não selecionados)
        topology = ProgramGenerator._prune_topology(template.topology, selected)

        return HouseProgram(category=category, rooms=rooms, topology=topology)

    @staticmethod
    def _allocate_areas(selected: List[str], total_area: float) -> Dict[str, float]:
        """Distribui a área total proporcionalmente ao weight de cada cômodo.

        Garante que cada cômodo tenha área suficiente para que seu lado
        menor seja >= min_dimension do catálogo (evita que o BSP gere
        cômodos impossíveis de cortar).

        Algoritmo:
        1. Calcula área bruta proporcional ao weight
        2. Clampa nos limites min/max do catálogo
        3. Garante que min_area é geometricamente viável
        4. Distribui a sobra/falta no living (cômodo mais flexível)
        """
        configs = [ROOM_CATALOG[r] for r in selected]
        total_weight = sum(c.weight for c in configs)

        areas = {}
        allocated = 0.0

        for conf in configs:
            raw = (conf.weight / total_weight) * total_area
            clamped = max(conf.min_area, min(raw, conf.max_area))
            areas[conf.room_type] = clamped
            allocated += clamped

        # Distribuir diferença no cômodo principal
        diff = total_area - allocated
        if abs(diff) > 0.1:
            primary = "living" if "living" in areas else "living_kitchen"
            if primary in areas:
                areas[primary] += diff
            else:
                bump = diff / len(areas)
                for r in areas:
                    areas[r] += bump

        return areas

    @staticmethod
    def _prune_topology(
        topology: Dict[str, tuple],
        selected: List[str],
    ) -> Dict[str, List[str]]:
        """Remove cômodos não selecionados do grafo de topologia.

        Se bedroom_3 não foi selecionado:
        ANTES:  corridor → [bathroom_1, bedroom_1, bedroom_2, bedroom_3]
        DEPOIS: corridor → [bathroom_1, bedroom_1, bedroom_2]
        """
        selected_set = set(selected)
        pruned = {}
        for room, neighbors in topology.items():
            if room in selected_set:
                pruned[room] = [n for n in neighbors if n in selected_set]
        return pruned
