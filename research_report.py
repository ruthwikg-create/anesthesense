from datetime import timezone
from agent import analyze
from safety import DISCLAIMER
def retrospective_report(case,case_id="DEMO-001",source="Synthetic demonstration"):
    frames=sorted(case.frames,key=lambda f:f.timestamp)
    assessments=[analyze(case.model_copy(update={"frames":frames[:i+1]})) for i in range(len(frames))]
    levels={"STABLE":0,"LOW":1,"MODERATE":2,"HIGH":3,"CRITICAL":4}
    valid_maps=[f.map_value for f in frames if f.map_value is not None]
    events=[{"timestamp":f.timestamp.isoformat(),"risk":a["risk_level"],"rules":[r["code"] for r in a["rules"]]} for f,a in zip(frames,assessments) if a["rules"]]
    return {"case_summary":{"case_id":case_id,"source":source,"duration_minutes":round((frames[-1].timestamp-frames[0].timestamp).total_seconds()/60,2),"peak_risk":max((a["risk_level"] for a in assessments),key=levels.get)},"data_quality":{"frames":len(frames),"missing_map_percent":round(100*(len(frames)-len(valid_maps))/len(frames),2),"latest_signal_quality":assessments[-1]["signal_quality"]},"physiological_summary":{"minimum_map":min(valid_maps) if valid_maps else None,"maximum_map":max(valid_maps) if valid_maps else None},"forecast":assessments[-1]["forecast"],"risk_assessment":assessments[-1]["risk_level"],"deterministic_safety_rules":assessments[-1]["rules"],"haii":assessments[-1]["haii"],"contributing_factors":assessments[-1]["contributing_factors"],"event_timeline":events,"retrospective_metrics":{"alerted_frames":len(events),"forecast_mae":None,"forecast_rmse":None,"note":"Forecast accuracy requires held-out future observations; not clinically validated."},"audit":{"rule_version":assessments[-1]["versions"]["rules"],"model_version":assessments[-1]["versions"]["forecast"],"ai_availability":"disabled","safety_override":assessments[-1]["deterministic_override"]},"safety_boundary":DISCLAIMER}
