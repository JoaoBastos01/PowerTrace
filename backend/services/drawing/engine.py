"""DXFGenerator — orquestrador da drawing engine do PowerTrace.

Esta classe é o único ponto de entrada público. Ela instancia o documento
ezdxf, configura as layers e delega cada operação de desenho ao módulo
especializado correspondente.
"""
import ezdxf
from typing import List

from models.base import BaseRoom

from .layers    import setup_layers
from .openings  import Opening
from .walls     import draw_room_structure
from .lighting  import draw_lighting
from .appliances import draw_appliances


class DXFGenerator:
    """Gerador de arquivos DXF para plantas baixas elétricas (NBR 5410)."""

    def __init__(self):
        self.doc = ezdxf.new(setup=True)
        self.msp = self.doc.modelspace()
        setup_layers(self.doc)

    # ------------------------------------------------------------------
    # API pública — delega para os módulos especializados
    # ------------------------------------------------------------------

    def draw_room_structure(self, room: BaseRoom,
                            wall_thickness: float = 0.15,
                            openings: List[Opening] = None) -> None:
        """Desenha as paredes do cômodo com suporte a aberturas."""
        draw_room_structure(self.msp, room, wall_thickness, openings)

    def draw_lighting(self, room: BaseRoom) -> None:
        """Distribui os pontos de iluminação em grade uniforme no cômodo."""
        draw_lighting(self.msp, room)

    def draw_appliances(self, room: BaseRoom,
                        wall_thickness: float = 0.15) -> None:
        """Distribui os pontos de TUG ao longo do perímetro do cômodo."""
        draw_appliances(self.msp, room, wall_thickness)

    # ------------------------------------------------------------------
    # Persistência
    # ------------------------------------------------------------------

    def save(self, filename: str = "output.dxf") -> None:
        """Salva o documento DXF no caminho especificado."""
        self.doc.saveas(filename)
        print(f"Arquivo DXF salvo como '{filename}'")
