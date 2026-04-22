"""Módulo de Posicionamento Lógico de Aberturas (Portas e Janelas)."""

from typing import Dict, List
from models.floor_plan import FloorPlan
from services.drawing.openings import Opening
from services.generation.adjacency import AdjacencyGraph

class OpeningsPlacer:
    """Distribui portas e janelas com base no grafo de intersecções."""
    
    @staticmethod
    def generate_openings(plan: FloorPlan, graph: AdjacencyGraph) -> Dict[str, List[Opening]]:
        """
        Gera o dicionário injetável de Openings para o DXFGenerator.
        Retorna: { 'living': [Opening(...)], 'bedroom_1': [...] }
        """
        openings_dict: Dict[str, List[Opening]] = {rspec.room_type: [] for rspec in plan.rooms}
        
        placed_doors = set()
        doors_count = {rspec.room_type: 0 for rspec in plan.rooms}
        
        # 1. Portas Internas baseadas na Adjacência (Fase 3 do Generator)
        for room_name, adj_set in graph.edges.items():
            r1 = graph.rooms[room_name]
            
            # Prioriza abrir porta para a Sala ou Corredor, ignorando vizinhos de baixo calão
            sorted_adjs = sorted(list(adj_set), key=lambda r: 0 if r in ['living', 'corridor'] else 1)
            
            for adj_name in sorted_adjs:
                edge_id = tuple(sorted([room_name, adj_name]))
                if edge_id in placed_doors:
                    continue
                    
                # Regra Arquitetural: Não permitir um quarto encruzilhada.
                # Se não for uma área mestre de passagem (living/hub) e já tiver 1 porta, trava o pedreiro.
                is_r1_hub = room_name in ['living', 'corridor']
                is_r2_hub = adj_name in ['living', 'corridor']
                
                if not is_r1_hub and doors_count[room_name] >= 1:
                    continue
                if not is_r2_hub and doors_count[adj_name] >= 1:
                    continue
                    
                doors_count[room_name] += 1
                doors_count[adj_name] += 1
                
                r2 = graph.rooms[adj_name]
                door_w = 0.8
                boneca_ideal = 0.15  # Afastamento ideal
                
                # Eixo X (Corte vertical, lado Leste/Oeste)
                if abs((r1.x + r1.width) - r2.x) < 0.05:
                    y_start = max(r1.y, r2.y)
                    y_end = min(r1.y + r1.length, r2.y + r2.length)
                    overlap = y_end - y_start
                    
                    if overlap < door_w:
                        continue
                        
                    # Aperta a boneca se a parede compartilhada for muito justa (ex: Living-Bedroom2 tem 0.9m)
                    boneca = min(boneca_ideal, (overlap - door_w) / 2.0)
                    abs_y = y_start + boneca
                    
                    # r1 tem 'E' (vai do Sul p Norte), r2 tem 'W' (vai do Norte p Sul)
                    off_r1 = abs_y - r1.y
                    off_r2 = (r2.y + r2.length) - (abs_y + door_w)
                    
                    openings_dict[r1.room_type].append(Opening(wall='E', offset=off_r1, width=door_w, kind='gap', swing='right'))
                    openings_dict[r2.room_type].append(Opening(wall='W', offset=off_r2, width=door_w, kind='door', swing='left'))
                    placed_doors.add(edge_id)
                    doors_count[room_name] += 1
                    doors_count[adj_name] += 1
                    continue

                if abs((r2.x + r2.width) - r1.x) < 0.05:
                    y_start = max(r1.y, r2.y)
                    y_end = min(r1.y + r1.length, r2.y + r2.length)
                    overlap = y_end - y_start
                    
                    if overlap < door_w:
                        continue
                        
                    boneca = min(boneca_ideal, (overlap - door_w) / 2.0)
                    abs_y = y_start + boneca
                    
                    off_r2 = abs_y - r2.y
                    off_r1 = (r1.y + r1.length) - (abs_y + door_w)
                    
                    openings_dict[r2.room_type].append(Opening(wall='E', offset=off_r2, width=door_w, kind='gap', swing='right'))
                    openings_dict[r1.room_type].append(Opening(wall='W', offset=off_r1, width=door_w, kind='door', swing='left'))
                    placed_doors.add(edge_id)
                    doors_count[room_name] += 1
                    doors_count[adj_name] += 1
                    continue
                    
                # Eixo Y (Corte horizontal, lado Norte/Sul)
                if abs((r1.y + r1.length) - r2.y) < 0.05:
                    x_start = max(r1.x, r2.x)
                    x_end = min(r1.x + r1.width, r2.x + r2.width)
                    overlap = x_end - x_start
                    
                    if overlap < door_w:
                        continue
                        
                    boneca = min(boneca_ideal, (overlap - door_w) / 2.0)
                    abs_x = x_start + boneca
                    
                    # r1 tem 'N' (vai do Leste p Oeste), r2 tem 'S' (vai do Oeste p Leste)
                    off_r2 = abs_x - r2.x 
                    off_r1 = (r1.x + r1.width) - (abs_x + door_w)
                    
                    openings_dict[r1.room_type].append(Opening(wall='N', offset=off_r1, width=door_w, kind='gap', swing='right'))
                    openings_dict[r2.room_type].append(Opening(wall='S', offset=off_r2, width=door_w, kind='door', swing='left'))
                    placed_doors.add(edge_id)
                    doors_count[room_name] += 1
                    doors_count[adj_name] += 1
                    continue
                    
                if abs((r2.y + r2.length) - r1.y) < 0.05:
                    x_start = max(r1.x, r2.x)
                    x_end = min(r1.x + r1.width, r2.x + r2.width)
                    overlap = x_end - x_start
                    
                    if overlap < door_w:
                        continue
                        
                    boneca = min(boneca_ideal, (overlap - door_w) / 2.0)
                    abs_x = x_start + boneca
                    
                    off_r1 = abs_x - r1.x
                    off_r2 = (r2.x + r2.width) - (abs_x + door_w)
                    
                    openings_dict[r1.room_type].append(Opening(wall='S', offset=off_r1, width=door_w, kind='gap', swing='right'))
                    openings_dict[r2.room_type].append(Opening(wall='N', offset=off_r2, width=door_w, kind='door', swing='left'))
                    placed_doors.add(edge_id)
                    doors_count[room_name] += 1
                    doors_count[adj_name] += 1
                    continue

        # 2. Janelas Extenas e Porta de Entrada Principal
        has_main_door = False
        
        for rspec in plan.rooms:
            # Lista apenas a fachada de maior extensao para ganhar a janela (evita excesso na renderização)
            if not rspec.exterior_walls:
                 continue
                 
            # Ordena decrescente pelo comprimento do segmento
            best_walls = sorted(list(rspec.exterior_walls), 
                                key=lambda e: rspec.width if e in ['S', 'N'] else rspec.length, 
                                reverse=True)
            
            main_ext = best_walls[0]
            wall_length = rspec.width if main_ext in ['S', 'N'] else rspec.length
            boneca = 0.20
            
            if not has_main_door and rspec.room_type == "living":
                # Living abriga a porta de 0.9m da calçada + Janela nela
                has_main_door = True
                main_w = 0.9
                openings_dict[rspec.room_type].append(Opening(wall=main_ext, offset=boneca, width=main_w, kind='door', swing='right'))
                
                win_w = 1.2
                win_off = (wall_length / 2) - (win_w / 2)
                if win_off < (boneca + main_w + 0.3):
                    win_off = wall_length - win_w - 0.2
                
                # Evitar que parede muito estreita crie janela pra fora
                if win_off > 0 and (win_off + win_w) < wall_length:
                    openings_dict[rspec.room_type].append(Opening(wall=main_ext, offset=win_off, width=win_w, kind='window'))
            else:
                # Quartos e Cozinha recebem janelas de 1.2m
                win_w = 1.2
                
                # Banheiros recebem janelas do tipo Vitrô super menores
                if rspec.room_type.startswith("bathroom"):
                    win_w = 0.60
                    
                win_off = (wall_length / 2) - (win_w / 2)
                
                if win_off > 0 and (win_off + win_w) < wall_length:
                    openings_dict[rspec.room_type].append(Opening(wall=main_ext, offset=win_off, width=win_w, kind='window'))
                    
        return openings_dict
