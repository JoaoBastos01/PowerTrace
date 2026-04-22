"""Architectural Pathfinding and Adjacency Validation Module."""

from typing import List, Dict, Set
from models.floor_plan import RoomSpec
from .bsp import BSPNode

class AdjacencyGraph:
    """Monta o grafo de conexões físicas entre cômodos e valida regras de arquitetura."""
    
    # Espaço mínimo (m) para considerar uma conexão de parede passível de uma porta
    DOOR_MIN_SPACE = 0.8  

    def __init__(self, nodes: List[BSPNode]):
        # 1. Converte os nós soltos do BSPTree para instancias sólidas de `RoomSpec` (models)
        self.rooms: Dict[str, RoomSpec] = {}
        for node in nodes:
            name = node.room_type
            self.rooms[name] = RoomSpec(
                room_type=name,
                x=node.x,
                y=node.y,
                width=node.width,
                length=node.length,
                exterior_walls=frozenset(node.exterior_walls)
            )
            
        # 2. Grafo de adjacência (ex: { 'living': {'bedroom_1', 'kitchen'} })
        self.edges: Dict[str, Set[str]] = {name: set() for name in self.rooms}
        self._build_edges()
        
    def _build_edges(self):
        """Detecção geométrica AABB de intersecções exatas de borda/parede para achar portas."""
        room_names = list(self.rooms.keys())
        
        for i in range(len(room_names)):
            for j in range(i + 1, len(room_names)):
                r1 = self.rooms[room_names[i]]
                r2 = self.rooms[room_names[j]]
                
                # --- Checa Eixo X (Paredes Leste e Oeste se tocando) ---
                if abs((r1.x + r1.width) - r2.x) < 0.05 or abs((r2.x + r2.width) - r1.x) < 0.05:
                    # Há contato no Eixo X! Agora avaliamos se no eixo Y o overlap abriga uma porta (0.8m)
                    overlap_y = min(r1.y + r1.length, r2.y + r2.length) - max(r1.y, r2.y)
                    if overlap_y >= self.DOOR_MIN_SPACE:
                        self.edges[r1.room_type].add(r2.room_type)
                        self.edges[r2.room_type].add(r1.room_type)
                        
                # --- Checa Eixo Y (Paredes Norte e Sul se tocando) ---
                if abs((r1.y + r1.length) - r2.y) < 0.05 or abs((r2.y + r2.length) - r1.y) < 0.05:
                    # Há contato no Eixo Y! Agora avaliamos se no eixo X o overlap abriga uma porta
                    overlap_x = min(r1.x + r1.width, r2.x + r2.width) - max(r1.x, r2.x)
                    if overlap_x >= self.DOOR_MIN_SPACE:
                        self.edges[r1.room_type].add(r2.room_type)
                        self.edges[r2.room_type].add(r1.room_type)

    def validate_architecture(self) -> bool:
        """
        Garante que a configuração topológica final seja aceitável para habitação.
        Retorna True se for um layout válido e que respeite fluxos básicos.
        """
        
        # Regra 1: Áreas Integradas
        # Todas as salas devem ser parte de um único sistema (Nenhuma sala nasce presa, cercada)
        if not self._is_connected():
            return False

        # Regra 2: O Paradoxo do Banheiro Zumbi (Resolvendo sua requisição do plano)
        # O banheiro íntimo NUNCA deve ser obrigado a acessar a casa exclusivamente através da lavanderia ou cozinha.
        for room, adjacencies in self.edges.items():
            if room.startswith("bathroom"):
                allowed_hubs = {"living", "corridor"} | {k for k in self.edges if k.startswith("bedroom")}
                
                # Se o banheiro possuir área social adjacente, passou na prova da "zona".
                # Se nenhuma face dele toca zona social/íntima, ele falha (sendo banheiro zumbi) e a planta reseta.
                if not any(hub in adjacencies for hub in allowed_hubs):
                    return False
                    
        return True

    def _is_connected(self) -> bool:
        """Checa se o trajeto pelas portas acessa todos os cômodos (Árvore Conexa)."""
        if not self.rooms: return True
        start = list(self.rooms.keys())[0]
        visited = set()
        queue = [start]
        while queue:
            curr = queue.pop(0)
            if curr not in visited:
                visited.add(curr)
                queue.extend(self.edges[curr] - visited)
        # Se visitamos a quantia de cômodos que existem, quer dizer que todos se conectam!
        return len(visited) == len(self.rooms)
