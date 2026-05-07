from __future__ import annotations

import re

from pydantic import BaseModel, field_validator


class Lead(BaseModel):
    fullName: str
    phone: str
    smsConsent: bool = True

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        digits = re.sub(r"\D", "", value)
        if len(digits) < 10:
            raise ValueError("Phone number must have at least 10 digits.")
        return value.strip()
