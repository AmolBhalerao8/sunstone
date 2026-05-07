"""
Estimate engine for ZOL mechanic-shop services.

These are configurable starting estimates. Keep final invoices in the shop
management system after inspection and approval.
"""
from __future__ import annotations

from models.quote import LineItem, Quote
from models.service_info import ADDON_LABELS, SERVICE_TYPE_LABELS, ServiceInfo, VehicleInfo


BASE_RATES: dict[str, float] = {
    "diagnostic": 149.00,
    "oil_change": 95.00,
    "brake_service": 425.00,
    "battery": 245.00,
    "tires": 720.00,
    "alignment": 129.00,
    "ac_service": 189.00,
    "engine_repair": 650.00,
    "transmission": 850.00,
    "inspection": 129.00,
    "other": 149.00,
}

ADDON_RATES: dict[str, float] = {
    "diagnostic_scan": 89.00,
    "multi_point_inspection": 69.00,
    "tire_rotation": 45.00,
    "fluid_top_off": 35.00,
    "road_test": 55.00,
}

PARTS_MULTIPLIERS: dict[str, float] = {
    "budget": 0.90,
    "standard": 1.00,
    "oem": 1.18,
    "not_sure": 1.00,
}

HIGH_MILEAGE_SURCHARGE = 65.00
OLDER_VEHICLE_SURCHARGE = 75.00


def calculate_quote(service: ServiceInfo, vehicle: VehicleInfo) -> Quote:
    line_items: list[LineItem] = []

    service_label = SERVICE_TYPE_LABELS[service.serviceType]
    base = BASE_RATES[service.serviceType]
    subtotal = base
    line_items.append(LineItem(description=f"{service_label} starting estimate", amount=base))

    if vehicle.mileage is not None and vehicle.mileage >= 150_000:
        subtotal += HIGH_MILEAGE_SURCHARGE
        line_items.append(
            LineItem(
                description="High-mileage inspection allowance",
                amount=HIGH_MILEAGE_SURCHARGE,
            )
        )

    if vehicle.year is not None and vehicle.year <= 2005:
        subtotal += OLDER_VEHICLE_SURCHARGE
        line_items.append(
            LineItem(
                description="Older vehicle labor allowance",
                amount=OLDER_VEHICLE_SURCHARGE,
            )
        )

    for addon in service.addons or []:
        amount = ADDON_RATES[addon]
        subtotal += amount
        line_items.append(LineItem(description=ADDON_LABELS[addon], amount=amount))

    multiplier = PARTS_MULTIPLIERS.get(service.partsPreference, 1.0)
    if multiplier != 1.0:
        adjustment = round(subtotal * (multiplier - 1.0), 2)
        subtotal += adjustment
        label = "OEM parts allowance" if adjustment > 0 else "Budget parts estimate adjustment"
        line_items.append(LineItem(description=label, amount=adjustment))

    total = round(subtotal, 2)
    return Quote(total=total, lineItems=line_items)
