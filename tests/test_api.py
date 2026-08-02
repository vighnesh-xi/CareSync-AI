from fastapi.testclient import TestClient

from app.main import app, session_store


client = TestClient(app)


class DummyOrchestrator:
    def start_conversation(self):
        return {
            "response": "Hello! I'm your post-discharge care assistant. What's your name?",
            "current_agent": "receptionist",
            "patient_data": None,
            "patient_verified": False,
        }

    def handle_message(self, user_message, session_state):
        if not session_state.get("patient_verified"):
            return {
                "response": "Hi John Smith! I found your discharge report from 2024-01-15 for Chronic Kidney Disease Stage 3. How are you feeling today?",
                "current_agent": "receptionist",
                "patient_data": {
                    "patient_name": "John Smith",
                    "primary_diagnosis": "Chronic Kidney Disease Stage 3"
                },
                "patient_verified": True,
                "citations": [],
            }

        return {
            "response": "Based on nephrology guidance, swelling can indicate fluid retention. [1]",
            "current_agent": "clinical",
            "patient_data": session_state.get("patient_data"),
            "patient_verified": True,
            "source_type": "reference_material",
            "citations": [
                {
                    "title": "Nephrology Reference Chunk 1",
                    "source": "nephrology_reference.pdf"
                }
            ],
        }


def test_start_session(monkeypatch):
    from app import main

    monkeypatch.setattr(main, "orchestrator", DummyOrchestrator())
    session_store.clear()

    response = client.post("/start-session", params={"session_id": "test-session-1"})

    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == "test-session-1"
    assert data["agent"] == "receptionist"
    assert "What's your name?" in data["response"]


def test_chat_flow(monkeypatch):
    from app import main

    monkeypatch.setattr(main, "orchestrator", DummyOrchestrator())
    session_store.clear()

    client.post("/start-session", params={"session_id": "test-session-2"})

    response = client.post(
        "/chat",
        json={
            "session_id": "test-session-2",
            "message": "John Smith"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["agent"] == "receptionist"
    assert data["patient_verified"] is True
    assert data["patient_name"] == "John Smith"

    response_2 = client.post(
        "/chat",
        json={
            "session_id": "test-session-2",
            "message": "I have swelling in my legs. Should I be worried?"
        }
    )

    assert response_2.status_code == 200
    data_2 = response_2.json()
    assert data_2["agent"] == "clinical"
    assert data_2["source_type"] == "reference_material"
    assert len(data_2["citations"]) > 0