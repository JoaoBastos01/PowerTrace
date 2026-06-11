"""Rules for applying default and custom TUE overrides."""

from dataclasses import dataclass

from .appliances import Appliance, ApplianceSource, ApplianceType
from .base import BaseRoom


class TUEOverrideError(ValueError):
    """Raised when a TUE override violates domain rules."""


@dataclass(frozen=True)
class TUEOverride:
    key: str
    name: str | None
    quantity: int
    power_w: int | None
    voltage: int
    power_factor: float
    enabled: bool
    source: ApplianceSource


def _apply_default_override(
    room: BaseRoom,
    override: TUEOverride,
    default_tues: dict[str, Appliance],
) -> None:
    """Keep or remove one default TUE from a room."""
    if override.key not in default_tues:
        raise TUEOverrideError(
            f"Unknown default TUE '{override.key}' for room '{room.name}'."
        )

    if override.enabled:
        return

    room.appliances = [
        appliance
        for appliance in room.appliances
        if appliance.key != override.key
    ]


def _apply_custom_override(
    room: BaseRoom,
    override: TUEOverride,
    existing_keys: set[str],
) -> None:
    """Add enabled custom TUEs to a room."""
    if not override.enabled:
        return

    if override.name is None:
        raise TUEOverrideError(
            f"Custom TUE '{override.key}' requires a name."
        )

    if override.power_w is None:
        raise TUEOverrideError(
            f"Custom TUE '{override.key}' requires power_w."
        )

    for index in range(override.quantity):
        instance_key = (
            override.key
            if override.quantity == 1
            else f"{override.key}_{index + 1}"
        )

        if instance_key in existing_keys:
            raise TUEOverrideError(
                f"Duplicate TUE key '{instance_key}'."
            )

        room.add_appliance(
            Appliance(
                key=instance_key,
                name=override.name,
                wattage=override.power_w,
                type=ApplianceType.DEDICATED,
                voltage=override.voltage,
                pf=override.power_factor,
                source=ApplianceSource.CUSTOM,
            )
        )
        existing_keys.add(instance_key)


def apply_tue_overrides(
    room: BaseRoom,
    overrides: list[TUEOverride],
) -> None:
    """Apply TUE commands without changing lighting or general outlets."""
    default_tues = {
        appliance.key: appliance
        for appliance in room.appliances
        if appliance.type == ApplianceType.DEDICATED
        and appliance.source == ApplianceSource.DEFAULT
        and appliance.key is not None
    }

    existing_keys = {
        appliance.key
        for appliance in room.appliances
        if appliance.key is not None
    }

    for override in overrides:
        if override.source == ApplianceSource.DEFAULT:
            _apply_default_override(room, override, default_tues)
            continue

        _apply_custom_override(room, override, existing_keys)
