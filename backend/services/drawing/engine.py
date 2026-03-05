import ezdxf
from backend.models.base import BaseRoom


class DXFGenerator:
    def __init__(self):
        self.doc = ezdxf.new(setup=True)
        self.msp = self.doc.modelspace()
        self._setup_layers()

    def _setup_layers(self):
        self.doc.layers.add(name="PT_WALLS", color=7)
        self.doc.layers.add(name="PT_TEXT", color=2)

    def draw_room(self, room: BaseRoom, wall_thickness=0.15):
        x, y = room.origin
        w, l = room.width, room.length
        t = wall_thickness

        outer_points = [
        (x, y),           # Bottom-left
        (x + w, y),       # Bottom-right
        (x + w, y + l),   # Top-right
        (x, y + l),       # Top-left
        (x, y)            # Close the loop
        ]
        self.msp.add_lwpolyline(outer_points, dxfattribs={'layer': 'PT_WALLS_OUTER', 'color': 7})
        
        inner_points = [
        (x + t, y + t),           # Bottom-left offset
        (x + w - t, y + t),       # Bottom-right offset
        (x + w - t, y + l - t),   # Top-right offset
        (x + t, y + l - t),       # Top-left offset
        (x + t, y + t)            # Close the loop
        ]
        self.msp.add_lwpolyline(inner_points, dxfattribs={'layer': 'PT_WALLS_INNER', 'color': 8})
        
        label_pos = (x + w / 2, y + l / 2)
        self.msp.add_text(
            f"{room.name}\n{room.get_total_wattage()}W", dxfattribs={"height": 0.2, "layer": "PT_TEXT"}
        ).set_placement(label_pos)
        
    def draw_door(self, x, y, width=0.8):
        self.msp.add_line((x, y), (x, y + width), dxfattribs={"color": 1})
        self.msp.add_arc((x, y), radius=width, start_angle=0, end_angle=90, dxfattribs={"color": 1})

    def draw_window(self, x, y, width=1.2):
        self.msp.add_line((x, y), (x + width, y), dxfattribs={"color": 4})
        self.msp.add_line((x, y + 0.15), (x + width, y + 0.15), dxfattribs={"color": 4})

    def draw_appliances(self, room: BaseRoom):
        x, y = room.origin
        spacing = room.width / (len(room.appliances) + 1)

        for i, app in enumerate(room.appliances):
            pos_x = x + (spacing * (i + 1))
            pos_y = y + 0.2

            self.msp.add_circle(
                (pos_x, pos_y), radius=0.05, dxfattribs={"layer": "PT_SYMBOLS"}
            )

            self.msp.add_text(
                f"{app.wattage}W", dxfattribs={"height": 0.1}
            ).set_placement((pos_x, pos_y + 0.1))

    def save(self, filename="output.dxf"):
        self.doc.saveas(filename)
        print(f"DXF file saved as {filename}")
