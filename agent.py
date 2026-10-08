from safety import DISCLAIMER,deterministic_rule_check,metrics,haii
from forecasting import forecast
VERSION="0.1.0"
LEVELS=["STABLE","LOW","MODERATE","HIGH","CRITICAL"]
def analyze(case):
    frames=sorted(case.frames,key=lambda f:f.timestamp)
    latest=frames[-1]
    derived=metrics(latest,case.baseline)
    rules=deterministic_rule_check(latest,derived,case.surgical_phase)
    prediction=forecast(frames)
    composite=haii(latest)
    risk="STABLE"
    if composite["score"] is not None and composite["score"]>=20: risk="LOW"
    if composite["score"] is not None and composite["score"]>=40: risk="MODERATE"
    if prediction["trajectory"] in ("DECLINING","HIGH_RISK_DECLINE","CRITICAL_DECLINE"): risk=max((risk,"MODERATE"),key=LEVELS.index)
    if prediction["predicted_map_10"] is not None and prediction["predicted_map_10"]<65: risk="HIGH"
    for rule in rules: risk=max((risk,rule["severity"]),key=LEVELS.index)
    missing=sum(getattr(latest,k) is None for k in ("HR","SpO2","EtCO2","BIS"))
    quality="POOR" if latest.map_value is None or missing>=3 else "FAIR" if missing else "GOOD"
    factors=[r["explanation"] for r in rules]
    if prediction["slope"] is not None and prediction["slope"]<-.3: factors.append("MAP trajectory is declining.")
    if not factors: factors=["No deterministic safety rule triggered in the available data."]
    return {"risk_level":risk,"safety_status":"RESEARCH ONLY","deterministic_override":[r["code"] for r in rules],"rules":rules,"derived":derived,"forecast":prediction,"haii":composite,"signal_quality":quality,"explanation":" ".join(factors)+" Clinician review recommended; correlate with signal quality and context.","contributing_factors":factors,"disclaimer":DISCLAIMER,"versions":{"software":VERSION,"rules":"research-rules-0.1","forecast":"0.1-research"}}
