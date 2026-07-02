"""DXFGenerator — orquestrador da drawing engine do PowerTrace.

Esta classe é o único ponto de entrada público. Ela instancia o documento
ezdxf, configura as layers e delega cada operação de desenho ao módulo
especializado correspondente.
"""
import os
import ezdxf
from typing import List

from core.electrical.base import BaseRoom
from app.config import settings

from .layers    import setup_layers
from .openings  import Opening
from .walls     import draw_room_structure
from .lighting  import draw_lighting
from .appliances import draw_appliances
from .legend import draw_electrical_legend


class DXFGenerator:
    """Gerador de arquivos DXF para plantas baixas elétricas (NBR 5410)."""

    def __init__(self):
        previous_fixed_metadata = ezdxf.options.write_fixed_meta_data_for_testing
        ezdxf.options.write_fixed_meta_data_for_testing = True
        try:
            self.doc = ezdxf.new(setup=True)
        finally:
            ezdxf.options.write_fixed_meta_data_for_testing = previous_fixed_metadata
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
                        wall_thickness: float = 0.15,
                        openings: List[Opening] = None) -> None:
        """Distribui os pontos de TUG ao longo do perímetro do cômodo."""
        draw_appliances(self.msp, room, wall_thickness, openings)

    def draw_legend(self, plan_width: float, plan_length: float) -> None:
        """Desenha a legenda elétrica simples fora dos limites da planta."""
        draw_electrical_legend(self.msp, plan_width, plan_length)

    # ------------------------------------------------------------------
    # Persistência
    # ------------------------------------------------------------------

    def save(self, filename: str = "output.dxf") -> str:
        """Salva o documento DXF no diretório de saída configurado.

        Retorna:
            Caminho absoluto do arquivo salvo.
        """
        os.makedirs(settings.output_dir, exist_ok=True)
        path = os.path.join(settings.output_dir, filename)
        previous_fixed_metadata = ezdxf.options.write_fixed_meta_data_for_testing
        original_dxf_types_in_use = self.doc.entitydb.dxf_types_in_use
        ezdxf.options.write_fixed_meta_data_for_testing = True
        self.doc.entitydb.dxf_types_in_use = lambda: sorted(original_dxf_types_in_use())
        try:
            self.doc.saveas(path)
        finally:
            self.doc.entitydb.dxf_types_in_use = original_dxf_types_in_use
            ezdxf.options.write_fixed_meta_data_for_testing = previous_fixed_metadata
        print(f"DXF file saved as '{path}'")
        return path
