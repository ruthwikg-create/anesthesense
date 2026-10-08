import numpy as np

VERSION = "0.1-research"
def forecast(frames):
    points = [(f.timestamp, f.map_value) for f in frames if f.map_value is not None]
    if len(points) < 3:
        return {"trajectory":"INSUFFICIENT_DATA","predicted_map_10":None,"predicted_map_15":None,"slope":None,"acceleration":None,"volatility":None,"trend_strength":None}
    points = points[-30:]
    x = np.array([(t-points[0][0]).total_seconds()/60 for t,_ in points],dtype=float)
    y = np.array([v for _,v in points],dtype=float)
    if len(set(x)) != len(x) or np.ptp(x) == 0:
        return {"trajectory":"INSUFFICIENT_DATA","predicted_map_10":None,"predicted_map_15":None,"slope":None,"acceleration":None,"volatility":None,"trend_strength":None}
    slope = float(np.polyfit(x,y,1)[0])
    residual = y - np.polyval(np.polyfit(x,y,1),x)
    acceleration = float(np.polyfit(x,np.gradient(y,x),1)[0]) if len(x)>=4 else 0.0
    p10 = float(np.clip(y[-1]+10*slope,0,250))
    p15 = float(np.clip(y[-1]+15*slope,0,250))
    trajectory = ("CRITICAL_DECLINE" if p10<55 else "HIGH_RISK_DECLINE" if p10<65 and slope<0 else "DECLINING" if slope<-.3 else "RECOVERING" if slope>.3 else "STABLE")
    return {"trajectory":trajectory,"predicted_map_10":round(p10,1),"predicted_map_15":round(p15,1),"slope":round(slope,3),"acceleration":round(acceleration,3),"volatility":round(float(np.std(residual)),2),"trend_strength":round(float(abs(np.corrcoef(x,y)[0,1])) if np.std(y)>0 else 0,2)}
