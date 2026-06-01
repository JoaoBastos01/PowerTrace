"""Access-graph policy for functional door placement."""

from typing import Dict, Iterable, Set, Tuple

from core.generation.room_roles import resolve_room_presentation

AccessEdges = Dict[str, Set[str]]
Edge = Tuple[str, str]

PROHIBITED_COST = 10_000


def sorted_edge(first: str, second: str) -> Edge:
    return tuple(sorted((first, second)))


def room_access_role(room_type: str, category: str | None = None) -> str:
    if category:
        role = resolve_room_presentation(room_type, category).room_role
        if role in {"social_full_bathroom", "powder_room"}:
            return "social_bathroom"
        if role == "full_bathroom":
            return "full_bathroom"
        if role == "living_area" or role == "living_kitchen":
            return "social_hub"
        if role == "circulation":
            return "corridor"
        return role

    if room_type == "bathroom_social":
        return "social_bathroom"
    if room_type.startswith("bathroom"):
        return "full_bathroom"
    if room_type.startswith("living"):
        return "social_hub"
    if room_type.startswith("corridor"):
        return "corridor"
    if room_type.startswith("bedroom"):
        return "bedroom"
    return room_type


def connection_cost(first: str, second: str, category: str | None = None) -> int:
    roles = frozenset([
        room_access_role(first, category),
        room_access_role(second, category),
    ])
    costs = {
        frozenset(["corridor", "bedroom"]): 1,
        frozenset(["corridor", "full_bathroom"]): 1,
        frozenset(["corridor", "social_bathroom"]): 1,
        frozenset(["corridor", "social_hub"]): 1,
        frozenset(["social_hub", "kitchen"]): 1,
        frozenset(["social_hub", "social_bathroom"]): 1,
        frozenset(["living_kitchen", "bedroom"]): 1,
        frozenset(["living_kitchen", "full_bathroom"]): 1,
        frozenset(["living_kitchen", "social_bathroom"]): 1,
        frozenset(["bedroom", "full_bathroom"]): 2,
        frozenset(["social_hub", "bedroom"]): 5,
        frozenset(["kitchen", "corridor"]): 10,
        frozenset(["social_hub", "full_bathroom"]): 20,
        frozenset(["kitchen", "bedroom"]): 50,
        frozenset(["bedroom", "bedroom"]): 50,
        frozenset(["kitchen", "full_bathroom"]): 100,
        frozenset(["full_bathroom", "full_bathroom"]): 100,
        frozenset(["bedroom", "social_bathroom"]): PROHIBITED_COST,
        frozenset(["social_bathroom", "full_bathroom"]): PROHIBITED_COST,
        frozenset(["garage", "social_hub"]): 1,
        frozenset(["garage", "kitchen"]): 5,
        frozenset(["garage", "corridor"]): 10,
        frozenset(["garage", "bedroom"]): PROHIBITED_COST,
        frozenset(["garage", "full_bathroom"]): PROHIBITED_COST,
        frozenset(["garage", "social_bathroom"]): PROHIBITED_COST,
    }
    return costs.get(roles, PROHIBITED_COST)


def build_access_edges(
    physical_edges: AccessEdges,
    topology_edges: Iterable[Edge] | None = None,
    category: str | None = None,
) -> AccessEdges:
    access_edges: AccessEdges = {room: set() for room in physical_edges}
    preferred_edges = set(topology_edges or [])

    for first, second in sorted(preferred_edges):
        if second in physical_edges.get(first, set()):
            _add_edge(access_edges, first, second)

    if _is_connected(access_edges):
        return access_edges

    fallback_edges = []
    for first, neighbors in physical_edges.items():
        for second in neighbors:
            if first >= second:
                continue
            cost = connection_cost(first, second, category)
            if cost >= PROHIBITED_COST:
                continue
            fallback_edges.append((cost, first, second))

    for _, first, second in sorted(fallback_edges):
        _add_edge(access_edges, first, second)
        if _is_connected(access_edges):
            break

    return access_edges


def _add_edge(edges: AccessEdges, first: str, second: str) -> None:
    edges.setdefault(first, set()).add(second)
    edges.setdefault(second, set()).add(first)


def _is_connected(edges: AccessEdges) -> bool:
    if not edges:
        return True
    start = min(edges)
    visited = set()
    queue = [start]
    while queue:
        current = queue.pop(0)
        if current in visited:
            continue
        visited.add(current)
        queue.extend(edges[current] - visited)
    return len(visited) == len(edges)
