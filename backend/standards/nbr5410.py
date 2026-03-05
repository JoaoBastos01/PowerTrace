
class ElectricalStandards:
    
    # Tensões nominais para sistemas monofásicos, bifásicos e trifásicos, em volts
    PHASE_NEUTRAL = 127
    PHASE_PHASE = 220
    THREE_PHASE = 380
    
    # Limites de Baixa Tensão (BT), Acima disso é considerado Alta Tensão (AT) para fins de instalação
    AC_MAX_VOLTAGE = 1000
    DC_MAX_VOLTAGE = 1500

    # Extra Baixa Tensão (ELV - Extra Low Voltage), Limites de segurança para evitar choque elétrico fatal
    AC_ELV_LIMIT = 50
    DC_ELV_LIMIT = 120

    # Queda de Tensão Máxima Permitida (Voltage Drop), Representados como decimais para facilitar cálculos (4% e 5%, respectivamente)
    MAX_DROP_TERMINAL = 0.04
    MAX_DROP_NETWORK = 0.05
    
    # Simplificação da tabela 38 da ABNT NBR 5410, que define a corrente máxima para cada seção transversal de cabo de cobre com isolação em PVC, considerando temperatura de referência do ambiente de 30°C(ar)    ), e de temperatura de 70°C no condutor 
    WIRE_GAUGE_TABLE = [
        (1.5, 17.5,  12.1),
        (2.5, 24,    7.41),
        (4.0, 32,    4.61),
        (6.0, 41,    3.08),
        (10.0, 57,   1.83),
        (16.0, 76,   1.15),
        (25.0, 101, 0.727),
        (35.0, 125, 0.524),
        (50.0, 151, 0.387)
    ]
    
    # Lista de Disjuntores Comerciais comuns (Amperes)
    COMERCIAL_CIRCUIT_BREAKERS = [10, 16, 20, 25, 32, 40, 50, 63, 70, 80, 100]
    
    
    # Função para calcular a bitola do cabo com base na carga, tensão e fator de potência
    @staticmethod
    def calculate_gauge(load, voltage, pf=1.0):
        """Calcula a bitola mínima do condutor e o disjuntor adequado
        para uma dada carga elétrica, conforme NBR 5410:2004 Tabela 38.

        Calcula a corrente com base na carga, tensão e fator de potência,
        aplica uma margem de segurança de 10% e seleciona o disjuntor e a
        bitola do cabo de acordo com as tabelas da NBR 5410.
        
        Considera instalação em eletroduto (método B), temperatura
        ambiente de 30°C e condutor de cobre com isolação PVC (70°C).

        Argumentos:
            load -- a carga de potência em Watts (W).
            voltage -- a tensão de operação em Volts (V).
            pf -- o fator de potência (padrão 1.0).

        Retorna:
            Um dicionário contendo a corrente real, corrente dimensionada,
            bitola do fio, capacidade máxima, resistência por km e o disjuntor recomendado.

        Levanta:
            ValueError -- se a carga exceder os limites da NBR 5410.
        """
        # Cálculo da corrente, em amperes
        # I = P / (V * PF)
        current = load / (voltage * pf)
        
        # Margem de 10% para segurança e futuras expansões, conforme recomendado pela norma
        design_current = current * 1.10
        
        # Encontra o disjuntor adequado (In >= Ib)
        breaker = next((b for b in ElectricalStandards.COMERCIAL_CIRCUIT_BREAKERS if b >= design_current), ElectricalStandards.COMERCIAL_CIRCUIT_BREAKERS[-1])
            
        for gauge, max_amp, res in ElectricalStandards.WIRE_GAUGE_TABLE:
            if max_amp >= breaker: # Iz >= In
                return {
                    "corrente": f"{current:.2f}A",
                    "corrente dimensionada": f"{design_current:.2f}A",
                    "bitola": f"{gauge}mm²",
                    "corrente máxima": f"{max_amp}A",
                    "resistência por km": f"{res}Ω/km",
                    "disjuntor recomendado": f"{breaker}A"
                }
        raise ValueError(f"A carga de {load}W excede a capacidade máxima da tabela da NBR 5410")