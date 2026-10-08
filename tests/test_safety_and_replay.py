import io
import pytest
from datetime import datetime, timezone
from pydantic import ValidationError
from schema import TelemetryFrame, PatientBaseline
from safety import metrics, haii, deterministic_rule_check
from patient_replay import parse_csv
from simulation import simulate
from agent import analyze

NOW=datetime(2025,1,1,tzinfo=timezone.utc)
def frame(**kwargs): return TelemetryFrame(timestamp=NOW,**kwargs)
def test_measured_map_preserved():
    assert frame(MAP=72,SBP=120,DBP=80).map_value==72
def test_invalid_bp():
    with pytest.raises(ValidationError): frame(SBP=70,DBP=80)
def test_critical_hypoxemia():
    case=simulate()
    case.frames[-1].SpO2=85
    result=analyze(case)
    assert result["risk_level"]=="CRITICAL"
    assert "CRITICAL_HYPOXEMIA" in result["deterministic_override"]
def test_bis_maintenance_only():
    f=frame(MAP=80,BIS=70)
    d=metrics(f,PatientBaseline())
    assert any(r["code"]=="AWARENESS_RISK" for r in deterministic_rule_check(f,d,"MAINTENANCE"))
    assert not deterministic_rule_check(f,d,"INDUCTION")
def test_shock_index():
    f=frame(MAP=65,SBP=85,DBP=55,HR=100)
    d=metrics(f,PatientBaseline())
    assert any(r["code"]=="ELEVATED_SHOCK_INDEX" for r in deterministic_rule_check(f,d,"MAINTENANCE"))
def test_missing_renormalization():
    score=haii(frame(MAP=65))
    assert score["weight_coverage"]==.3
    assert len(score["missing_signals"])==4
def test_no_fabricated_missing_signals():
    result=parse_csv(b"minute,MAP,HR\n0,80,70\n1,75,75\n")
    assert result["case"].frames[0].SpO2 is None
def test_utf16_csv():
    result=parse_csv("minute;SBP;DBP;HR\n0;120;80;75\n1;110;70;80\n".encode("utf-16"))
    assert result["rows_used"]==2
def test_bad_rows():
    result=parse_csv(b"minute,MAP,HR\n0,80,70\n1,broken,80\n2,70,90\n")
    assert result["rows_skipped"]==1
def test_missing_columns():
    with pytest.raises(ValueError,match="Required"):parse_csv(b"minute,MAP\n0,80\n")
def test_empty_csv():
    with pytest.raises(ValueError):parse_csv(b"")
def test_oversized_csv():
    with pytest.raises(ValueError,match="10 MB"):parse_csv(b"x"*10_000_001)
def test_forecast_decline():
    result=analyze(simulate("Hemorrhage",20))
    assert result["forecast"]["slope"]<0
    assert result["forecast"]["predicted_map_10"]<result["derived"]["map_current"]
def test_api_invalid():
    from fastapi.testclient import TestClient
    from main import app
    assert TestClient(app).post("/api/v1/predict",json={}).status_code==422
