VERSION = "research-rules-0.1"
DISCLAIMER = "AnestheSense is a research/demo clinical decision-support prototype. It has not been clinically validated and is not intended for patient care, diagnosis, medication dosing, or autonomous treatment. Thresholds and scores are configurable research rules and must not substitute for validated clinical protocols or professional judgment."
WEIGHTS = {"MAP":.30,"HR":.15,"SpO2":.25,"EtCO2":.15,"BIS":.15}
def metrics(frame,baseline):
    m = frame.map_value
    sbp,dbp,hr = frame.SBP,frame.DBP,frame.HR
    b = baseline.baseline_map
    if b is None and baseline.baseline_sbp is not None and baseline.baseline_dbp is not None and baseline.baseline_sbp>baseline.baseline_dbp:
        b = baseline.baseline_dbp+(baseline.baseline_sbp-baseline.baseline_dbp)/3
    return {"calculated_map":m if frame.MAP is None else None,"map_current":m,"pulse_pressure":sbp-dbp if sbp is not None and dbp is not None else None,"shock_index":hr/sbp if hr is not None and sbp is not None and sbp>0 else None,"map_baseline":b,"map_deviation_percent":(m-b)/b*100 if m is not None and b is not None and b>0 else None,"tof_ratio":frame.TOF_ratio}
def deterministic_rule_check(frame,derived,phase):
    rules=[]
    def add(code,severity,signal,value,threshold,explanation):
        rules.append({"code":code,"severity":severity,"signal":signal,"value":round(value,2),"threshold":threshold,"explanation":explanation,"timestamp":frame.timestamp.isoformat()})
    m=derived["map_current"]
    if m is not None and m<55: add("CRITICAL_HYPOTENSION","CRITICAL","MAP",m,"<55 mmHg","MAP below research critical threshold.")
    d=derived["map_deviation_percent"]
    if d is not None and d<=-20: add("BASELINE_MAP_DROP","HIGH","MAP deviation",d,"<=-20%","MAP has fallen at least 20% from baseline.")
    if frame.SpO2 is not None and frame.SpO2<90: add("CRITICAL_HYPOXEMIA","CRITICAL","SpO2",frame.SpO2,"<90%","Oxygen saturation below research threshold.")
    if phase=="MAINTENANCE" and frame.BIS is not None and frame.BIS>65: add("AWARENESS_RISK","HIGH","BIS",frame.BIS,">65","BIS exceeds research maintenance display threshold; not a diagnosis.")
    s=derived["shock_index"]
    if s is not None and s>.9: add("ELEVATED_SHOCK_INDEX","HIGH","Shock index",s,">0.9","Calculated shock index above research threshold.")
    return rules
def haii(frame):
    values={"MAP":frame.map_value,"HR":frame.HR,"SpO2":frame.SpO2,"EtCO2":frame.EtCO2,"BIS":frame.BIS}
    def penalty(k,v):
        if k=="MAP": return min(1,max(0,(75-v)/30))
        if k=="HR": return min(1,max(0,(v-90)/70,(50-v)/40))
        if k=="SpO2": return min(1,max(0,(97-v)/12))
        if k=="EtCO2": return min(1,max(0,(30-v)/15,(v-45)/20))
        return min(1,max(0,(40-v)/30,(v-60)/30))
    covered=sum(WEIGHTS[k] for k,v in values.items() if v is not None)
    return {"score":round(sum(WEIGHTS[k]*penalty(k,v) for k,v in values.items() if v is not None)/covered*100,1) if covered else None,"weight_coverage":round(covered,2),"contributions":{k:round(penalty(k,v)*100,1) for k,v in values.items() if v is not None},"missing_signals":[k for k,v in values.items() if v is None],"disclaimer":"Research/demo composite — not clinically validated."}
