"""Módulo de Seleção e Dimensionamento Alvo (Room Pool)."""

from typing import List, Dict
import random

from models.floor_plan import RoomConfig

# Catálogo Master de Possíveis Cômodos a gerar
# Os weights refletem áreas alvo proporcionais para ajudar no pre-scaling
DEFAULT_ROOM_POOL = [
    RoomConfig(room_type="living", min_area=8.0, max_area=25.0, min_dimension=2.5, requires_natural_light=True, base_probability=1.0, area_threshold=0.0, weight=15.0),
    RoomConfig(room_type="kitchen", min_area=4.0, max_area=15.0, min_dimension=1.5, requires_natural_light=True, base_probability=1.0, area_threshold=0.0, weight=7.0),
    RoomConfig(room_type="bathroom_1", min_area=2.5, max_area=6.0, min_dimension=1.2, requires_natural_light=True, base_probability=1.0, area_threshold=0.0, weight=3.5),
    RoomConfig(room_type="bedroom_1", min_area=7.0, max_area=20.0, min_dimension=2.5, requires_natural_light=True, base_probability=1.0, area_threshold=0.0, weight=10.0),
    RoomConfig(room_type="bedroom_2", min_area=7.0, max_area=16.0, min_dimension=2.5, requires_natural_light=True, base_probability=0.8, area_threshold=40.0, weight=9.0),
    RoomConfig(room_type="bedroom_3", min_area=7.0, max_area=14.0, min_dimension=2.5, requires_natural_light=True, base_probability=0.3, area_threshold=70.0, weight=8.0),
    RoomConfig(room_type="bathroom_2", min_area=2.5, max_area=5.0, min_dimension=1.2, requires_natural_light=True, base_probability=0.5, area_threshold=60.0, weight=3.0),
]


class RoomSelector:
    """Seleciona da pool e pré-calcula áreas alvo para as particoes BSP."""
    
    @staticmethod
    def select_and_scale(total_area: float, rng: random.Random, catalog: List[RoomConfig] = None) -> Dict[str, float]:
        """
        Retorna um dicionário { room_type: target_area_m2 }.
        1. Seleciona os cômodos (100% obrigatorios + rng check para extras).
        2. Checa limite inferior crítico de espaço físico da casa.
        3. Realiza o scaling de weights para a target area de corte do BSP.
        """
        if catalog is None:
            catalog = DEFAULT_ROOM_POOL
            
        selected_configs = []
        for conf in catalog:
            # Filtro da área threshold
            if total_area < conf.area_threshold:
                continue
            # Rolagem RNG (deterministic via SeedContext.rng emitido)
            if conf.base_probability >= 1.0 or rng.random() < conf.base_probability:
                selected_configs.append(conf)
                
        # Checagem crassa matemática 
        min_required_area = sum(c.min_area for c in selected_configs)
        if total_area < min_required_area:
            raise ValueError(
                f"A área de {total_area}m² é inviável para acomodar todos os {len(selected_configs)} "
                f"cômodos selecionados. Mínimo regulamentar exigido: {min_required_area}m²."
            )
            
        # Distribuição de área proporcional ao weight
        total_weight = sum(c.weight for c in selected_configs)
        
        target_areas = {}
        allocated = 0.0
        
        # Passo 1: Área via Proporção + Clamp
        for conf in selected_configs:
            raw_target = (conf.weight / total_weight) * total_area
            # Clampa no min e max exigidos por NBR ou do objeto
            clamped = max(conf.min_area, min(raw_target, conf.max_area))
            target_areas[conf.room_type] = clamped
            allocated += clamped
            
        # Passo 2: Correção da diferença (se a plant for mto grande e bateu no max das coisas)
        diff = total_area - allocated
        if abs(diff) > 0.1:
            # Se o limite estourar o max de tudo, sobrou area. Acumulamos primariamente no living.
            # Alternativamente, em um caso real podemos estourar o limite max_area do living temporariamente, 
            # já que área nunca é ruim na sala.
            if "living" in target_areas:
                target_areas["living"] += diff
            else:
                # Fallback, distribui uniformemente
                bump = diff / len(target_areas)
                for r in target_areas:
                    target_areas[r] += bump
            
        return target_areas
