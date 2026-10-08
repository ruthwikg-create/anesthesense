import hashlib
from fastapi.testclient import TestClient
from main import app

def test_csv_import_login_and_validation(monkeypatch):
    monkeypatch.setattr("auth.SECRET","test-secret-abcdefghijklmnopqrstuvwxyz-123")
    monkeypatch.setattr("auth.USER","researcher")
    monkeypatch.setattr("auth.PASSWORD_HASH",hashlib.sha256(b"password").hexdigest())
    c=TestClient(app)
    csv=b"minute;SBP;DBP;HR;SpO2\n0;120;75;75;99\n1;110;70;82;97\n2;bad;65;85;96\n"
    assert c.post("/api/v1/csv/import",content=csv,headers={"Content-Type":"text/csv"}).status_code==401
    assert c.post("/api/v1/auth/login",json={"username":"researcher","password":"password"}).status_code==200
    response=c.post("/api/v1/csv/import",content=csv,headers={"Content-Type":"text/csv"})
    assert response.status_code==200,response.text
    obj=response.json()
    assert obj["rows_read"]==3 and obj["rows_used"]==2 and obj["rows_skipped"]==1
    assert obj["case"]["frames"][0]["MAP"] is None
    assert "MAP" in obj["normalized_csv"]
    assert c.post("/api/v1/csv/import",content=b"",headers={"Content-Type":"text/csv"}).status_code==422
