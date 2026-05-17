"""Teste de stress: valida o gerador Topology-First com múltiplos seeds e áreas."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.generation.generator import FloorPlanGenerator


def stress_test():
    configs = [
        ("Kitnet 30m2",  5.0,  6.0),
        ("Small 45m2",   5.0,  9.0),
        ("Small 55m2",   5.5, 10.0),
        ("Medium 72m2",  8.0,  9.0),
        ("Medium 80m2",  8.0, 10.0),
        ("Medium 96m2",  8.0, 12.0),
        ("Large 120m2", 10.0, 12.0),
        ("Large 150m2", 10.0, 15.0),
    ]

    total_tests = 0
    total_ok = 0
    total_fail = 0
    failures = []

    SEEDS_PER_CONFIG = 50
    MAX_ATTEMPTS = 100

    for label, w, l in configs:
        ok = 0
        fail = 0
        for seed in range(SEEDS_PER_CONFIG):
            total_tests += 1
            try:
                gen = FloorPlanGenerator(master_seed=seed, width=w, length=l)
                plan, graph, program = gen.generate(max_attempts=MAX_ATTEMPTS)

                # Validacao 1: Todo comodo deve ter pelo menos 1 adjacencia
                for room_name in program.rooms:
                    if room_name not in graph.edges or len(graph.edges[room_name]) == 0:
                        raise AssertionError(f"{room_name} sem adjacencia no grafo")

                # Validacao 2: Nenhum par de banheiros adjacentes
                for room_name, adjs in graph.edges.items():
                    if room_name.startswith("bathroom"):
                        for adj in adjs:
                            if adj.startswith("bathroom"):
                                raise Exception(f"Banheiros adjacentes: {room_name} <-> {adj}")

                # Validacao 3: Grafo conexo (BFS)
                visited = set()
                queue = [list(program.rooms.keys())[0]]
                while queue:
                    curr = queue.pop(0)
                    if curr not in visited:
                        visited.add(curr)
                        queue.extend(graph.edges.get(curr, set()) - visited)
                if len(visited) != len(program.rooms):
                    raise Exception(f"Grafo desconexo: visitados={len(visited)}, total={len(program.rooms)}")

                ok += 1
                total_ok += 1

            except Exception as e:
                fail += 1
                total_fail += 1
                failures.append(f"  [{label}] seed={seed}: {e}")

        print(f"  {label:15s} | {ok}/{SEEDS_PER_CONFIG} OK | {fail} falhas")

    print(f"\n{'='*50}")
    print(f"TOTAL: {total_ok}/{total_tests} OK ({total_fail} falhas)")

    if failures:
        print(f"\nFalhas detalhadas (primeiras 10):")
        for f in failures[:10]:
            print(f)

    return total_fail == 0

if __name__ == "__main__":
    print("Stress Test - Topology-First Generator")
    print("=" * 50)
    success = stress_test()
    print(f"\nResultado: {'PASSOU' if success else 'FALHOU'}")
