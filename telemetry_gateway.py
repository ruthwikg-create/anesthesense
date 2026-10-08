"""Opt-in research telemetry relay for de-identified, authorized data sources.
Not a medical device interface; no automatic device discovery or control.
"""
import asyncio
from collections import deque
from fastapi import APIRouter,Depends,HTTPException,WebSocket,WebSocketDisconnect
from auth import require,websocket_authorized
from schema import TelemetryFrame,PatientBaseline,PatientTelemetry
from agent import analyze
router=APIRouter(prefix="/api/v1/telemetry",tags=["Research telemetry"])
_frames=deque(maxlen=240)
_clients=set()
_lock=asyncio.Lock()
@router.get("/status")
async def status(user:str=Depends(require)):
    return {"mode":"RESEARCH_ONLY","connected_subscribers":len(_clients),"buffered_frames":len(_frames),"source":"Authorized de-identified telemetry bridge; vendor adapter not included"}
@router.post("/ingest")
async def ingest(frame:TelemetryFrame,user:str=Depends(require)):
    async with _lock:
        if _frames and frame.timestamp<=_frames[-1].timestamp:
            raise HTTPException(409,"Timestamps must increase strictly")
        _frames.append(frame)
        case=PatientTelemetry(baseline=PatientBaseline(),frames=list(_frames))
        event={"type":"telemetry","frame":frame.model_dump(mode="json"),"assessment":analyze(case)}
        for queue in list(_clients):
            if queue.full():
                try:queue.get_nowait()
                except asyncio.QueueEmpty:pass
            queue.put_nowait(event)
    return {"accepted":True,"buffered_frames":len(_frames),"research_only":True}
@router.websocket("/stream")
async def stream(ws:WebSocket):
    if not websocket_authorized(ws):
        await ws.close(code=1008)
        return
    await ws.accept()
    queue=asyncio.Queue(maxsize=10)
    _clients.add(queue)
    try:
        await ws.send_json({"type":"status","mode":"RESEARCH_ONLY","message":"De-identified telemetry stream; no device control"})
        while True:await ws.send_json(await queue.get())
    except (WebSocketDisconnect,RuntimeError):
        pass
    finally:_clients.discard(queue)
