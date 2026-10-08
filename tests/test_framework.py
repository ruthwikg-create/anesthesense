from datetime import datetime,timedelta,timezone
from fastapi.testclient import TestClient
from schema import TelemetryFrame,PatientBaseline,PatientTelemetry
from safety import metrics,haii
from agent import analyze
from simulation import simulate
from patient_replay import parse_csv,normalized_csv
from main import app
def test_metrics():
    f=TelemetryFrame(timestamp=datetime.now(timezone.utc),SBP=84,DBP=51,HR=98)
    d=metrics(f,PatientBaseline(baseline_map=78))
    assert d["map_current"]==62
    assert d["pulse_pressure"]==33
    assert round(d["shock_index"],2)==1.17
    assert round(d["map_deviation_percent"],1)==-20.5
def test_critical():
    c=simulate("Hemorrhage",30)
    assert analyze(c)["risk_level"]=="CRITICAL"
def test_missing_weights():
    f=TelemetryFrame(timestamp=datetime.now(timezone.utc),MAP=70,HR=80)
    assert haii(f)["weight_coverage"]==.45
def test_csv():
    p=parse_csv(b"minute;SBP;DBP;HR\n0;120;80;75\n1;110;70;80\n")
    assert p["rows_used"]==2
    assert p["case"].frames[0].map_value>90
    assert "minute" in normalized_csv(p["case"].frames)
def test_api():
    c=TestClient(app)
    assert c.get("/health").status_code==200
    assert c.post("/api/v1/simulate/analyze",json={"scenario":"Normotensive","minutes":10}).status_code==200
