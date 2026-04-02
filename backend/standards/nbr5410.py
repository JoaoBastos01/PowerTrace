"""Padrões elétricos conforme ABNT NBR 5410:2004."""
from dataclasses import dataclass


@dataclass(frozen=True)
class WireSpec:
    """Uma entrada da Tabela 38 da NBR 5410.

    Refere-se a cabos de cobre com isolação PVC (70°C),
    instalados em eletroduto (método B), temperatura ambiente 30°C.
    """
    gauge_mm2:   float  # seção transversal (mm²)
    max_current: float  # corrente máxima suportada (A)
    resistance:  float  # resistência elétrica (Ω/km)

    def __str__(self):
        return f"{self.gauge_mm2}mm² | {self.max_current}A | {self.resistance}Ω/km"


class ElectricalStandards:

    # ------------------------------------------------------------------
    # Tensões nominais (V)
    # ------------------------------------------------------------------
    PHASE_NEUTRAL = 127   # monofásico fase-neutro
    PHASE_PHASE   = 220   # bifásico fase-fase
    THREE_PHASE   = 380   # trifásico

    # ------------------------------------------------------------------
    # Limites de tensão (BT = Baixa Tensão)
    # ------------------------------------------------------------------
    AC_MAX_VOLTAGE = 1000   # acima = Alta Tensão (AT)
    DC_MAX_VOLTAGE = 1500

    # Extra Baixa Tensão (ELV) — limites de segurança anti-choque
    AC_ELV_LIMIT = 50
    DC_ELV_LIMIT = 120

    # ------------------------------------------------------------------
    # Queda de tensão máxima permitida (frações decimais)
    # ------------------------------------------------------------------
    MAX_DROP_TERMINAL = 0.04   # 4% — do ponto de entrega até a carga
    MAX_DROP_NETWORK  = 0.05   # 5% — total da rede

    # ------------------------------------------------------------------
    # Tabela 38 — bitolas de cabo de cobre / PVC / método B / 30°C
    # ------------------------------------------------------------------
    WIRE_TABLE: list[WireSpec] = [
        WireSpec(1.5,   17.5, 12.100),
        WireSpec(2.5,   24.0,  7.410),
        WireSpec(4.0,   32.0,  4.610),
        WireSpec(6.0,   41.0,  3.080),
        WireSpec(10.0,  57.0,  1.830),
        WireSpec(16.0,  76.0,  1.150),
        WireSpec(25.0, 101.0,  0.727),
        WireSpec(35.0, 125.0,  0.524),
        WireSpec(50.0, 151.0,  0.387),
    ]

    # ------------------------------------------------------------------
    # Disjuntores comerciais comuns (A)
    # ------------------------------------------------------------------
    BREAKERS: list[int] = [10, 16, 20, 25, 32, 40, 50, 63, 70, 80, 100]

    # ------------------------------------------------------------------
    # Métodos de dimensionamento
    # ------------------------------------------------------------------

    @staticmethod
    def select_breaker(design_current: float) -> int:
        """Retorna o menor disjuntor comercial que suporta a corrente dimensionada.

        Critério: In >= Ib (corrente nominal do disjuntor >= corrente de projeto).

        Levanta:
            ValueError -- se a corrente exceder o maior disjuntor da tabela.
        """
        breaker = next(
            (b for b in ElectricalStandards.BREAKERS if b >= design_current),
            None
        )
        if breaker is None:
            raise ValueError(
                f"Corrente dimensionada {design_current:.2f}A excede o maior "
                f"disjuntor disponível ({ElectricalStandards.BREAKERS[-1]}A)."
            )
        return breaker

    @staticmethod
    def select_wire(design_current: float) -> WireSpec:
        """Retorna a menor bitola de cabo que suporta a corrente dimensionada.

        Critério: Iz >= In  (capacidade do cabo >= disjuntor selecionado).

        Levanta:
            ValueError -- se a corrente exceder a tabela NBR 5410.
        """
        breaker = ElectricalStandards.select_breaker(design_current)
        for spec in ElectricalStandards.WIRE_TABLE:
            if spec.max_current >= breaker:
                return spec
        raise ValueError(
            f"Nenhuma bitola na tabela NBR 5410 suporta {design_current:.2f}A."
        )

    @staticmethod
    def calculate_gauge(load: float, voltage: float, pf: float = 1.0) -> dict:
        """Dimensiona condutor e disjuntor para uma dada carga.

        Aplica margem de segurança de 10% sobre a corrente calculada,
        conforme recomendação da NBR 5410.

        Argumentos:
            load    -- potência em Watts (W).
            voltage -- tensão de operação em Volts (V).
            pf      -- fator de potência (padrão 1.0).

        Retorna:
            Dicionário com corrente real, corrente dimensionada,
            disjuntor recomendado e especificação do cabo (WireSpec).
        """
        current        = load / (voltage * pf)
        design_current = current * 1.10
        breaker        = ElectricalStandards.select_breaker(design_current)
        wire           = ElectricalStandards.select_wire(design_current)

        return {
            "corrente":             round(current, 2),
            "corrente_dimensionada": round(design_current, 2),
            "disjuntor":            breaker,
            "cabo":                 wire,
        }