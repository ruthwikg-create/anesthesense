from datetime import datetime,timedelta,timezone
from schema import PatientTelemetry,PatientBaseline,TelemetryFrame
SCENARIOS={"Normotensive":(0,0),"Vasodilation":(-.65,0.3),"Hypovolemia":(-.85,.7),"Hemorrhage":(-1.2,1),"Mixed Shock":(-1.4,1.2),"Hypoxia Stress":(-.4,.5)}
def simulate(scenario="Normotensive",minutes=30):
    if scenario not in SCENARIOS: raise ValueError("Unknown scenario")
    if not 3<=minutes<=240: raise ValueError("minutes must be 3..240")
    decline,hr_rise=SCENARIOS[scenario]
    start=datetime(2025,1,1,tzinfo=timezone.utc)
    frames=[]
    for i in range(minutes+1):
        m=round(80+decline*i+0.6*__import__("math").sin(i*.5),1)
        spo=round(98-(max(0,i-5)*.45 if scenario=="Hypoxia Stress" else 0),1)
        frames.append(TelemetryFrame(timestamp=start+timedelta(minutes=i),MAP=m,SBP=round(m+38,1),DBP=round(m-18,1),HR=round(72+hr_rise*i,1),SpO2=max(70,spo),EtCO2=round(37-.12*i,1),SVV=round(9+.2*i,1),CVP=round(7-.05*i,1),BIS=48))
    return PatientTelemetry(baseline=PatientBaseline(baseline_map=80),frames=frames)
