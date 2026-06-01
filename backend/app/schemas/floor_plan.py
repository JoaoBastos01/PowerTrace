"""Schemas Pydantic de request/response para a API do PowerTrace."""

from typing import List
from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    """Parâmetros de entrada para geração de planta baixa."""

    seed: int = Field(default=42, description="Seed para geração procedural determinística.")
    width: float = Field(default=8.0, gt=0, description="Largura da casa em metros.")
    length: float = Field(default=12.0, gt=0, description="Comprimento da casa em metros.")


class RoomResponse(BaseModel):
    """Dados de um cômodo gerado."""

    room_type: str
    room_role: str
    name: str
    x: float
    y: float
    width: float
    length: float
    area: float
    total_wattage: int
    exterior_walls: List[str]


class FloorPlanResponse(BaseModel):
    """Resposta completa da geração de planta baixa."""

    seed: int
    category: str
    total_width: float
    total_length: float
    total_area: float
    rooms: List[RoomResponse]
    dxf_filename: str
