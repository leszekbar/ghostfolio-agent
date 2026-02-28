from fastapi.testclient import TestClient

from app.data_sources.mock_provider import MOCK_PERFORMANCE
from app.main import app


client = TestClient(app)


def test_portfolio_summary_happy_path():
    response = client.post(
        "/chat",
        json={"message": "What's my portfolio worth?", "session_id": "s1", "data_source": "mock"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["tool_calls"] == ["get_portfolio_summary"]
    assert "portfolio value" in body["response"].lower()
    assert body["verification"]["fact_grounded"] is True
    assert body["verification"]["disclaimer_present"] is True


def test_performance_happy_path():
    response = client.post(
        "/chat",
        json={"message": "How has my portfolio performed this year?", "session_id": "s2", "data_source": "mock"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["tool_calls"] == ["get_performance"]
    assert "ytd" in body["response"].lower()
    assert body["verification"]["fact_grounded"] is True


def test_transactions_happy_path():
    response = client.post(
        "/chat",
        json={"message": "Show me my recent transactions", "session_id": "s3", "data_source": "mock"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["tool_calls"] == ["get_transactions"]
    assert "recent transactions" in body["response"].lower()
    assert body["verification"]["disclaimer_present"] is True


def test_follow_up_uses_session_context():
    first = client.post(
        "/chat",
        json={"message": "How has my portfolio performed this year?", "session_id": "s4", "data_source": "mock"},
    )
    assert first.status_code == 200
    second = client.post(
        "/chat",
        json={"message": "What about last year?", "session_id": "s4", "data_source": "mock"},
    )
    assert second.status_code == 200
    body = second.json()
    assert body["tool_calls"] == ["get_performance"]
    assert "1y" in body["response"].lower()


def test_disclaimer_always_present_on_p0_queries():
    for msg in [
        "What's my portfolio worth?",
        "How has my portfolio performed this year?",
        "Show me my recent transactions",
    ]:
        response = client.post(
            "/chat",
            json={"message": msg, "session_id": "s5", "data_source": "mock"},
        )
        assert response.status_code == 200
        assert "not financial advice" in response.json()["response"].lower()


def test_multi_step_compare_chains_summary_and_performance_tools():
    response = client.post(
        "/chat",
        json={
            "message": "Compare my holdings performance this year",
            "session_id": "s6",
            "data_source": "mock",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["tool_calls"] == ["get_portfolio_summary", "get_performance"]
    assert "compared to your total portfolio value" in body["response"].lower()
    assert body["verification"]["fact_grounded"] is True


def test_follow_up_after_multi_step_prefers_performance_context():
    first = client.post(
        "/chat",
        json={
            "message": "Compare my holdings performance this year",
            "session_id": "s7",
            "data_source": "mock",
        },
    )
    assert first.status_code == 200
    second = client.post(
        "/chat",
        json={"message": "What about max?", "session_id": "s7", "data_source": "mock"},
    )
    assert second.status_code == 200
    body = second.json()
    assert body["tool_calls"] == ["get_performance"]
    assert "max" in body["response"].lower()


def test_stale_data_warning_reduces_confidence(monkeypatch):
    stale_payload = dict(MOCK_PERFORMANCE["ytd"])
    stale_payload["last_updated"] = "2020-01-01T00:00:00Z"
    monkeypatch.setitem(MOCK_PERFORMANCE, "ytd", stale_payload)

    response = client.post(
        "/chat",
        json={
            "message": "How has my portfolio performed this year?",
            "session_id": "s8",
            "data_source": "mock",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["verification"]["stale_data_warning"] is True
    assert body["verification"]["confidence_level"] == "medium"
    assert body["confidence"] < 0.8
    assert "older than 6 hours" in body["response"].lower()
