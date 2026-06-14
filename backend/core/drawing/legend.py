"""Simple Portuguese legend for generated electrical plans."""

from .appliances import draw_outlet_symbol
from .lighting import draw_lighting_symbol


def _add_text(msp, text: str, x: float, y: float, height: float = 0.16) -> None:
    msp.add_text(
        text,
        dxfattribs={"height": height, "layer": "PT_TEXT"},
    ).set_placement((x, y))


def draw_electrical_legend(
    msp,
    plan_width: float,
    plan_length: float,
) -> None:
    """Draw the symbol legend to the right of the floor plan bounds."""
    x = plan_width + 0.8
    y = max(plan_length, 3.0)

    _add_text(msp, "LEGENDA ELÉTRICA", x, y, height=0.24)

    draw_lighting_symbol(msp, x + 0.1, y - 0.45, r=0.07)
    _add_text(msp, "Luminária", x + 0.35, y - 0.51)

    draw_outlet_symbol(msp, x + 0.1, y - 0.9, dedicated=False)
    _add_text(msp, "TUG - Tomada de uso geral", x + 0.35, y - 0.96)

    draw_outlet_symbol(msp, x + 0.1, y - 1.35, dedicated=True)
    _add_text(msp, "TUE - Tomada de uso específico", x + 0.35, y - 1.41)
