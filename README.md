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
