"""
Vapi tool webhook endpoints.

Vapi sends tool calls in this envelope:
  { "message": { "type": "tool-calls", "toolCallList": [...] } }

For local tests, these endpoints also accept the flat tool arguments directly.
"""
from __future__ import annotations

import json
import logging
from typing import TypeVar

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from models.tool_schemas import (
    SendFollowupSmsArgs,
    SendQuoteSmsArgs,
    VapiWebhookPayload,
)
from services.pricing import calculate_quote
from services.sms_service import build_followup_sms, build_quote_sms, send_sms

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tools", tags=["tools"])

T = TypeVar("T", bound=BaseModel)


def _vapi_error(tool_call_id: str, code: str, message: str) -> JSONResponse:
    payload = json.dumps({"ok": False, "errorCode": code, "error": message})
    return JSONResponse(
        status_code=200,
        content={"results": [{"toolCallId": tool_call_id, "result": payload}]},
    )


def _vapi_ok(tool_call_id: str, data: dict) -> JSONResponse:
    return JSONResponse(
        status_code=200,
        content={"results": [{"toolCallId": tool_call_id, "result": json.dumps(data)}]},
    )


def _direct_ok(data: dict) -> JSONResponse:
    return JSONResponse(status_code=200, content=data)


def _parse_vapi_args(body: dict, schema: type[T]) -> tuple[T | None, str | None, JSONResponse | None]:
    if "message" not in body:
        try:
            return schema.model_validate(body), "direct-test", None
        except Exception as exc:
            return None, None, JSONResponse(status_code=422, content={"error": str(exc)})

    try:
        payload = VapiWebhookPayload.model_validate(body)
    except Exception as exc:
        logger.error("Failed to parse Vapi envelope: %s", exc)
        return None, None, JSONResponse(status_code=422, content={"error": str(exc)})

    tool_calls = payload.message.toolCallList or []
    if not tool_calls:
        return None, None, JSONResponse(status_code=200, content={"results": []})

    tool_call = tool_calls[0]
    try:
        return schema.model_validate(tool_call.function.arguments), tool_call.id, None
    except Exception as exc:
        logger.error("Invalid tool arguments: %s", exc)
        return None, tool_call.id, _vapi_error(tool_call.id, "invalid_args", f"Invalid arguments: {exc}")


async def _json_body(request: Request) -> dict | JSONResponse:
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"error": "Invalid JSON body"})
    if not isinstance(body, dict):
        return JSONResponse(status_code=400, content={"error": "JSON body must be an object"})
    return body


@router.post("/send_quote_sms", response_model=None)
async def send_quote_sms(request: Request) -> JSONResponse:
    body = await _json_body(request)
    if isinstance(body, JSONResponse):
        return body

    args, tool_call_id, error = _parse_vapi_args(body, SendQuoteSmsArgs)
    if error:
        return error
    assert args is not None and tool_call_id is not None

    if not args.lead.smsConsent:
        return _vapi_error(
            tool_call_id,
            "missing_sms_consent",
            "Please ask the caller for permission to text the estimate to this number.",
        )

    quote = args.quote if args.quote else calculate_quote(args.service, args.vehicle)
    sms_body = build_quote_sms(
        lead=args.lead,
        vehicle=args.vehicle,
        service=args.service,
        quote=quote,
        available_slots=args.availableSlots,
        booked_slot=args.bookedSlot,
    )

    try:
        message_sid = send_sms(args.lead.phone, sms_body)
    except ValueError as exc:
        return _vapi_error(tool_call_id, "invalid_phone", str(exc))
    except RuntimeError as exc:
        logger.error("SMS delivery failed: %s", exc)
        return _vapi_error(
            tool_call_id,
            "sms_failed",
            "I had trouble sending the text. Please confirm the best phone number.",
        )

    result = {
        "ok": True,
        "quoteTotal": quote.total,
        "quoteCurrency": quote.currency,
        "sentTo": args.lead.phone,
        "messageSid": message_sid,
        "bookedSlot": args.bookedSlot.model_dump() if args.bookedSlot else None,
    }
    return _direct_ok(result) if tool_call_id == "direct-test" else _vapi_ok(tool_call_id, result)


@router.post("/send_followup_sms", response_model=None)
async def send_followup_sms(request: Request) -> JSONResponse:
    body = await _json_body(request)
    if isinstance(body, JSONResponse):
        return body

    args, tool_call_id, error = _parse_vapi_args(body, SendFollowupSmsArgs)
    if error:
        return error
    assert args is not None and tool_call_id is not None

    if not args.lead.smsConsent:
        return _vapi_error(
            tool_call_id,
            "missing_sms_consent",
            "Please ask the caller for permission to text this follow-up to the number.",
        )

    sms_body = build_followup_sms(
        lead=args.lead,
        custom_message=args.customMessage,
        booked_slot=args.bookedSlot,
        vehicle=args.vehicle,
        service=args.service,
    )

    try:
        message_sid = send_sms(args.lead.phone, sms_body)
    except ValueError as exc:
        return _vapi_error(tool_call_id, "invalid_phone", str(exc))
    except RuntimeError as exc:
        logger.error("Follow-up SMS failed: %s", exc)
        return _vapi_error(
            tool_call_id,
            "sms_failed",
            "I had trouble sending the follow-up text. Please confirm the phone number.",
        )

    result = {
        "ok": True,
        "sentTo": args.lead.phone,
        "messageSid": message_sid,
    }
    return _direct_ok(result) if tool_call_id == "direct-test" else _vapi_ok(tool_call_id, result)
