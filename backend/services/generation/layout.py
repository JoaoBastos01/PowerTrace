"""Fase 2: Layout — BSP guiado pela topologia.

Posiciona cômodos no retângulo da planta usando BSP com ordem
topológica. O BSP corta LIVREMENTE (variedade procedural), mas a
ORDEM dos cômodos é definida por BFS na topologia, o que aumenta
a chance de vizinhos topológicos ficarem geometricamente adjacentes.

Se o layout resultante não satisfaz a topologia, o generator faz
retry com outro seed — a validação pós-layout garante correção.

Algoritmo:
    1. BFS na topologia a partir do living → lista ordenada
    2. BSP recursivo seguindo essa ordem (cortes livres)
    3. Validação: topologia satisfeita + anti-cluster de banheiros

Design:
    TopologyBSP(program, width, length).build(rng) -> List[BSPNode] | None
"""

import random
from collections import deque
from typing import Dict, List, Optional, Set, Tuple

from .bsp import BSPNode
from .program import HouseProgram


class TopologyBSP:
    """BSP com ordem topológica — procedural mas com viés inteligente."""

    def __init__(self, program: HouseProgram, width: float, length: float):
        self.program = program
        self.width = width
        self.length = length

    def build(self, rng: random.Random) -> Optional[List[BSPNode]]:
        """Constrói layout BSP e retorna folhas, ou None se falhar."""
        root = BSPNode(0, 0, self.width, self.length)
        ordered = self._bfs_order(rng)

        if not self._partition(root, ordered, rng):
            return None

        return self._leaves(root)

    # ──────────────────────────────────────────────────────────────
    # BFS — ordena cômodos por proximidade topológica
    # ──────────────────────────────────────────────────────────────

    def _bfs_order(self, rng: random.Random) -> List[str]:
        """BFS a partir do living, com shuffle nos vizinhos para variedade.

        A ordem BFS garante que cômodos topologicamente próximos
        ficam próximos na lista. Ao particionar o BSP seguindo
        essa lista, cômodos conectados tendem a compartilhar paredes.

        O shuffle nos vizinhos dá variedade entre tentativas.
        """
        root = self.program.root_room
        visited: Set[str] = set()
        order: List[str] = []
        queue = deque([root])

        while queue:
            room = queue.popleft()
            if room in visited:
                continue
            visited.add(room)
            order.append(room)

            neighbors = list(self.program.topology.get(room, []))
            rng.shuffle(neighbors)  # ← variedade entre tentativas
            for n in neighbors:
                if n not in visited:
                    queue.append(n)

        return order

    # ──────────────────────────────────────────────────────────────
    # Particionamento recursivo (BSP livre)
    # ──────────────────────────────────────────────────────────────

    def _partition(
        self, node: BSPNode, rooms: List[str], rng: random.Random,
    ) -> bool:
        """Divide o espaço recursivamente seguindo a ordem topológica.

        Caso base: 1 cômodo → atribui.
        Recursivo: divide a lista em dois pela área (~50%),
        faz corte BSP, recursa em cada metade.

        Os cortes são LIVRES (eixo escolhido por proporção do nó,
        com variação aleatória), dando variedade procedural.
        """
        if len(rooms) == 1:
            node.room_type = rooms[0]
            return True

        # Encontrar ponto de split pela metade da área
        left, right = self._split_by_area(rooms)

        left_area = sum(self.program.rooms[r] for r in left)
        right_area = sum(self.program.rooms[r] for r in right)
        ratio = left_area / (left_area + right_area)

        # Jitter para variedade visual (±5%)
        ratio += rng.uniform(-0.05, 0.05)
        ratio = max(0.2, min(0.8, ratio))

        # Eixo: cortar pelo lado mais comprido para manter proporção quadrada
        horizontal = node.length > node.width
        
        # Permite inverter o corte (variedade) apenas se o container for quase quadrado
        if abs(node.length - node.width) / max(node.length, node.width) < 0.2:
            if rng.random() < 0.5:
                horizontal = not horizontal

        if not node.split(ratio, horizontal, rng):
            if not node.split(ratio, not horizontal, rng):
                return False

        return (
            self._partition(node.left, left, rng)
            and self._partition(node.right, right, rng)
        )

    def _split_by_area(self, rooms: List[str]) -> Tuple[List[str], List[str]]:
        """Divide a lista em dois grupos com áreas ~iguais."""
        total = sum(self.program.rooms[r] for r in rooms)
        half = total / 2.0
        accumulated = 0.0
        idx = 1

        for i, room in enumerate(rooms):
            accumulated += self.program.rooms[room]
            if accumulated >= half and i > 0:
                idx = i
                break

        idx = max(1, min(idx, len(rooms) - 1))
        return rooms[:idx], rooms[idx:]

    def _leaves(self, node: BSPNode) -> List[BSPNode]:
        """Coleta folhas da árvore BSP."""
        if node.is_leaf():
            return [node]
        out: List[BSPNode] = []
        if node.left:
            out.extend(self._leaves(node.left))
        if node.right:
            out.extend(self._leaves(node.right))
        return out


# ──────────────────────────────────────────────────────────────────────
# Validação pós-layout
# ──────────────────────────────────────────────────────────────────────

def validate_topology(leaves: List[BSPNode], program: HouseProgram) -> bool:
    """Verifica se o layout satisfaz topologia + regras de sanidade.

    1. Navegabilidade: grafo de adjacência é conexo e válido arquiteturalmente.
    2. Banheiros NÃO adjacentes entre si (anti-cluster)
    """
    from .adjacency import AdjacencyGraph
    graph = AdjacencyGraph(leaves)
    if not graph.validate_architecture():
        import logging
        logging.getLogger(__name__).debug("Edge falhou: arquitetura inválida (desconexa ou zumbi)")
        return False

    nodes: Dict[str, BSPNode] = {l.room_type: l for l in leaves if l.room_type}

    # Check 2: anti-cluster de banheiros
    baths = [rt for rt in nodes if rt.startswith("bathroom")]
    for i in range(len(baths)):
        for j in range(i + 1, len(baths)):
            if _adjacent(nodes[baths[i]], nodes[baths[j]], 0.05):
                return False

    return True


def _adjacent(n1: BSPNode, n2: BSPNode, min_overlap: float) -> bool:
    """Dois nós compartilham parede com overlap suficiente?"""
    EPS = 0.05
    # Parede vertical (Leste/Oeste)
    if abs((n1.x + n1.width) - n2.x) < EPS or abs((n2.x + n2.width) - n1.x) < EPS:
        ov = min(n1.y + n1.length, n2.y + n2.length) - max(n1.y, n2.y)
        if ov >= min_overlap:
            return True
    # Parede horizontal (Norte/Sul)
    if abs((n1.y + n1.length) - n2.y) < EPS or abs((n2.y + n2.length) - n1.y) < EPS:
        ov = min(n1.x + n1.width, n2.x + n2.width) - max(n1.x, n2.x)
        if ov >= min_overlap:
            return True
    return False
