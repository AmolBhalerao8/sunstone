"""
Twilio SMS service for ZOL quote and follow-up messages.
"""
from __future__ import annotations

import logging
import os
import re
from datetime import datetime

import pytz
from twilio.rest import Client

from models.lead import Lead
from models.quote import Quote, TimeSlot
from models.service_info import SERVICE_TYPE_LABELS, ServiceInfo, VehicleInfo

logger = logging.getLogger(__name__)

SHOP_NAME = os.getenv("SHOP_NAME", "ZOL")
SHOP_PHONE = os.getenv("SHOP_PHONE", "(878) 673-0209")
SHOP_ADDRESS = os.getenv("SHOP_ADDRESS", "1146 North Cedar Street, Beside Safeway")
SHOP_WEBSITE = os.getenv("SHOP_WEBSITE", "")
SHOP_HOURS = os.getenv(
    "SHOP_HOURS",
    "Calls answered 24/7. Shop appointments available daily 8:00 AM-6:00 PM.",
)
SHOP_TEAM_NOTIFY_NUMBER = os.getenv("SHOP_TEAM_NOTIFY_NUMBER", "")

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER", "")


def _digits(value: str) -> str:
    return re.sub(r"\D", "", value)


def _format_e164(value: str) -> str:
    digits = _digits(value)
    if len(digits) == 10:
        return f"+1{digits}"
    if len(digits) == 11 and digits.startswith("1"):
        return f"+{digits}"
    if value.startswith("+"):
        return value
    raise ValueError("Phone number must be a valid US phone number.")


def _fmt_slot(slot: TimeSlot) -> str:
    try:
        tz = pytz.timezone(slot.timezone)
        start = datetime.fromisoformat(slot.startISO.replace("Z", "+00:00")).astimezone(tz)
        end = datetime.fromisoformat(slot.endISO.replace("Z", "+00:00")).astimezone(tz)
        start_date = start.strftime("%a %b %d").replace(" 0", " ")
        start_time = start.strftime("%I:%M %p").lstrip("0")
        end_time = end.strftime("%I:%M %p").lstrip("0")
        return f"{start_date}, {start_time}-{end_time} {start.strftime('%Z')}"
    except Exception:
        return slot.startISO


def _vehicle_label(vehicle: VehicleInfo) -> str:
    year = f"{vehicle.year} " if vehicle.year else ""
    mileage = f", {vehicle.mileage:,} mi" if vehicle.mileage else ""
    return f"{year}{vehicle.make} {vehicle.model}{mileage}"


def build_quote_sms(
    lead: Lead,
    vehicle: VehicleInfo,
    service: ServiceInfo,
    quote: Quote,
    available_slots: list[TimeSlot] | None = None,
    booked_slot: TimeSlot | None = None,
) -> str:
    service_label = SERVICE_TYPE_LABELS[service.serviceType]
    lines = [
        f"{SHOP_NAME}: Estimate for {lead.fullName}",
        f"Vehicle: {_vehicle_label(vehicle)}",
        f"Service: {service_label}",
        f"Estimated total: ${quote.total:,.2f} {quote.currency}",
        quote.disclaimer,
    ]

    if booked_slot:
        lines.append(f"Appointment confirmed: {_fmt_slot(booked_slot)}")
    elif available_slots:
        slot_text = "; ".join(_fmt_slot(slot) for slot in available_slots[:3])
        lines.append(f"Open times: {slot_text}")

    lines.append(f"Questions? Call {SHOP_PHONE}. {SHOP_ADDRESS}.")
    return "\n".join(lines)


def build_followup_sms(
    lead: Lead,
    custom_message: str | None = None,
    booked_slot: TimeSlot | None = None,
    vehicle: VehicleInfo | None = None,
    service: ServiceInfo | None = None,
) -> str:
    if custom_message:
        return custom_message

    lines = [f"{SHOP_NAME}: Hi {lead.fullName.split()[0]}, thanks for calling."]
    if booked_slot:
        lines.append(f"Your appointment is confirmed for {_fmt_slot(booked_slot)}.")
    if vehicle:
        lines.append(f"Vehicle: {_vehicle_label(vehicle)}.")
    if service:
        lines.append(f"Service: {SERVICE_TYPE_LABELS[service.serviceType]}.")
    lines.append(f"Shop hours: {SHOP_HOURS}. Call {SHOP_PHONE} with questions.")
    return " ".join(lines)


def build_team_booking_sms(
    lead: Lead,
    booked_slot: TimeSlot,
    vehicle: VehicleInfo | None = None,
    service: ServiceInfo | None = None,
) -> str:
    lines = [
        f"ZOL booking: {lead.fullName}",
        f"Customer: {lead.phone}",
        f"Time: {_fmt_slot(booked_slot)}",
    ]
    if vehicle:
        lines.append(f"Vehicle: {_vehicle_label(vehicle)}")
    if service:
        lines.append(f"Service: {SERVICE_TYPE_LABELS[service.serviceType]}")
        lines.append(f"Issue: {service.issueDescription}")
    return "\n".join(lines)


def send_sms(to_number: str, body: str) -> str:
    missing = [key for key, value in {
        "TWILIO_ACCOUNT_SID": TWILIO_ACCOUNT_SID,
        "TWILIO_AUTH_TOKEN": TWILIO_AUTH_TOKEN,
        "TWILIO_FROM_NUMBER": TWILIO_FROM_NUMBER,
    }.items() if not value]
    if missing:
        raise RuntimeError(f"Missing Twilio credentials: {', '.join(missing)}.")

    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    message = client.messages.create(
        body=body,
        from_=TWILIO_FROM_NUMBER,
        to=_format_e164(to_number),
    )
    logger.info("SMS sent to %s with sid=%s", to_number, message.sid)
    return message.sid


def send_team_booking_notification(
    lead: Lead,
    booked_slot: TimeSlot,
    vehicle: VehicleInfo | None = None,
    service: ServiceInfo | None = None,
) -> str | None:
    if not SHOP_TEAM_NOTIFY_NUMBER:
        logger.info("Team booking notification skipped because SHOP_TEAM_NOTIFY_NUMBER is not set.")
        return None

    body = build_team_booking_sms(
        lead=lead,
        booked_slot=booked_slot,
        vehicle=vehicle,
        service=service,
    )
    return send_sms(SHOP_TEAM_NOTIFY_NUMBER, body)
