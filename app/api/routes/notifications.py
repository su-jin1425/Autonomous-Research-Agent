from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter
from fastapi import WebSocket
from fastapi import WebSocketDisconnect

from app.services.redis_service import RedisService


router = APIRouter(
    prefix="/research",
    tags=["notifications"],
)


@router.websocket("/ws/{query_id}")
async def research_updates(
    websocket: WebSocket,
    query_id: str,
) -> None:
    await websocket.accept()

    redis_service = RedisService()

    pubsub = await redis_service.subscribe(
        f"research:{query_id}"
    )

    if pubsub is None:
        await websocket.send_json(
            {
                "query_id": query_id,
                "status": "connected",
                "transport": "memory",
            }
        )

        await websocket.close()

        return

    try:
        while True:
            message = await asyncio.wait_for(
                pubsub.get_message(
                    ignore_subscribe_messages=True,
                ),
                timeout=30,
            )

            if message:
                payload = json.loads(
                    message["data"]
                )

                await websocket.send_json(
                    {
                        "query_id": query_id,
                        **payload,
                    }
                )

            await websocket.send_json(
                {
                    "type": "heartbeat",
                }
            )

            await asyncio.sleep(15)

    except WebSocketDisconnect:
        pass

    finally:
        await pubsub.unsubscribe(
            f"research:{query_id}"
        )

        await pubsub.close()