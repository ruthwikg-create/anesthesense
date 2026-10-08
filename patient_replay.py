import csv,io,hashlib,statistics
from datetime import datetime,timedelta,timezone
from schema import TelemetryFrame,PatientTelemetry,PatientBaseline
ALIASES={"MAP":["map","meanarterialpressure"],"SBP":["sbp","systolic","systolicbp","arterialsystolic"],"DBP":["dbp","diastolic","diastolicbp"],"HR":["hr","heartrate","pulse"],"SpO2":["spo2","oxygensaturation"],"EtCO2":["etco2","endtidalco2"],"SVV":["svv"],"CVP":["cvp"],"BIS":["bis","bispectralindex"],"TOF_twitches":["toftwitches","tof"],"TOF_ratio":["tofratio"],"minute":["minute","minutes","time"]}
FIELDS=["minute","MAP","HR","SBP","DBP","SVV","EtCO2","SpO2","CVP","BIS","TOF_twitches","TOF_ratio"]
def parse_csv(data:bytes):
    if len(data)>10_000_000: raise ValueError("CSV exceeds 10 MB limit")
    decoded=None
    for enc in (["utf-16"] if data.startswith((b"\\xff\\xfe",b"\\xfe\\xff")) else ["utf-8-sig","utf-16","cp1252"]):
        try:
            decoded=data.decode(enc)
            if "\\x00" in decoded: continue
            break
        except UnicodeError: continue
    if decoded is None or not decoded.strip(): raise ValueError("CSV is empty or unreadable")
    sample=decoded[:4096]
    try: dialect=csv.Sniffer().sniff(sample,delimiters=",;\\t|")
    except csv.Error: dialect=csv.excel
    reader=csv.DictReader(io.StringIO(decoded),dialect=dialect)
    if not reader.fieldnames: raise ValueError("CSV has no header")
    normalize=lambda s:"".join(c for c in str(s).lower() if c.isalnum())
    mapping={field:next((col for col in reader.fieldnames if normalize(col) in aliases),None) for field,aliases in ALIASES.items()}
    if not mapping["HR"] or not (mapping["MAP"] or (mapping["SBP"] and mapping["DBP"])): raise ValueError("Required HR and MAP or SBP/DBP columns not detected")
    frames=[];read=0;skipped=0
    origin=datetime(2025,1,1,tzinfo=timezone.utc)
    for row in reader:
        read+=1
        try:
            values={}
            for field in ALIASES:
                if field=="minute":continue
                raw=row.get(mapping[field]) if mapping[field] else None
                values[field]=float(raw) if raw is not None and raw.strip() else None
            minute=float(row[mapping["minute"]]) if mapping["minute"] and row.get(mapping["minute"]) else read-1
            frame=TelemetryFrame(timestamp=origin+timedelta(minutes=minute),**values)
            if frame.map_value is None or frame.HR is None:raise ValueError("Missing required values")
            frames.append(frame)
        except (ValueError,TypeError,OverflowError,AttributeError):skipped+=1
    if not frames:raise ValueError("No valid CSV rows")
    frames.sort(key=lambda f:f.timestamp)
    intervals=[(b.timestamp-a.timestamp).total_seconds()/60 for a,b in zip(frames,frames[1:]) if b.timestamp>a.timestamp]
    return {"case":PatientTelemetry(baseline=PatientBaseline(baseline_map=frames[0].map_value),frames=frames),"sha256":hashlib.sha256(data).hexdigest(),"mapping":mapping,"rows_read":read,"rows_used":len(frames),"rows_skipped":skipped,"sampling_interval_minutes":statistics.median(intervals) if intervals else None,"missing_optional_signals":[k for k in ("SpO2","EtCO2","BIS","SVV","CVP") if all(getattr(f,k) is None for f in frames)]}
def normalized_csv(frames):
    out=io.StringIO();writer=csv.DictWriter(out,fieldnames=FIELDS);writer.writeheader()
    first=frames[0].timestamp
    for f in frames:
        row={k:getattr(f,k) for k in FIELDS if k!="minute"}
        row["minute"]=round((f.timestamp-first).total_seconds()/60,4)
        if row["MAP"] is None:row["MAP"]=f.map_value
        writer.writerow({k:"" if v is None else v for k,v in row.items()})
    return out.getvalue()
