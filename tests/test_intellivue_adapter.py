from datetime import datetime,timedelta,timezone
import pytest
from pydantic import ValidationError
from intellivue_adapter import ExportPacket,normalize

NOW=datetime(2030,1,1,tzinfo=timezone.utc)
def packet(measurements=None,stamp=None):
    return ExportPacket(source="PHILIPS_INTELLIVUE_NORMALIZED",source_id="lab-monitor-01",sequence=1,timestamp=stamp or NOW,measurements=measurements or [{"code":"ABP_MAP","value":75,"unit":"mmHg"},{"code":"ECG_HR","value":82,"unit":"bpm"},{"code":"SPO2","value":98,"unit":"%"}])
def test_valid_packet():
    frame,meta=normalize(packet(),now=NOW+timedelta(seconds=2))
    assert frame.MAP==75 and frame.HR==82 and frame.SpO2==98
    assert meta["research_only"]
def test_stale_rejected():
    with pytest.raises(ValueError,match="Stale"):normalize(packet(),now=NOW+timedelta(seconds=16))
def test_future_rejected():
    with pytest.raises(ValueError,match="Stale"):normalize(packet(),now=NOW-timedelta(seconds=6))
def test_invalid_quality_dropped():
    p=packet([{"code":"ABP_MAP","value":75,"unit":"mmHg","quality":"INVALID"},{"code":"ECG_HR","value":82,"unit":"bpm"}])
    frame,meta=normalize(p,now=NOW)
    assert frame.MAP is None and frame.HR==82
def test_wrong_units_rejected():
    with pytest.raises(ValueError,match="No valid"):normalize(packet([{"code":"ABP_MAP","value":10,"unit":"kPa"}]),now=NOW)
def test_unknown_code_rejected():
    with pytest.raises(ValueError,match="No valid"):normalize(packet([{"code":"UNSUPPORTED","value":1,"unit":"mmHg"}]),now=NOW)
def test_naive_timestamp_rejected():
    with pytest.raises(ValidationError):packet(stamp=datetime(2030,1,1))
def test_invalid_value_rejected():
    with pytest.raises(ValidationError):normalize(packet([{"code":"SPO2","value":130,"unit":"%"}]),now=NOW)
