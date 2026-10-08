"""Philips IntelliVue normalized research adapter boundary.

Accepts ONLY decoded, de-identified numerics from an independently authorized
vendor-compatible export client. Does not implement Philips association,
UDP discovery, serial commands, or bedside device control.
"""
from datetime import datetime,timezone
from typing import Literal
from pydantic import BaseModel,Field,model_validator
from schema import TelemetryFrame

SIGNALS={
    "NIBP_MAP":("MAP","mmHg"),"ABP_MAP":("MAP","mmHg"),
    "NIBP_SYS":("SBP","mmHg"),"ABP_SYS":("SBP","mmHg"),
    "NIBP_DIA":("DBP","mmHg"),"ABP_DIA":("DBP","mmHg"),
    "PULSE":("HR","bpm"),"ECG_HR":("HR","bpm"),
    "SPO2":("SpO2","%"),"ETCO2":("EtCO2","mmHg"),
    "CVP":("CVP","mmHg"),"SVV":("SVV","%"),
    "BIS":("BIS","index"),"TOF_RATIO":("TOF_ratio","ratio"),
}
MAX_AGE_SECONDS=15
class Numeric(BaseModel):
    code:str
    value:float
    unit:str
    quality:Literal["VALID","INVALID","UNAVAILABLE"]="VALID"
class ExportPacket(BaseModel):
    source:Literal["PHILIPS_INTELLIVUE_NORMALIZED"]
    source_id:str=Field(min_length=3,max_length=80,pattern=r"^[a-zA-Z0-9_.-]+$")
    sequence:int=Field(ge=0)
    timestamp:datetime
    measurements:list[Numeric]=Field(min_length=1,max_length=100)
    @model_validator(mode="after")
    def tz_required(self):
        if self.timestamp.tzinfo is None or self.timestamp.utcoffset() is None:
            raise ValueError("Timestamp must include timezone")
        return self
def normalize(packet:ExportPacket,now:datetime|None=None):
    now=now or datetime.now(timezone.utc)
    age=(now-packet.timestamp).total_seconds()
    if age>MAX_AGE_SECONDS or age< -5:
        raise ValueError("Stale or future monitor timestamp")
    fields={};warnings=[]
    for item in packet.measurements:
        spec=SIGNALS.get(item.code)
        if spec is None:
            warnings.append("Unsupported code "+item.code);continue
        target,expected=spec
        if item.quality!="VALID":
            warnings.append("Unusable "+item.code);continue
        if item.unit!=expected:
            warnings.append("Unit mismatch "+item.code);continue
        if target in fields:
            warnings.append("Duplicate mapped signal "+target);continue
        fields[target]=item.value
    if not fields:raise ValueError("No valid supported numerics")
    frame=TelemetryFrame(timestamp=packet.timestamp,**fields)
    return frame,{"source_id":packet.source_id,"sequence":packet.sequence,"age_seconds":round(age,3),"mapped_signals":sorted(fields),"warnings":warnings,"research_only":True}
