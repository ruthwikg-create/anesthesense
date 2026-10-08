"""Research device capability catalog; listings are not certified integrations."""
from typing import Literal
from pydantic import BaseModel,Field
from fastapi import APIRouter,Depends
from auth import require

class DeviceFamily(BaseModel):
    id:str
    manufacturer:str
    family:str
    category:str
    signals:list[str]
    connection_options:list[str]
    integration_status:Literal["normalized_adapter","planned","reference_only"]="planned"
    validation_note:str="Model-specific export support, software revision, licensing, institutional authorization, and bench validation required."
    capabilities:list[str]=Field(default_factory=lambda:["read_only_observation"])
CATALOG=[
 DeviceFamily(id="philips-intellivue",manufacturer="Philips",family="IntelliVue X2 / MP / MX",category="patient_monitor",signals=["HR","SpO2","MAP","SBP","DBP","EtCO2","CVP"],connection_options=["Manufacturer-authorized Data Export Interface (model-dependent)"],integration_status="normalized_adapter"),
 DeviceFamily(id="ge-carescape",manufacturer="GE HealthCare",family="CARESCAPE B-series",category="patient_monitor",signals=["HR","SpO2","MAP","SBP","DBP","EtCO2"],connection_options=["Approved manufacturer interface or integration gateway"]),
 DeviceFamily(id="mindray-benevision",manufacturer="Mindray",family="BeneVision N-series",category="patient_monitor",signals=["HR","SpO2","MAP","SBP","DBP","EtCO2"],connection_options=["Approved manufacturer interface or integration gateway"]),
 DeviceFamily(id="draeger-infinity",manufacturer="Dräger",family="Infinity monitors",category="patient_monitor",signals=["HR","SpO2","MAP","SBP","DBP","EtCO2"],connection_options=["Approved manufacturer interface or integration gateway"]),
 DeviceFamily(id="nihon-kohden",manufacturer="Nihon Kohden",family="Life Scope monitors",category="patient_monitor",signals=["HR","SpO2","MAP","SBP","DBP","EtCO2"],connection_options=["Approved manufacturer interface or integration gateway"]),
 DeviceFamily(id="spacelabs",manufacturer="Spacelabs Healthcare",family="Patient monitors",category="patient_monitor",signals=["HR","SpO2","MAP","SBP","DBP"],connection_options=["Approved manufacturer interface or integration gateway"]),
 DeviceFamily(id="masimo",manufacturer="Masimo",family="Root / pulse oximetry platforms",category="oxygenation",signals=["SpO2","HR"],connection_options=["Approved device data output or gateway"]),
 DeviceFamily(id="ge-anesthesia",manufacturer="GE HealthCare",family="Aisys / Carestation",category="anesthesia_workstation",signals=["EtCO2","FiO2","airway_pressure","tidal_volume","respiratory_rate","agent_concentration"],connection_options=["Approved workstation export or gateway"]),
 DeviceFamily(id="draeger-anesthesia",manufacturer="Dräger",family="Perseus / Atlan / Fabius",category="anesthesia_workstation",signals=["EtCO2","FiO2","airway_pressure","tidal_volume","respiratory_rate","agent_concentration"],connection_options=["Approved workstation export or gateway"]),
 DeviceFamily(id="mindray-anesthesia",manufacturer="Mindray",family="A-series anesthesia workstations",category="anesthesia_workstation",signals=["EtCO2","FiO2","airway_pressure","tidal_volume","respiratory_rate"],connection_options=["Approved workstation export or gateway"]),
 DeviceFamily(id="hamilton",manufacturer="Hamilton Medical",family="Critical care ventilators",category="ventilator",signals=["EtCO2","FiO2","airway_pressure","tidal_volume","respiratory_rate","PEEP"],connection_options=["Approved ventilator export or gateway"]),
 DeviceFamily(id="draeger-ventilator",manufacturer="Dräger",family="Evita / Savina ventilators",category="ventilator",signals=["FiO2","airway_pressure","tidal_volume","respiratory_rate","PEEP"],connection_options=["Approved ventilator export or gateway"]),
 DeviceFamily(id="medtronic-bis",manufacturer="Medtronic",family="BIS monitoring",category="depth_of_anesthesia",signals=["BIS"],connection_options=["Approved device data export"]),
 DeviceFamily(id="tof-monitor",manufacturer="Multi-vendor",family="Neuromuscular blockade / TOF monitors",category="neuromuscular",signals=["TOF_ratio","TOF_twitches"],connection_options=["Approved device data export"]),
 DeviceFamily(id="infusion-pump",manufacturer="Multi-vendor",family="Infusion / syringe pumps",category="infusion_observation",signals=["pump_running","infusion_rate_display"],connection_options=["Approved read-only integration gateway"],capabilities=["read_only_observation","no_pump_control","no_dose_recommendation"]),
 DeviceFamily(id="blood-gas",manufacturer="Multi-vendor",family="Blood gas analyzers",category="laboratory",signals=["pH","PaCO2","PaO2","lactate","hemoglobin"],connection_options=["Authorized LIS / HL7 / FHIR feed"],capabilities=["retrospective_lab_observation"]),
 DeviceFamily(id="temperature",manufacturer="Multi-vendor",family="Temperature and warming systems",category="temperature",signals=["temperature"],connection_options=["Approved monitoring export"]),
 DeviceFamily(id="cardiac-output",manufacturer="Multi-vendor",family="Hemodynamic / cardiac output monitors",category="hemodynamic",signals=["cardiac_output","cardiac_index","SVV","CVP"],connection_options=["Approved device export"]),
]
router=APIRouter(prefix="/api/v1/devices",tags=["Research device catalog"])
@router.get("/catalog")
def catalog(user:str=Depends(require)):
    return {"devices":[d.model_dump() for d in CATALOG],"certification":"NONE","disclaimer":"Catalog entries are integration targets, not verified interoperability or clinical-device certification."}
@router.get("/categories")
def categories(user:str=Depends(require)):
    return {"categories":sorted(set(d.category for d in CATALOG))}
