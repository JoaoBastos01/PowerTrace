"""Sistema de seed hierárquico para geração determinística de plantas.

Todos os sub-processos do pipeline (seleção de cômodos, BSP, aberturas, etc.)
devem obter seu RNG exclusivamente via `SeedContext.rng(*namespace)`, nunca
instanciando `random.Random` diretamente.

Design:
    - O mesmo `master_seed` sempre produz os mesmos sub-seeds.
    - Sub-processos diferentes (namespaces diferentes) são completamente
      independentes entre si, mesmo que compartilhem o `master_seed`.
    - Retries do BSP (attempt_0, attempt_1, ...) não afetam o RNG das
      aberturas, garantindo isolamento total entre as etapas.
"""

import hashlib
import random
from dataclasses import dataclass


def make_rng(master_seed: int, *namespace: str) -> random.Random:
    """Cria um RNG determinístico e isolado para um sub-processo específico.

    O sub-seed é derivado via SHA-256 do master_seed combinado com o namespace,
    eliminando colisões entre seeds diferentes e entre tentativas de retry.

    Exemplos:
        make_rng(42, "layout", "attempt_0")  # BSP tentativa 0
        make_rng(42, "layout", "attempt_1")  # BSP tentativa 1 (independente)
        make_rng(42, "openings")             # OpeningPlacer (independente do BSP)
        make_rng(42, "room_selection")       # seleção de cômodos

    Parâmetros:
        master_seed -- Seed principal fornecido pelo usuário.
        *namespace  -- Identificadores do sub-processo (ex: "layout", "attempt_0").

    Retorna:
        Instância de random.Random inicializada de forma determinística.
    """
    key = f"{master_seed}:{'|'.join(namespace)}".encode("utf-8")
    digest = hashlib.sha256(key).digest()
    sub_seed = int.from_bytes(digest[:8], "big")
    return random.Random(sub_seed)


@dataclass(frozen=True)
class SeedContext:
    """Contexto de seed que todos os geradores do pipeline recebem.

    Em vez de passar um inteiro puro, os geradores recebem um SeedContext
    para garantir que cada sub-processo use um RNG isolado e reproduzível.

    Uso:
        ctx = SeedContext(master_seed=42)
        rng = ctx.rng("layout", "attempt_0")
        rng.random()   # sempre o mesmo valor para seed=42
    """

    master_seed: int

    def rng(self, *namespace: str) -> random.Random:
        """Retorna um RNG isolado para o namespace fornecido.

        Parâmetros:
            *namespace -- Identificadores do sub-processo.

        Retorna:
            Instância de random.Random determinística para este namespace.
        """
        return make_rng(self.master_seed, *namespace)
