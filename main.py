from fastapi import FastAPI,HTTPException,WebSocket,WebSocketDisconnect
from pydantic import BaseModel,Field
from schema import PatientTelemetry
from agent import analyze
from simulation import simulate,SCENARIOS
from safety import DISCLAIMER
app=FastAPI(title="AnestheSense CDS API",version="0.1.0",description=DISCLAIMER)
class SimRequest(BaseModel):
    scenario:str="Normotensive"
    minutes:int=Field(default=30,ge=3,le=240)
@app.get("/")
def root():return {"name":"AnestheSense","version":"0.1.0","disclaimer":DISCLAIMER}
@app.get("/health")
def health():return {"status":"ok","version":"0.1.0","research_only":True}
@app.post("/api/v1/predict")
def predict(payload:PatientTelemetry):return analyze(payload)
@app.post("/api/v1/simulate")
def simulation(payload:SimRequest):
    try:return simulate(payload.scenario,payload.minutes)
    except ValueError as e:raise HTTPException(422,str(e))
@app.post("/api/v1/simulate/analyze")
def simulate_analyze(payload:SimRequest):
    try:case=simulate(payload.scenario,payload.minutes)
    except ValueError as e:raise HTTPException(422,str(e))
    return {"case":case.model_dump(mode="json"),"assessment":analyze(case)}
@app.websocket("/ws/telemetry")
async def telemetry(ws:WebSocket):
    await ws.accept()
    try:
        while True:
            data=await ws.receive_json()
            try:await ws.send_json(analyze(PatientTelemetry.model_validate(data)))
            except Exception as e:await ws.send_json({"error":"Invalid telemetry payload","detail":str(e)})
    except WebSocketDisconnect:pass
