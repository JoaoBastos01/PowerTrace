"""Orchestrator for procedural floor plan generation."""

import logging
from typing import Optional, List, Dict
from .seed import SeedContext
from .pool import RoomSelector, DEFAULT_ROOM_POOL
from .bsp import BSPTreeGenerator
from .adjacency import AdjacencyGraph
from models.floor_plan import FloorPlan, RoomConfig, RoomSpec

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FloorPlanGenerator:
    """Manages the procedural generation pipeline uniting Pool, BSP and Adjacency."""

    def __init__(self, master_seed: int, width: float, length: float, catalog: List[RoomConfig] = None):
        self.ctx = SeedContext(master_seed=master_seed)
        self.width = width
        self.length = length
        self.area = width * length
        self.catalog = catalog if catalog is not None else DEFAULT_ROOM_POOL

    def generate(self, max_attempts: int = 100) -> FloorPlan:
        """
        Runs the generation pipeline until a valid architecture is found.
        Raises ValueError if it cannot find a valid layout after max_attempts.
        """
        pool_rng = self.ctx.rng("pool")
        
        # Step 1: Select and scale rooms (Deterministic on master_seed, only done once per plan)
        try:
            target_areas = RoomSelector.select_and_scale(self.area, pool_rng, self.catalog)
        except ValueError as e:
            logger.error(f"Generation aborted at Pool Stage: {str(e)}")
            raise e

        # Loop through attempts for BSP and Adjacency
        for attempt in range(max_attempts):
            attempt_rng = self.ctx.rng("bsp", f"attempt_{attempt}")
            
            # Step 2: BSP Slicing
            bsp = BSPTreeGenerator(target_areas, self.width, self.length)
            leaves = bsp.build_tree(attempt_rng)
            
            if not leaves:
                logger.debug(f"Attempt {attempt} failed: BSP minimum dimension rule triggered.")
                continue
                
            # Step 3: Adjacency Graph and Geometric Rules
            graph = AdjacencyGraph(leaves)
            
            light_rule_passed = True
            for conf in self.catalog:
                if conf.room_type in graph.rooms and conf.requires_natural_light:
                    room = graph.rooms[conf.room_type]
                    if len(room.exterior_walls) == 0:
                        logger.debug(f"Attempt {attempt} failed: {conf.room_type} is trapped without windows.")
                        light_rule_passed = False
                        break
            
            if not light_rule_passed:
                continue
                
            if not graph.validate_architecture():
                logger.debug(f"Attempt {attempt} failed: Adjacency or Zoning rules broken (zombie layout).")
                continue
                
            # Valid layout found!
            logger.info(f"Successfully generated a valid layout on attempt {attempt}.")
            plan = FloorPlan(
                seed=self.ctx.master_seed,
                total_width=self.width,
                total_length=self.length,
                rooms=list(graph.rooms.values())
            )
            return plan, graph
            
        raise ValueError(f"Could not generate a valid floor plan after {max_attempts} attempts. Try different dimensions or another seed.")
