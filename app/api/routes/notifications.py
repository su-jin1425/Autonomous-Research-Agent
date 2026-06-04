import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.redis_service import RedisService


router = APIRouter(prefix="/research", tags=["notifications"])


@router.websocket("/ws/{query_id}")
async def research_updates(websocket: WebSocket, query_id: str) -> None:
    await websocket.accept()
    redis = RedisService()
    client = await redis._client()
    if client is None:
        await websocket.send_json({"query_id": query_id, "status": "connected", "transport": "memory"})
        await websocket.close()
        return

    pubsub = client.pubsub()
    await pubsub.subscribe(f"research:{query_id}")
    try:
        async for message in pubsub.listen():
            if message.get("type") != "message":
                continue
            payload = json.loads(message.get("data", "{}"))
            await websocket.send_json({"query_id": query_id, **payload})
    except WebSocketDisconnect:
        return
    finally:
        await pubsub.unsubscribe(f"research:{query_id}")
        await pubsub.close()
