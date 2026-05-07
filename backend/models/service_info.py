from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, field_validator

ServiceType = Literal[
    "diagnostic",
    "oil_change",
    "brake_service",
    "battery",
    "tires",
    "alignment",
    "ac_service",
    "engine_repair",
    "transmission",
    "inspection",
    "other",
]

Urgency = Literal["today", "this_week", "flexible", "emergency"]
PartsPreference = Literal["standard", "oem", "budget", "not_sure"]

SERVICE_TYPE_LABELS: dict[str, str] = {
    "diagnostic": "Diagnostic inspection",
    "oil_change": "Oil change",
    "brake_service": "Brake service",
    "battery": "Battery service",
    "tires": "Tires",
    "alignment": "Wheel alignment",
    "ac_service": "A/C service",
    "engine_repair": "Engine repair",
    "transmission": "Transmission service",
    "inspection": "Pre-purchase or safety inspection",
    "other": "General repair",
}

URGENCY_LABELS: dict[str, str] = {
    "today": "Needs service today",
    "this_week": "Needs service this week",
    "flexible": "Flexible timing",
    "emergency": "Urgent or unsafe to drive",
}

PARTS_PREFERENCE_LABELS: dict[str, str] = {
    "standard": "Standard parts",
    "oem": "OEM parts",
    "budget": "Budget-friendly parts",
    "not_sure": "Not sure",
}

VALID_ADDONS = {
    "diagnostic_scan",
    "multi_point_inspection",
    "tire_rotation",
    "fluid_top_off",
    "road_test",
}

ADDON_LABELS: dict[str, str] = {
    "diagnostic_scan": "Diagnostic scan",
    "multi_point_inspection": "Multi-point inspection",
    "tire_rotation": "Tire rotation",
    "fluid_top_off": "Fluid top-off",
    "road_test": "Road test",
}


class VehicleInfo(BaseModel):
    year: int | None = None
    make: str
    model: str
    mileage: int | None = None
    vin: str | None = None
    licensePlate: str | None = None

    @field_validator("year")
    @classmethod
    def validate_year(cls, value: int | None) -> int | None:
        if value is not None and (value < 1950 or value > 2035):
            raise ValueError("Vehicle year must be between 1950 and 2035.")
        return value

    @field_validator("mileage")
    @classmethod
    def validate_mileage(cls, value: int | None) -> int | None:
        if value is not None and (value < 0 or value > 1_000_000):
            raise ValueError("Mileage must be between 0 and 1,000,000.")
        return value


class ServiceInfo(BaseModel):
    serviceType: ServiceType
    issueDescription: str
    urgency: Urgency = "flexible"
    partsPreference: PartsPreference = "not_sure"
    addons: list[str] | None = None
    notes: str | None = None
    customerCanDropOff: bool | None = None

    @field_validator("addons")
    @classmethod
    def validate_addons(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return value
        invalid = [addon for addon in value if addon not in VALID_ADDONS]
        if invalid:
            raise ValueError(f"Unknown add-ons: {invalid}. Valid options: {sorted(VALID_ADDONS)}")
        return value
