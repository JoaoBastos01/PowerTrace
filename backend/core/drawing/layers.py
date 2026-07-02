"""Configuração das layers DXF do PowerTrace."""


def setup_layers(doc) -> None:
    """Cria as layers padrão PT_* no documento DXF.

    Paleta de cores conforme índice AutoCAD (ACI):
        1 = Vermelho   2 = Amarelo   3 = Verde
        4 = Ciano      7 = Branco    8 = Cinza
    """
    doc.layers.add(name="PT_WALLS_OUTER", color=7)  # Branco/Preto
    doc.layers.add(name="PT_WALLS_INNER", color=8)  # Cinza
    doc.layers.add(name="PT_DOORS",       color=1)  # Vermelho
    doc.layers.add(name="PT_WINDOWS",     color=4)  # Ciano
    doc.layers.add(name="PT_LIGHTING",    color=2)  # Amarelo
    doc.layers.add(name="PT_TEXT",        color=7)  # Branco
    doc.layers.add(name="PT_SYMBOLS",     color=3)  # Verde
