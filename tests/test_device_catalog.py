from fastapi.testclient import TestClient
from main import app
from device_catalog import CATALOG

def test_catalog_unique_ids():
    assert len({d.id for d in CATALOG})==len(CATALOG)
def test_catalog_no_device_control():
    assert all("read_only_observation" in d.capabilities or "retrospective_lab_observation" in d.capabilities for d in CATALOG)
    assert all("dose" not in capability or capability=="no_dose_recommendation" for d in CATALOG for capability in d.capabilities)
def test_catalog_is_not_certification():
    assert all(d.integration_status in ("planned","normalized_adapter","reference_only") for d in CATALOG)
def test_catalog_requires_login():
    client=TestClient(app)
    assert client.get("/api/v1/devices/catalog").status_code==401
