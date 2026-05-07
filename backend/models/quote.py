from __future__ import annotations

from pydantic import BaseModel


class LineItem(BaseModel):
    description: str
    amount: float


class Quote(BaseModel):
    currency: str = "USD"
    total: float
    lineItems: list[LineItem]
    disclaimer: str = (
        "Estimate only. Final price depends on inspection, parts availability, "
        "vehicle condition, taxes, and shop supplies."
    )


class TimeSlot(BaseModel):
    startISO: str
    endISO: str
    timezone: str


class PreferredWindow(BaseModel):
    startISO: str
    endISO: str
    timezone: str
