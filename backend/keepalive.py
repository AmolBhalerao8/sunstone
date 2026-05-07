"""
Keep-alive background task for hosted free tiers.
"""
from __future__ import annotations

import asyncio
import logging
import os

import httpx

logger = logging.getLogger(__name__)


async def start_keepalive() -> None:
    base_url = os.getenv("BASE_URL", "")
    if not base_url or "localhost" in base_url:
        logger.info("Keep-alive disabled because BASE_URL is local or empty.")
        return

    url = f"{base_url.rstrip('/')}/health"
    logger.info("Keep-alive started: pinging %s every 10 minutes.", url)

    while True:
        await asyncio.sleep(600)
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(url)
                logger.info("Keep-alive ping returned %s.", response.status_code)
        except Exception as exc:
            logger.warning("Keep-alive ping failed: %s", exc)
