from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field, model_validator

class PatientBaseline(BaseModel):
    baseline_sbp: float | None = None
    baseline_dbp: float | None = None
    baseline_hr: float | None = None
    baseline_map: float | None = None

class TelemetryFrame(BaseModel):
    timestamp: datetime
    MAP: float | None = Field(default=None, ge=0, le=250)
    HR: float | None = Field(default=None, ge=0, le=300)
    SBP: float | None = Field(default=None, ge=0, le=350)
    DBP: float | None = Field(default=None, ge=0, le=250)
    SVV: float | None = None
    EtCO2: float | None = None
    SpO2: float | None = Field(default=None, ge=0, le=100)
    CVP: float | None = None
    BIS: float | None = Field(default=None, ge=0, le=100)
    TOF_twitches: float | None = None
    TOF_ratio: float | None = None
    @model_validator(mode="after")
    def validate_bp(self):
        if self.SBP is not None and self.DBP is not None and self.SBP <= self.DBP:
            raise ValueError("SBP must exceed DBP")
        return self
    @property
    def map_value(self):
        return self.MAP if self.MAP is not None else (self.DBP + (self.SBP-self.DBP)/3 if self.SBP is not None and self.DBP is not None else None)

class PatientTelemetry(BaseModel):
    age: int | None = Field(default=None, ge=0, le=120)
    weight_kg: float | None = Field(default=None, gt=0)
    surgical_phase: Literal["INDUCTION","MAINTENANCE","EMERGENCE"] = "MAINTENANCE"
    baseline: PatientBaseline = Field(default_factory=PatientBaseline)
    frames: list[TelemetryFrame] = Field(min_length=1)
