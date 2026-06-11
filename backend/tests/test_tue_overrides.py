import pytest

from core.electrical.appliances import ApplianceSource, ApplianceType
from core.electrical.rooms import Kitchen
from core.electrical.tue_overrides import (
    TUEOverride,
    TUEOverrideError,
    apply_tue_overrides,
)


def make_kitchen() -> Kitchen:
    kitchen = Kitchen(name="Kitchen", width=4, length=3)
    kitchen.apply_nbr5410_rules()
    return kitchen


def test_disable_default_faucet():
    kitchen = make_kitchen()

    apply_tue_overrides(
        kitchen,
        [
            TUEOverride(
                key="kitchen_electric_faucet",
                name=None,
                quantity=1,
                power_w=None,
                voltage=220,
                power_factor=1.0,
                enabled=False,
                source=ApplianceSource.DEFAULT,
            )
        ],
    )

    assert all(
        appliance.key != "kitchen_electric_faucet"
        for appliance in kitchen.appliances
    )


def test_add_custom_oven_with_custom_power():
    kitchen = make_kitchen()

    apply_tue_overrides(
        kitchen,
        [
            TUEOverride(
                key="custom_oven",
                name="Electric oven",
                quantity=1,
                power_w=3000,
                voltage=220,
                power_factor=1.0,
                enabled=True,
                source=ApplianceSource.CUSTOM,
            )
        ],
    )

    oven = next(
        appliance
        for appliance in kitchen.appliances
        if appliance.key == "custom_oven"
    )
    assert oven.wattage == 3000
    assert oven.voltage == 220
    assert oven.pf == 1.0
    assert oven.type == ApplianceType.DEDICATED
    assert oven.source == ApplianceSource.CUSTOM


def test_quantity_creates_unique_custom_tues():
    kitchen = make_kitchen()

    apply_tue_overrides(
        kitchen,
        [
            TUEOverride(
                key="custom_air_conditioner",
                name="Air conditioner",
                quantity=2,
                power_w=1500,
                voltage=220,
                power_factor=0.92,
                enabled=True,
                source=ApplianceSource.CUSTOM,
            )
        ],
    )

    keys = {appliance.key for appliance in kitchen.appliances}
    assert "custom_air_conditioner_1" in keys
    assert "custom_air_conditioner_2" in keys


def test_override_preserves_general_outlets_and_lighting():
    kitchen = make_kitchen()
    general_before = sum(
        appliance.type == ApplianceType.GENERAL
        for appliance in kitchen.appliances
    )
    lighting_before = sum(
        appliance.type == ApplianceType.LIGHTING
        for appliance in kitchen.appliances
    )

    apply_tue_overrides(kitchen, [])

    general_after = sum(
        appliance.type == ApplianceType.GENERAL
        for appliance in kitchen.appliances
    )
    lighting_after = sum(
        appliance.type == ApplianceType.LIGHTING
        for appliance in kitchen.appliances
    )
    assert general_after == general_before
    assert lighting_after == lighting_before


def test_unknown_default_tue_raises_error():
    kitchen = make_kitchen()

    with pytest.raises(TUEOverrideError, match="Unknown default TUE"):
        apply_tue_overrides(
            kitchen,
            [
                TUEOverride(
                    key="unknown_default",
                    name=None,
                    quantity=1,
                    power_w=None,
                    voltage=127,
                    power_factor=1.0,
                    enabled=False,
                    source=ApplianceSource.DEFAULT,
                )
            ],
        )
