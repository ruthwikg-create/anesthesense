"""Research-only login sessions. Set credentials via environment variables; never ship defaults."""
import os,hmac,hashlib,base64,json,time,secrets
from fastapi import HTTPException,Request,WebSocket
from fastapi.security.utils import get_authorization_scheme_param
SECRET=os.getenv("ANESTHESENSE_SESSION_SECRET","")
USER=os.getenv("ANESTHESENSE_USERNAME","")
PASSWORD_HASH=os.getenv("ANESTHESENSE_PASSWORD_SHA256","")
TTL=3600*8
def configured():
    return len(SECRET)>=32 and bool(USER) and len(PASSWORD_HASH)==64
def password_matches(username,password):
    if not configured():return False
    digest=hashlib.sha256(password.encode()).hexdigest()
    return hmac.compare_digest(username,USER) and hmac.compare_digest(digest,PASSWORD_HASH)
def _sign(payload):
    data=base64.urlsafe_b64encode(json.dumps(payload,separators=(",",":")).encode()).decode().rstrip("=")
    mac=hmac.new(SECRET.encode(),data.encode(),hashlib.sha256).hexdigest()
    return data+"."+mac
def issue(username):
    return _sign({"sub":username,"exp":int(time.time())+TTL,"nonce":secrets.token_hex(8)})
def verify(token):
    if not configured() or not token or "." not in token:return False
    try:
        data,mac=token.rsplit(".",1)
        if not hmac.compare_digest(hmac.new(SECRET.encode(),data.encode(),hashlib.sha256).hexdigest(),mac):return False
        obj=json.loads(base64.urlsafe_b64decode(data+"="*(-len(data)%4)))
        return obj.get("sub")==USER and int(obj.get("exp",0))>time.time()
    except (ValueError,TypeError,KeyError):return False
def require(request:Request):
    if not verify(request.cookies.get("anesthesense_session")):
        raise HTTPException(401,"Login required")
    return USER
def websocket_authorized(ws:WebSocket):
    return verify(ws.cookies.get("anesthesense_session"))
