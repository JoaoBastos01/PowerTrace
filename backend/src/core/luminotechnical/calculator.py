from dataclasses import dataclass
from typing import Literal

# Iluminâncias requeridas por ambiente — NBR 5413 Tabela 1
ILUMINANCIA_NBR = {
    "kitchen":    500,   # lux
    "bedroom":    150,
    "living":     300,
    "bathroom":   200,
    "corridor":   100,
    "garage":     75,
}

# Fator de utilização médio por tipo de ambiente (simplificado para TCC)
FATOR_UTILIZACAO = {
    "kitchen": 0.60,
    "bedroom": 0.55,
    "living":  0.60,
    "bathroom":0.50,
    "corridor":0.55,
    "garage":  0.50,
}

FATOR_MANUTENCAO = 0.80   # NBR 5413: ambientes limpos de uso residencial

@dataclass
class ResultadoLuminotecnico:
    iluminancia_requerida: float   # lux
    fluxo_luminoso_total: float    # lúmens necessários
    num_luminárias: int
    fluxo_por_luminaria: float     # lúmens de cada luminária
    potencia_total_w: float

def lightning_calculator(
    room_type: str,
    area: float,                   # m²
    fluxo_luminaria: float = 800,  # lúmens — padrão lâmpada LED 9W
    potencia_luminaria: float = 9, # watts
) -> ResultadoLuminotecnico:
    """Método dos Lumens — NBR 5413."""
    E  = ILUMINANCIA_NBR.get(room_type, 300)
    η  = FATOR_UTILIZACAO.get(room_type, 0.55)
    fc = FATOR_MANUTENCAO

    # N = (E × A) / (ф × η × fc)
    fluxo_total = (E * area) / (η * fc)
    num = max(1, -(-int(fluxo_total) // int(fluxo_luminaria)))  # ceiling

    return ResultadoLuminotecnico(
        iluminancia_requerida=E,
        fluxo_luminoso_total=fluxo_total,
        num_luminárias=num,
        fluxo_por_luminaria=fluxo_luminaria,
        potencia_total_w=num * potencia_luminaria,
    )