"""Sistema de seed hierárquico para geração determinística de plantas."""

import hashlib
import random
from dataclasses import dataclass


def make_rng(master_seed: int, *namespace: str) -> random.Random:
    """Cria um RNG determinístico e isolado para um sub-processo específico."""
    key = f"{master_seed}:{'|'.join(namespace)}".encode("utf-8")
    digest = hashlib.sha256(key).digest()
    sub_seed = int.from_bytes(digest[:8], "big")
    return random.Random(sub_seed)


@dataclass(frozen=True)
class SeedContext:
    """Contexto de seed que todos os geradores do pipeline recebem."""

    master_seed: int

    def rng(self, *namespace: str) -> random.Random:
        """Retorna um RNG isolado para o namespace fornecido."""
        return make_rng(self.master_seed, *namespace)
