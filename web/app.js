"use strict";
const $=id=>document.getElementById(id), API="/api/v1", keys=[["MAP","mmHg"],["HR","bpm"],["SBP","mmHg"],["DBP","mmHg"],["SpO2","%"],["EtCO2","mmHg"],["SVV","%"],["CVP","mmHg"],["BIS","index"],["TOF_ratio","ratio"]];
let dataset=null,assessment=null,metadata=null,index=0,timer=null,verified=false,liveSocket=null;
const escapeHTML=s=>String(s).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
async function request(path,options={}){const res=await fetch(path,options);let data;try{data=await res.json()}catch{throw Error("Backend returned an unreadable response")}if(!res.ok)throw Error(typeof data.detail==="string"?data.detail:JSON.stringify(data.detail||data));return data}
function post(path,body){return request(API+path,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)})}
function currentCase(){if(!dataset)return null;return {...dataset,surgical_phase:$("phase").value,frames:dataset.frames.slice(0,index+1)}}
function fmt(v,d=1){return v==null||!Number.isFinite(Number(v))?"—":Number(v).toFixed(d)}
function showError(err){$("explanation").textContent="Unable to analyze: "+err.message;$("api-status").textContent="Backend unavailable"}
function changeView(name){document.querySelectorAll(".view").forEach(e=>e.classList.toggle("active",e.id===name));document.querySelectorAll("#nav button").forEach(e=>e.classList.toggle("active",e.dataset.view===name));$("page-title").textContent=({monitor:"Patient Monitoring",data:"Data & Replay",analysis:"Trajectory Analysis",report:"Research Report & Audit",equipment:"Equipment Integration"})[name]}
document.querySelectorAll("#nav button").forEach(b=>b.onclick=()=>changeView(b.dataset.view));
function updateVitals(frame){$("vitals").innerHTML=keys.map(([key,unit])=>{const v=key==="MAP"?(frame.MAP??(frame.SBP!=null&&frame.DBP!=null?frame.DBP+(frame.SBP-frame.DBP)/3:null)):frame[key];const source=key==="MAP"?(frame.MAP!=null?"MEASURED":"CALCULATED"):"SOURCE VALUE";return '<div class="vital"><div class="name">'+key+'</div><div class="number">'+fmt(v,key==="TOF_ratio"?2:1)+' <span class="unit">'+unit+'</span></div><div class="source">'+source+'</div></div>'}).join("")}
function drawChart(){const canvas=$("map-chart"),rect=canvas.getBoundingClientRect(),ratio=window.devicePixelRatio||1;canvas.width=Math.max(300,rect.width*ratio);canvas.height=Math.max(180,rect.height*ratio);const ctx=canvas.getContext("2d");ctx.scale(ratio,ratio);const w=canvas.width/ratio,h=canvas.height/ratio,p={l:45,r:16,t:18,b:34};ctx.clearRect(0,0,w,h);const frames=dataset?.frames.slice(0,index+1)||[];if(!frames.length)return;const start=new Date(frames[0].timestamp).getTime(),xvals=frames.map(f=>(new Date(f.timestamp).getTime()-start)/60000),values=frames.map(f=>f.MAP??(f.SBP!=null&&f.DBP!=null?f.DBP+(f.SBP-f.DBP)/3:null));const maxX=Math.max(20,xvals.at(-1)+15),minY=Math.max(0,Math.min(45,...values.filter(v=>v!=null))-8),maxY=Math.max(105,...values.filter(v=>v!=null))+7;const x=v=>p.l+v/maxX*(w-p.l-p.r),y=v=>h-p.b-(v-minY)/(maxY-minY)*(h-p.t-p.b);ctx.font="11px sans-serif";ctx.strokeStyle="#27394b";ctx.fillStyle="#8da6ba";for(let v=50;v<=110;v+=10){if(v<minY||v>maxY)continue;ctx.beginPath();ctx.moveTo(p.l,y(v));ctx.lineTo(w-p.r,y(v));ctx.stroke();ctx.fillText(String(v),8,y(v)+4)}for(let i=0;i<=5;i++){const v=i*maxX/5;ctx.fillText(v.toFixed(0),x(v)-5,h-10)}function line(points,color,dashed=false){ctx.strokeStyle=color;ctx.lineWidth=2;ctx.setLineDash(dashed?[6,5]:[]);ctx.beginPath();let active=false;for(const [a,b] of points){if(b==null){active=false;continue}if(!active){ctx.moveTo(x(a),y(b));active=true}else ctx.lineTo(x(a),y(b))}ctx.stroke();ctx.setLineDash([])}line([[0,65],[maxX,65]],"#e1b15c",true);line([[0,55],[maxX,55]],"#e56e73",true);line(xvals.map((v,i)=>[v,values[i]]),"#4dbcd9");const f=assessment?.forecast;if(f?.predicted_map_10!=null){line([[xvals.at(-1),values.at(-1)],[xvals.at(-1)+10,f.predicted_map_10],[xvals.at(-1)+15,f.predicted_map_15]],"#b8a3f4",true)}}
async function render(){if(!dataset)return;const payload=currentCase();try{assessment=await post("/predict",payload);const frame=payload.frames.at(-1);updateVitals(frame);$("risk-level").textContent=assessment.risk_level;$("risk-level").className="risk-value "+assessment.risk_level.toLowerCase();$("trajectory").textContent=assessment.forecast.trajectory.replaceAll("_"," ");$("forecast-10").textContent=fmt(assessment.forecast.predicted_map_10);$("haii").textContent=fmt(assessment.haii.score)+" / 100";$("coverage").textContent=Math.round(assessment.haii.weight_coverage*100)+"% signal weight coverage • unvalidated";$("quality").textContent=assessment.signal_quality;$("frame-time").textContent="Frame "+(index+1)+" / "+dataset.frames.length+" • "+(metadata?.source||"Synthetic demonstration");$("explanation").textContent=assessment.explanation;$("rules").innerHTML=assessment.rules.length?assessment.rules.map(r=>'<div class="rule '+(r.severity==="CRITICAL"?"critical":"")+'"><strong>'+escapeHTML(r.code)+'</strong><div class="subtle">'+escapeHTML(r.explanation)+'</div></div>').join(""):'<span class="subtle">No deterministic rule triggered</span>';$("analysis-output").textContent=JSON.stringify(assessment,null,2);$("trends").innerHTML=["MAP","HR","SpO2","EtCO2","SVV","BIS"].map(k=>{const vals=payload.frames.map(f=>k==="MAP"?(f.MAP??(f.SBP!=null&&f.DBP!=null?f.DBP+(f.SBP-f.DBP)/3:null)):f[k]).filter(v=>v!=null);return '<div class="trend-item">'+k+'<strong>'+fmt(vals.at(-1))+'</strong><span class="subtle">'+(vals.length>1?fmt(vals.at(-1)-vals[0])+" change since start":"Insufficient history")+'</span></div>'}).join("");drawChart();updateReport()}catch(e){showError(e)}}
async function start(){disconnectLive();clearInterval(timer);$("start").disabled=true;try{const result=await post("/simulate",{scenario:$("scenario").value,minutes:30});dataset=result;metadata={source:"Synthetic demonstration",scenario:$("scenario").value};index=0;verified=true;await render();timer=setInterval(async()=>{if(!dataset||index>=dataset.frames.length-1){clearInterval(timer);return}index++;await render()},1000)}catch(e){showError(e)}finally{$("start").disabled=false}}
$("start").onclick=start;$("pause").onclick=()=>{if(timer){clearInterval(timer);timer=null;$("pause").textContent="▶ Resume"}else if(dataset){timer=setInterval(async()=>{if(index>=dataset.frames.length-1){clearInterval(timer);timer=null;return}index++;await render()},1000);$("pause").textContent="Ⅱ Pause"}};$("reset").onclick=()=>{clearInterval(timer);timer=null;index=0;render()};$("phase").onchange=render;
function download(name,content,type){const a=document.createElement("a"),url=URL.createObjectURL(new Blob([content],{type}));a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)}
function normalized(){if(!dataset)return "";const cols=["minute","MAP","HR","SBP","DBP","SVV","EtCO2","SpO2","CVP","BIS","TOF_twitches","TOF_ratio"];const t=new Date(dataset.frames[0].timestamp).getTime();return [cols.join(","),...dataset.frames.map(f=>cols.map(k=>{let v=k==="minute"?(new Date(f.timestamp).getTime()-t)/60000:k==="MAP"?(f.MAP??(f.SBP!=null&&f.DBP!=null?f.DBP+(f.SBP-f.DBP)/3:null)):f[k];return v==null?"":v}).join(","))].join("\n")}
$("csv-file").onchange=async e=>{clearInterval(timer);const file=e.target.files[0];if(!file)return;verified=false;$("verify").disabled=true;$("analyze-csv").disabled=true;try{if(file.size>10_000_000)throw Error("File exceeds 10 MB");const bytes=new Uint8Array(await file.arrayBuffer());let text;try{text=new TextDecoder(bytes[0]===255&&bytes[1]===254?"utf-16le":bytes[0]===254&&bytes[1]===255?"utf-16be":"utf-8",{fatal:true}).decode(bytes)}catch{text=new TextDecoder("windows-1252").decode(bytes)}text=text.replace(/^\uFEFF/,"");const rows=text.trim().split(/\r?\n/);if(rows.length<2)throw Error("No data rows found");const header=rows[0],delimiter=[",",";","\t","|"].sort((a,b)=>header.split(b).length-header.split(a).length)[0],columns=header.split(delimiter).map(x=>x.trim().toLowerCase().replace(/[^a-z0-9]/g,""));const aliases={MAP:["map","meanarterialpressure"],SBP:["sbp","systolic","systolicbp"],DBP:["dbp","diastolic","diastolicbp"],HR:["hr","heartrate","pulse"],SpO2:["spo2","oxygensaturation"],EtCO2:["etco2","endtidalco2"],SVV:["svv"],CVP:["cvp"],BIS:["bis","bispectralindex"],TOF_ratio:["tofratio"],TOF_twitches:["toftwitches","tof"],minute:["minute","minutes","time"]};const mapping=Object.fromEntries(Object.entries(aliases).map(([k,v])=>[k,columns.findIndex(c=>v.includes(c))]));if(mapping.HR<0||(mapping.MAP<0&&(mapping.SBP<0||mapping.DBP<0)))throw Error("Required HR and MAP or SBP/DBP columns missing");let skipped=0,frames=[];for(let i=1;i<rows.length;i++){const cols=rows[i].split(delimiter);try{const values={};for(const k of Object.keys(aliases)){if(k==="minute")continue;const raw=mapping[k]>=0?cols[mapping[k]]?.trim():"";values[k]=raw?Number(raw):null;if(values[k]!=null&&!Number.isFinite(values[k]))throw Error("Invalid number")}if(values.SBP!=null&&values.DBP!=null&&values.SBP<=values.DBP)throw Error("Invalid BP");if(values.HR==null||(values.MAP==null&&(values.SBP==null||values.DBP==null)))throw Error("Missing required value");const minute=mapping.minute>=0?Number(cols[mapping.minute]):i-1;if(!Number.isFinite(minute))throw Error("Invalid time");frames.push({timestamp:new Date(Date.UTC(2025,0,1)+minute*60000).toISOString(),...values})}catch{skipped++}}if(!frames.length)throw Error("No valid rows");frames.sort((a,b)=>a.timestamp.localeCompare(b.timestamp));const first=frames[0];dataset={baseline:{baseline_map:first.MAP??(first.DBP+(first.SBP-first.DBP)/3)},surgical_phase:$("phase").value,frames};metadata={source:"De-identified CSV",filename:file.name,rows_read:rows.length-1,rows_used:frames.length,rows_skipped:skipped,column_mapping:mapping};index=frames.length-1;$("import-info").textContent=JSON.stringify(metadata,null,2);$("preview").innerHTML="<table><thead><tr>"+Object.keys(first).map(k=>"<th>"+escapeHTML(k)+"</th>").join("")+"</tr></thead><tbody>"+frames.slice(0,15).map(f=>"<tr>"+Object.values(f).map(v=>"<td>"+escapeHTML(v??"—")+"</td>").join("")+"</tr>").join("")+"</tbody></table>";$("verify").disabled=false;$("export-csv").disabled=false;await render()}catch(err){$("import-info").textContent="Import error: "+err.message}};
$("verify").onclick=()=>{verified=true;$("analyze-csv").disabled=false;$("import-info").textContent+="\nDataset verified for research/demo analysis."};$("analyze-csv").onclick=async()=>{if(!verified)return;await render();changeView("analysis")};$("export-csv").onclick=()=>download("anesthesense_normalized.csv",normalized(),"text/csv");
function reportObject(){if(!dataset||!assessment)return null;const vals=dataset.frames.map(f=>f.MAP??(f.SBP!=null&&f.DBP!=null?f.DBP+(f.SBP-f.DBP)/3:null)).filter(v=>v!=null);return {case_id:$("case-id").value,data_source:metadata,frames_analyzed:index+1,minimum_map:Math.min(...vals),maximum_map:Math.max(...vals),assessment,rule_version:assessment.versions?.rules,ai_status:"disabled",safety_boundary:"Research/demo only; not clinically validated or for patient care."}}
function updateReport(){const r=reportObject();$("report-content").textContent=r?JSON.stringify(r,null,2):"No dataset analyzed."}
function exportReport(){const r=reportObject();if(r)download("anesthesense_audit.json",JSON.stringify(r,null,2),"application/json")}
$("export-top").onclick=exportReport;$("download-report").onclick=exportReport;window.addEventListener("resize",drawChart);
async function initAuth(){
 try{
 const status=await request("/api/v1/auth/status");
 if(!status.configured){$("login-error").textContent="Administrator setup required: configure login environment variables.";return}
 if(status.authenticated){showWorkstation();return}
 }catch(e){$("login-error").textContent="Unable to reach backend: "+e.message}
}
function showWorkstation(){
 loadEquipment();
 $("login-screen").hidden=true;$("workstation").hidden=false;
 request("/health").then(()=>{$("api-status").textContent="Backend online"}).catch(()=>{$("api-status").textContent="Backend unavailable"});
 start();
}
$("login-form").onsubmit=async e=>{
 e.preventDefault();$("login-error").textContent="";
 try{
 await request("/api/v1/auth/login",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({username:$("login-user").value,password:$("login-password").value})});
 $("login-password").value="";showWorkstation()
 }catch(err){$("login-error").textContent=err.message}
};
$("logout").onclick=async()=>{disconnectLive();
 clearInterval(timer);timer=null;dataset=null;assessment=null;
 try{await request("/api/v1/auth/logout",{method:"POST"})}catch{}
 $("workstation").hidden=true;$("login-screen").hidden=false;
};
function disconnectLive(){
 if(liveSocket){const ws=liveSocket;liveSocket=null;ws.close()}
 $("live-status").textContent="Feed disconnected";
 $("live-connect").textContent="◉ Connect research feed";
}
$("live-connect").onclick=()=>{
 if(liveSocket){disconnectLive();return}
 clearInterval(timer);timer=null;
 const protocol=location.protocol==="https:"?"wss:":"ws:";
 const ws=new WebSocket(protocol+"//"+location.host+"/api/v1/telemetry/stream");
 liveSocket=ws;$("live-status").textContent="Connecting…";
 ws.onopen=()=>{$("live-status").textContent="Research feed connected";$("live-connect").textContent="Disconnect feed"};
 ws.onmessage=async event=>{
   try{
     const msg=JSON.parse(event.data);
     if(msg.type!=="telemetry")return;
     if(!dataset||metadata?.source!=="Authorized research telemetry"){
       dataset={baseline:{},surgical_phase:$("phase").value,frames:[]};
       metadata={source:"Authorized research telemetry"};
     }
     dataset.frames.push(msg.frame);
     if(dataset.frames.length>240)dataset.frames.shift();
     index=dataset.frames.length-1;
     await render();
   }catch(e){$("live-status").textContent="Stream data error: "+e.message}
 };
 ws.onerror=()=>{$("live-status").textContent="Research feed connection error"};
 ws.onclose=()=>{if(liveSocket===ws){liveSocket=null;$("live-status").textContent="Feed disconnected";$("live-connect").textContent="◉ Connect research feed"}};
};
initAuth();

let equipment=[];
async function loadEquipment(){
 try{const result=await request("/api/v1/devices/catalog");equipment=result.devices;renderEquipment()}
 catch(e){$("device-list").textContent="Equipment catalog unavailable: "+e.message}
}
function renderEquipment(){
 const query=($("device-search")?.value||"").toLowerCase();
 const matches=equipment.filter(d=>[d.manufacturer,d.family,d.category,...d.signals].join(" ").toLowerCase().includes(query));
 $("device-list").innerHTML=matches.map(d=>'<div class="device-card"><div class="caption">'+escapeHTML(d.category.replaceAll("_"," ").toUpperCase())+'</div><h3>'+escapeHTML(d.manufacturer)+' · '+escapeHTML(d.family)+'</h3><div class="subtle">'+escapeHTML(d.signals.join(" · "))+'</div><p class="subtle">Interface: '+escapeHTML(d.connection_options.join(", "))+'</p><div class="pill muted">'+(d.integration_status==="normalized_adapter"?"NORMALIZED ADAPTER ONLY":"PLANNED / NOT CONNECTED")+'</div><p class="subtle">'+escapeHTML(d.validation_note)+'</p></div>').join("")||'<p class="subtle">No matching equipment</p>';
}
$("device-search").oninput=renderEquipment;
