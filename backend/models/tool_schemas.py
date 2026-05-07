"""
Pydantic schemas for Vapi tool webhook payloads.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from models.lead import Lead
from models.quote import PreferredWindow, Quote, TimeSlot
from models.service_info import ServiceInfo, VehicleInfo


class SendQuoteSmsArgs(BaseModel):
    lead: Lead
    vehicle: VehicleInfo
    service: ServiceInfo
    preferredWindow: PreferredWindow | None = None
    availableSlots: list[TimeSlot] | None = None
    bookedSlot: TimeSlot | None = None
    quote: Quote | None = None


class SendFollowupSmsArgs(BaseModel):
    lead: Lead
    messageType: str = "appointment_followup"
    customMessage: str | None = None
    bookedSlot: TimeSlot | None = None
    vehicle: VehicleInfo | None = None
    service: ServiceInfo | None = None


class VapiFunctionCall(BaseModel):
    name: str
    arguments: dict[str, Any]


class VapiToolCall(BaseModel):
    id: str
    type: str = "function"
    function: VapiFunctionCall


class VapiMessage(BaseModel):
    type: str
    toolCallList: list[VapiToolCall] | None = None
    model_config = {"extra": "allow"}


class VapiWebhookPayload(BaseModel):
    message: VapiMessage
    model_config = {"extra": "allow"}


class ToolCallResult(BaseModel):
    toolCallId: str
    result: str


class VapiToolResponse(BaseModel):
    results: list[ToolCallResult]
