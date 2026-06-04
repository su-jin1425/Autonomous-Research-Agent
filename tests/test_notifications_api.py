def test_notifications_websocket_uses_memory_fallback(client) -> None:
    with client.websocket_connect("/api/v1/research/ws/query-123") as websocket:
        message = websocket.receive_json()

    assert message["query_id"] == "query-123"
    assert message["status"] == "connected"
    assert message["transport"] == "memory"
