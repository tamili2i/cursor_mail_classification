import pytest
import asyncio
from fastapi.testclient import TestClient
from week6.collaborative_docs_architecture.services.collaboration_service.main import app

@pytest.mark.asyncio
async def test_websocket_join_and_presence():
    client = TestClient(app)
    doc_id = "testdoc"
    with client.websocket_connect(f"/ws/documents/{doc_id}?user_id=user1&username=User1") as ws1:
        join_event = ws1.receive_json()
        assert join_event["type"] == "user_joined"
        presence_event = ws1.receive_json()
        assert presence_event["type"] == "presence"
        # Connect a second user
        with client.websocket_connect(f"/ws/documents/{doc_id}?user_id=user2&username=User2") as ws2:
            join_event2 = ws2.receive_json()
            assert join_event2["type"] == "user_joined"
            presence_event2 = ws2.receive_json()
            assert presence_event2["type"] == "presence"
            # Both users should see each other in presence
            ws1_presence = ws1.receive_json()
            assert ws1_presence["type"] == "presence"
            assert any(u["user_id"] == "user2" for u in ws1_presence["users"])
            # Send a document change from user2
            ws2.send_json({
                "type": "document_change",
                "user_id": "user2",
                "op": {"op_type": "insert", "pos": 0, "text": "A"},
                "version": 1,
                "timestamp": 123.0
            })
            change_event = ws1.receive_json()
            assert change_event["type"] == "document_change"
            attribution_event = ws1.receive_json()
            assert attribution_event["type"] == "attribution"
            # Send a cursor position from user1
            ws1.send_json({
                "type": "cursor_position",
                "user_id": "user1",
                "position": 1
            })
            cursor_event = ws2.receive_json()
            assert cursor_event["type"] == "cursor_position"
            presence_update = ws2.receive_json()
            assert presence_update["type"] == "presence" 