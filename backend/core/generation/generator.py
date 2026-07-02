"""Orquestrador do pipeline Topology-First de geração de plantas."""

import logging
from typing import Tuple

from .seed import SeedContext
from .program import ProgramGenerator, HouseProgram
from .layout import TopologyBSP, validate_topology
from .adjacency import AdjacencyGraph
from models.floor_plan import FloorPlan, RoomSpec

logger = logging.getLogger(__name__)


class FloorPlanGenerator:
    """Gerencia o pipeline Topology-First de geração procedural."""

    def __init__(self, master_seed: int, width: float, length: float):
        self.ctx = SeedContext(master_seed=master_seed)
        self.width = width
        self.length = length
        self.area = width * length

    def generate(self, max_attempts: int = 50) -> Tuple[FloorPlan, AdjacencyGraph, HouseProgram]:
        """Executa o pipeline completo de geração.

        Retorna:
            Tupla (FloorPlan, AdjacencyGraph, HouseProgram).

        Levanta:
            ValueError -- Se não conseguir gerar após max_attempts.
        """
        # ── Fase 1: Program (determinístico no master_seed) ──────
        program_rng = self.ctx.rng("program")
        program = ProgramGenerator.generate(self.area, program_rng)

        logger.info(
            f"Program: categoria='{program.category}', "
            f"cômodos={list(program.rooms.keys())}"
        )

        # ── Fase 2: Layout (com retry para dimensões mínimas) ────
        for attempt in range(max_attempts):
            layout_rng = self.ctx.rng("layout", f"attempt_{attempt}")

            bsp = TopologyBSP(program, self.width, self.length)
            leaves = bsp.build(layout_rng)

            if not leaves:
                logger.debug(f"Attempt {attempt}: BSP falhou (dimensão mínima).")
                continue

            # Validar luz natural
            from .program import ROOM_CATALOG
            light_ok = True
            for leaf in leaves:
                config = ROOM_CATALOG.get(leaf.room_type)
                if config and config.requires_natural_light:
                    if len(leaf.exterior_walls) == 0:
                        logger.debug(f"Attempt {attempt}: {leaf.room_type} sem luz natural.")
                        light_ok = False
                        break

            if not light_ok:
                continue

            if not validate_topology(leaves, program):
                logger.debug(f"Attempt {attempt}: topologia não satisfeita geometricamente.")
                continue

            # ── Sucesso! Construir o FloorPlan ────────────────────
            graph = AdjacencyGraph(leaves)

            # Ordena as salas de forma determinística por coordenada
            # para garantir reprodutibilidade mesmo com hash randomization.
            sorted_rooms = sorted(graph.rooms.values(), key=lambda r: (r.y, r.x))

            plan = FloorPlan(
                seed=self.ctx.master_seed,
                total_width=self.width,
                total_length=self.length,
                rooms=sorted_rooms,
            )

            taxa_falha = (attempt / max_attempts) * 100
            logger.info(
                f"Layout gerado com sucesso! Tentativas necessárias: {attempt + 1}/{max_attempts} "
                f"(Taxa de falha: {taxa_falha:.1f}%)."
            )
            logger.info(f"Categoria: {program.category} | Cômodos gerados: {len(plan.rooms)}")
            return plan, graph, program

        raise ValueError(
            f"Não foi possível gerar planta válida após {max_attempts} tentativas. "
            f"Tente dimensões diferentes ou outro seed."
        )
