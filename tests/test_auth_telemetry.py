import hashlib
from fastapi.testclient import TestClient
from main import app
def test_auth_and_research_gateway(monkeypatch):
    monkeypatch.setattr("auth.SECRET","a-test-secret-longer-than-thirty-two-characters")
    monkeypatch.setattr("auth.USER","researcher")
    monkeypatch.setattr("auth.PASSWORD_HASH",hashlib.sha256(b"test-password").hexdigest())
    client=TestClient(app)
    assert client.get("/api/v1/telemetry/status").status_code==401
    assert client.post("/api/v1/auth/login",json={"username":"researcher","password":"wrong"}).status_code==401
    assert client.post("/api/v1/auth/login",json={"username":"researcher","password":"test-password"}).status_code==200
    assert client.get("/api/v1/telemetry/status").status_code==200
    frame={"timestamp":"2035-01-01T00:00:00Z","MAP":75,"HR":80,"SpO2":98}
    assert client.post("/api/v1/telemetry/ingest",json=frame).status_code==200
    assert client.post("/api/v1/telemetry/ingest",json=frame).status_code==409
    with client.websocket_connect("/api/v1/telemetry/stream") as ws:
        assert ws.receive_json()["type"]=="status"
        frame["timestamp"]="2035-01-01T00:01:00Z"
        assert client.post("/api/v1/telemetry/ingest",json=frame).status_code==200
        assert ws.receive_json()["type"]=="telemetry"
    assert client.post("/api/v1/auth/logout").status_code==200
    assert client.get("/api/v1/telemetry/status").status_code==401
