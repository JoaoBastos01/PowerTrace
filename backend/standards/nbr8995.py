from dataclasses import dataclass

# Required illuminance by room type — NBR 8995-1 Table 1
REQUIRED_ILLUMINANCE = {
    "kitchen": 300, 
    "bedroom": 150,
    "living": 200,
    "bathroom": 200,
    "corridor": 100,
    "garage": 75,
}

# Utilization factor table η(K) — NBR 8995-1 Table 3
# (direct LED panel, light ceiling and walls — typical residential)
_ETA_TABLE = [
    (0.75, 0.45),
    (1.00, 0.50),
    (1.25, 0.55),
    (1.50, 0.58),
    (2.00, 0.62),
    (2.50, 0.65),
    (3.00, 0.68),
    (float("inf"), 0.70),
]

MAINTENANCE_FACTOR = 0.80  # NBR 8995-1: clean residential environments

CEILING_HEIGHT = 2.70  # meters - standard ceiling height

WORK_PLANE_HEIGHT = 0.80  # meters - work plane height


def room_index(width: float, length: float) -> float:
    """Room Index (K) — NBR 8995-1 Eq. 1.

    K = (W × L) / (Hm × (W + L))
    Hm = mounting height above work plane.
    """
    hm = CEILING_HEIGHT - WORK_PLANE_HEIGHT
    return (width * length) / (hm * (width + length))


def utilization_factor(k: float) -> float:
    """Return η by stepping through the normative K table."""
    for k_max, eta in _ETA_TABLE:
        if k <= k_max:
            return eta
    return 0.70


@dataclass
class LightingResult:
    required_illuminance: float  # lux (lx)
    total_flux: float            # necessary flux in lumens (lm)
    fixture_count: int           # number of fixtures
    flux_by_fixture: float       # fixtures flux in lumens (lm)
    total_power_w: float         # total power in watts (W)
    room_index_k: float          # K — geometric room index
    eta: float                   # utilization factor used


def lighting_calculator(
    room_type: str,              # room type
    area: float,                 # m²
    width: float,                # room width (m)
    length: float,               # room length (m)
    fixture_flux: float = 1800,  # LED panel 18W, residential standard (lm)
    fixture_power: float = 18,   # individual fixture power (W)
) -> LightingResult:
    """Lumens method — NBR 8995-1."""
    E = REQUIRED_ILLUMINANCE.get(room_type, 300)
    k = room_index(width, length)
    eta = utilization_factor(k)
    fc = MAINTENANCE_FACTOR

    # N = (E × A) / (Φ × η × fc)
    # E = required illuminance | A = area | Φ = luminaire flux | η = utilization factor | fc = maintenance factor
    total_flux = (E * area) / (eta * fc)
    num = max(1, -(-int(total_flux) // int(fixture_flux)))  # ceiling

    return LightingResult(
        required_illuminance=E,
        room_index_k=round(k, 3),
        eta=eta,
        total_flux=total_flux,
        fixture_count=num,
        flux_by_fixture=fixture_flux,
        total_power_w=num * fixture_power,
    )
