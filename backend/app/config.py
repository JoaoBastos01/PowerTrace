"""Configuração centralizada do backend PowerTrace."""

import os
from dataclasses import dataclass, field


@dataclass
class Settings:
    """Configurações da aplicação lidas de variáveis de ambiente ou defaults."""

    # Voltagem padrão das instalações residenciais (monofásico fase-neutro)
    default_voltage: int = int(os.getenv("DEFAULT_VOLTAGE", "127"))

    # Diretório onde os arquivos DXF gerados são salvos
    output_dir: str = os.getenv("OUTPUT_DIR", "output")

    # Nível de logging (DEBUG, INFO, WARNING, ERROR)
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    # Número máximo de tentativas de geração de planta
    max_generation_attempts: int = int(os.getenv("MAX_GENERATION_ATTEMPTS", "50"))


settings = Settings()
