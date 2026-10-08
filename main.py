from fastapi import FastAPI,HTTPException,WebSocket,WebSocketDisconnect,Request,Depends,Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from pydantic import BaseModel,Field
from schema import PatientTelemetry
from agent import analyze
from simulation import simulate,SCENARIOS
from safety import DISCLAIMER
from auth import configured,password_matches,issue,require,websocket_authorized
from telemetry_gateway import router as telemetry_router
from device_catalog import router as devices_router
from patient_replay import parse_csv,normalized_csv
app=FastAPI(title="AnestheSense CDS API",version="0.1.0",description=DISCLAIMER)
WEB_DIR=Path(__file__).resolve().parent / "web"
app.mount("/web",StaticFiles(directory=str(WEB_DIR)),name="web")
app.include_router(telemetry_router)
app.include_router(devices_router)
class LoginRequest(BaseModel):
    username:str
    password:str
@app.get("/api/v1/auth/status")
def auth_status(request:Request):
    return {"configured":configured(),"authenticated":bool(configured() and __import__("auth").verify(request.cookies.get("anesthesense_session")))}
@app.post("/api/v1/auth/login")
def login(body:LoginRequest,response:Response):
    if not configured():raise HTTPException(503,"Login not configured. Set environment variables.")
    if not password_matches(body.username,body.password):raise HTTPException(401,"Invalid credentials")
    response.set_cookie("anesthesense_session",issue(body.username),httponly=True,samesite="strict",secure=__import__("os").getenv("ANESTHESENSE_COOKIE_SECURE","false").lower()=="true",max_age=28800,path="/")
    return {"authenticated":True}
@app.post("/api/v1/auth/logout")
def logout(response:Response):
    response.delete_cookie("anesthesense_session",path="/")
    return {"authenticated":False}
@app.post("/api/v1/csv/import")
async def import_csv(request:Request,user:str=Depends(require)):
    if request.headers.get("content-type","").split(";")[0] not in ("text/csv","application/octet-stream","text/plain"):
        raise HTTPException(415,"Upload CSV bytes with Content-Type: text/csv")
    if request.headers.get("content-length") and int(request.headers["content-length"])>10_000_000:
        raise HTTPException(413,"CSV exceeds 10 MB limit")
    raw=await request.body()
    try:
        parsed=parse_csv(raw)
    except ValueError as exc:
        raise HTTPException(422,str(exc))
    return {**{k:v for k,v in parsed.items() if k!="case"},"case":parsed["case"].model_dump(mode="json"),"normalized_csv":normalized_csv(parsed["case"].frames)}

class SimRequest(BaseModel):
    scenario:str="Normotensive"
    minutes:int=Field(default=30,ge=3,le=240)
@app.get("/")
def root():return FileResponse(WEB_DIR / "index.html")
@app.get("/health")
def health():return {"status":"ok","version":"0.1.0","research_only":True}
@app.post("/api/v1/predict")
def predict(payload:PatientTelemetry,user:str=Depends(require)):return analyze(payload)
@app.post("/api/v1/simulate")
def simulation(payload:SimRequest,user:str=Depends(require)):
    try:return simulate(payload.scenario,payload.minutes)
    except ValueError as e:raise HTTPException(422,str(e))
@app.post("/api/v1/simulate/analyze")
def simulate_analyze(payload:SimRequest,user:str=Depends(require)):
    try:case=simulate(payload.scenario,payload.minutes)
    except ValueError as e:raise HTTPException(422,str(e))
    return {"case":case.model_dump(mode="json"),"assessment":analyze(case)}
@app.websocket("/ws/telemetry")
async def telemetry(ws:WebSocket):
    if not websocket_authorized(ws):
        await ws.close(code=1008)
        return
    await ws.accept()
    try:
        while True:
            data=await ws.receive_json()
            try:await ws.send_json(analyze(PatientTelemetry.model_validate(data)))
            except Exception as e:await ws.send_json({"error":"Invalid telemetry payload","detail":str(e)})
    except WebSocketDisconnect:pass
