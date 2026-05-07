"""
ZOL AI Receptionist - FastAPI backend.

Run locally with:
    uvicorn main:app --reload --port 8000
"""
from __future__ import annotations

import asyncio
import logging
import os
import sys

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

load_dotenv()

sys.path.insert(0, os.path.dirname(__file__))

from keepalive import start_keepalive
from routes.health import router as health_router
from routes.tools import router as tools_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ZOL AI Voice Receptionist",
    description=(
        "Backend for the ZOL mechanic-shop voice receptionist. "
        "Provides Vapi tool webhook endpoints for quote SMS and follow-up SMS."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(tools_router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception on %s %s: %s", request.method, request.url.path, exc)
    return JSONResponse(
        status_code=500,
        content={
            "ok": False,
            "errorCode": "server_error",
            "error": "An unexpected server error occurred.",
        },
    )


@app.on_event("startup")
async def on_startup() -> None:
    asyncio.create_task(start_keepalive())
    base_url = os.getenv("BASE_URL", "http://localhost:8000")
    shop_name = os.getenv("SHOP_NAME", "ZOL")
    logger.info("=" * 60)
    logger.info("%s AI receptionist backend starting up", shop_name)
    logger.info("  BASE_URL         : %s", base_url)
    logger.info("  Quote SMS tool   : POST %s/tools/send_quote_sms", base_url.rstrip("/"))
    logger.info("  Follow-up tool   : POST %s/tools/send_followup_sms", base_url.rstrip("/"))
    logger.info("=" * 60)


@app.on_event("shutdown")
async def on_shutdown() -> None:
    logger.info("ZOL backend shutting down.")
