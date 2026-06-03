"""Configuração centralizada do backend PowerTrace."""

import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Settings:
    """Configurações da aplicação lidas de variáveis de ambiente ou defaults."""

    # Voltagem padrão das instalações residenciais (monofásico fase-neutro)
    default_voltage: int = int(os.getenv("DEFAULT_VOLTAGE", "127"))

    # Diretório onde os arquivos DXF/JSON gerados são salvos
    output_dir: str = os.getenv("OUTPUT_DIR", "output")

    # Banco de dados
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///powertrace.db")
    
    # Autenticação simples
    app_username: str = os.getenv("APP_USERNAME", "admin")
    app_password: str = os.getenv("APP_PASSWORD", "password")
    secret_key: str = os.getenv("SECRET_KEY", "123456789abcdef")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "120"))
    
    # Nível de logging (DEBUG, INFO, WARNING, ERROR)
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    # Número máximo de tentativas de geração de planta
    max_generation_attempts: int = int(os.getenv("MAX_GENERATION_ATTEMPTS", "3000"))


settings = Settings()
