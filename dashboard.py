import json
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from agent import analyze
from simulation import simulate,SCENARIOS
from patient_replay import parse_csv,normalized_csv
from safety import DISCLAIMER
st.set_page_config(page_title="AnestheSense | Research Workstation",layout="wide",page_icon="🫀")
st.markdown("""<style>.stApp{background:#0b1420;color:#e6edf5}div[data-testid="stMetric"]{background:#152437;border:1px solid #294055;border-radius:8px;padding:14px}</style>""",unsafe_allow_html=True)
st.title("ANESTHESENSE")
st.caption("Transparent Intraoperative Hemodynamic Early Warning • Research Workstation")
st.warning(DISCLAIMER)
tabs=st.tabs(["CASE","DATA","VERIFY","MONITOR","ANALYSIS","REPORT"])
with tabs[0]:
    case_id=st.text_input("Research case ID","DEMO-001")
    phase=st.selectbox("Surgical phase",["MAINTENANCE","INDUCTION","EMERGENCE"])
with tabs[1]:
    source=st.radio("Source",["Synthetic demonstration","De-identified CSV"])
    if source=="Synthetic demonstration":
        scenario=st.selectbox("Scenario",list(SCENARIOS))
        minutes=st.slider("Duration (minutes)",3,120,30)
        case=simulate(scenario,minutes)
        st.info("Synthetic demonstration data — not patient data.")
        metadata={"source":"Synthetic demonstration","scenario":scenario}
    else:
        upload=st.file_uploader("Upload de-identified CSV (maximum 10 MB)",type=["csv","txt"])
        case=None;metadata={}
        if upload:
            try:
                parsed=parse_csv(upload.getvalue())
                case=parsed["case"]
                metadata={k:v for k,v in parsed.items() if k!="case"}
                st.success(f"Loaded {metadata['rows_used']} rows; skipped {metadata['rows_skipped']}")
                st.json(metadata)
            except ValueError as e:st.error(str(e))
    if case is not None:
        case.surgical_phase=phase
        st.session_state["case"]=case.model_dump(mode="json")
        st.session_state["metadata"]=metadata
        st.download_button("Download normalized CSV",normalized_csv(case.frames),file_name="anesthesense_normalized.csv",mime="text/csv")
with tabs[2]:
    raw=st.session_state.get("case")
    if raw:
        from schema import PatientTelemetry
        case=PatientTelemetry.model_validate(raw)
        st.write("Data source:",st.session_state.get("metadata",{}).get("source","CSV"))
        st.dataframe(pd.DataFrame([f.model_dump(mode="json") for f in case.frames]).head(30),use_container_width=True)
        verified=st.checkbox("I verified this is research/demo or appropriately de-identified data")
        st.session_state["verified"]=verified
    else:st.info("Load a dataset in DATA.")
with tabs[3]:
    if st.session_state.get("verified") and st.session_state.get("case"):
        from schema import PatientTelemetry
        case=PatientTelemetry.model_validate(st.session_state["case"])
        result=analyze(case)
        latest=case.frames[-1]
        st.subheader("Live vitals • replay snapshot")
        keys=["MAP","HR","SBP","DBP","SpO2","EtCO2","SVV","CVP","BIS","TOF_ratio"]
        columns=st.columns(5)
        for i,k in enumerate(keys):
            value=latest.map_value if k=="MAP" else getattr(latest,k)
            columns[i%5].metric(k,round(value,1) if value is not None else "N/A")
        st.subheader("Hemodynamic trajectory")
        xs=[(f.timestamp-case.frames[0].timestamp).total_seconds()/60 for f in case.frames]
        ys=[f.map_value for f in case.frames]
        fig=go.Figure()
        fig.add_trace(go.Scatter(x=xs,y=ys,name="Measured/derived MAP",mode="lines+markers",line_color="#55c6e8"))
        for v,name,color in [(65,"Research target","#f2ba57"),(55,"Research critical","#ee7070")]:
            fig.add_hline(y=v,line_dash="dash",line_color=color,annotation_text=name)
        fc=result["forecast"]
        if fc["predicted_map_10"] is not None:
            fig.add_trace(go.Scatter(x=[xs[-1],xs[-1]+10,xs[-1]+15],y=[ys[-1],fc["predicted_map_10"],fc["predicted_map_15"]],mode="lines+markers",line_dash="dot",name="Prototype forecast",line_color="#cba7ff"))
        fig.update_layout(template="plotly_dark",paper_bgcolor="#0b1420",plot_bgcolor="#122033",xaxis_title="Minutes",yaxis_title="MAP (mmHg)",height=410)
        st.plotly_chart(fig,use_container_width=True)
        st.metric("Current risk",result["risk_level"])
        st.write("Signal quality:",result["signal_quality"])
        st.write("Trajectory:",fc["trajectory"])
        st.write(result["explanation"])
    else:st.info("Load and verify data first.")
with tabs[4]:
    if st.session_state.get("verified") and st.session_state.get("case"):
        from schema import PatientTelemetry
        case=PatientTelemetry.model_validate(st.session_state["case"])
        if st.button("ANALYZE CSV NOW / ANALYZE DATA",type="primary"):
            st.session_state["assessment"]=analyze(case)
        if "assessment" in st.session_state:
            a=st.session_state["assessment"]
            st.subheader("Deterministic assessment")
            st.json({"risk":a["risk_level"],"rules":a["rules"],"derived":a["derived"],"forecast":a["forecast"],"haii":a["haii"],"quality":a["signal_quality"]})
            st.caption("HAII-style score: Research/demo composite — not clinically validated.")
    else:st.info("Verify data first.")
with tabs[5]:
    if st.session_state.get("verified") and st.session_state.get("case"):
        from schema import PatientTelemetry
        case=PatientTelemetry.model_validate(st.session_state["case"])
        assessment=analyze(case)
        report={"case_id":case_id,"source":st.session_state.get("metadata",{}),"rows":len(case.frames),"minimum_map":min((f.map_value for f in case.frames if f.map_value is not None),default=None),"assessment":assessment,"safety_boundary":DISCLAIMER}
        st.subheader("Retrospective research report")
        st.json(report)
        st.download_button("Download audit JSON",json.dumps(report,indent=2,default=str),file_name="anesthesense_audit.json",mime="application/json")
    else:st.info("Verify data first.")
