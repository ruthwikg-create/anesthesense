# AnestheSense

**A Transparent Intraoperative Hemodynamic Early Warning Clinical Decision Support Prototype**

AnestheSense is a transparent, multiparameter, trajectory-aware intraoperative hemodynamic early warning research prototype. It observes de-identified retrospective or synthetic physiological data, computes deterministic derived metrics, evaluates research thresholds, forecasts MAP trajectories, and provides auditable explanations.

> **Research and education only. Not clinically validated. Not for patient care, diagnosis, medication dosing, or autonomous treatment.** Research thresholds must not substitute for validated protocols or professional judgment.

## Architecture
- `schema.py`: Pydantic validation of case baseline and frames
- `safety.py`: deterministic research rules, MAP/pulse pressure/shock index, HAII-style composite with missing-weight renormalization
- `forecasting.py`: transparent linear MAP forecast (+10/+15 min), slope, acceleration and volatility
- `agent.py`: risk classification and deterministic explanation; no generative model can override rules
- `simulation.py`: reproducible synthetic scenario generation
- `patient_replay.py`: de-identified CSV parsing, alias mapping, quality statistics and normalized export
- `main.py`: FastAPI endpoints and WebSocket telemetry
- `dashboard.py`: Streamlit research workstation, six-stage workflow, chart, assessment and audit JSON

## Run locally (Windows PowerShell)
```powershell
py -3.11 -m venv venv
.\\venv\\Scripts\\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```
In a second terminal, activate the same environment and run:
```powershell
python -m streamlit run dashboard.py
```
Dashboard: http://localhost:8501 • API: http://127.0.0.1:8000 • Health: http://127.0.0.1:8000/health • Docs: http://127.0.0.1:8000/docs

## API
- `GET /`, `GET /health`
- `POST /api/v1/predict` — validated PatientTelemetry
- `POST /api/v1/simulate` — `{"scenario":"Hemorrhage","minutes":30}`
- `POST /api/v1/simulate/analyze` — simulated case and assessment
- `WS /ws/telemetry` — JSON PatientTelemetry messages

## Methods and limitations
MAP is measured when supplied, otherwise derived as DBP+(SBP−DBP)/3. Pulse pressure=SBP−DBP; shock index=HR/SBP; baseline deviation=(MAP−baseline)/baseline×100. HAII-style composite is an **unvalidated research score**, not a clinical probability. Its available weights (MAP .30, HR .15, SpO2 .25, EtCO2 .15, BIS .15) are renormalized when inputs are missing. Forecasts are simple extrapolations, not calibrated predictions. Synthetic simulations do not establish clinical performance. No medication suggestions or dosing are generated.

CSV accepts common column aliases and multiple encodings/delimiters; files are limited to 10 MB. Use only de-identified datasets. No Gemini API calls are implemented in this initial release; deterministic explanations always work offline. Optional Gemini integration is future work and must never change deterministic alerts. No credentials are needed; `.env` is ignored.

## Tests
```bash
python -m compileall -q .
pytest -q
```
GitHub Actions runs both checks on pushes and pull requests.

## Ethics and future work
This is not a medical device or clinically validated decision aid. Future research includes signal artifact detection, prospective evaluation on authorized de-identified datasets, retrospective forecast error/lead-time analysis, calibrated uncertainty, optional strictly bounded AI explanation, and independent clinical review. No comparative superiority over commercial hypotension prediction systems is claimed.


## Browser-based web app

The FastAPI server now serves the responsive HTML/CSS/JavaScript research workstation at **http://127.0.0.1:8000/**. Run:

```powershell
py -3.11 -m venv venv
.\\venv\\Scripts\\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000/ in a browser. The original Streamlit dashboard remains optional at port 8501. The browser app uses the same authoritative FastAPI deterministic analysis engine. Its client-side CSV importer is an initial research convenience parser and does not yet cover all quoted-field edge cases or server-side CSV verification. Do not use identifiable patient data.

## Login configuration (required)

The web workstation and research APIs require administrator-configured credentials. There are **no default accounts**. Set these in the same PowerShell session before running the server:

```powershell
$env:ANESTHESENSE_USERNAME = "researcher"
$env:ANESTHESENSE_SESSION_SECRET = python -c "import secrets; print(secrets.token_urlsafe(48))"
$env:ANESTHESENSE_PASSWORD_SHA256 = python -c "import hashlib,getpass; print(hashlib.sha256(getpass.getpass('New password: ').encode()).hexdigest())"
$env:ANESTHESENSE_COOKIE_SECURE = "false"
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000/ and sign in using the chosen username and password. For HTTPS deployment, set `ANESTHESENSE_COOKIE_SECURE=true`. Session signing is in-memory/stateless and changing the secret invalidates old sessions. Passwords are stored as SHA-256 digests in this **single-user research prototype**, not a production identity system; production use requires an identity provider, rate limiting, CSRF protection, account lifecycle management and security review. Do not expose this development server directly to the internet.

## Research telemetry gateway

The **Connect research feed** button subscribes to an authenticated WebSocket at `/api/v1/telemetry/stream`. An authorized software bridge can POST individual de-identified `TelemetryFrame` JSON objects to `/api/v1/telemetry/ingest` using the authenticated session cookie. `GET /api/v1/telemetry/status` reports buffered frames and subscribers. Frames must have strictly increasing ISO timestamps. This gateway stores only a bounded in-memory buffer and sends no device-control commands.

**Important:** This is a software relay, **not** a bedside-monitor driver or validated medical-device interface. Real physical bedside-monitor connectivity is not implemented. Connecting an authorized research feed requires manufacturer/model/protocol documentation, approved interface access, network segmentation, appropriate patient-data handling, signal validation, fail-safe behavior and a separate security and clinical safety review. Do not connect to a live patient monitor for patient-care decisions.

The browser's CSV importer is an initial preview parser and is not yet a full standards-compliant CSV parser. Its verification button is a user attestation, not independent dataset validation. Use synthetic or appropriately de-identified research data only.
