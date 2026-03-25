import streamlit as st
import pandas as pd
import re, os, io, pickle, json
from datetime import datetime
import plotly.graph_objects as go
import base64

st.set_page_config(page_title="OCP Manufacturing", layout="wide", initial_sidebar_state="expanded")

# ══════════════════════════════════════════════════════
# CSS — THÈME BLANC PROFESSIONNEL
# ══════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow:wght@300;400;500;600;700&family=Barlow+Condensed:wght@500;600;700;800&display=swap');

:root {
  --green:     #00843D;  --green-dk:  #005C2A;  --green-lt:  #E8F5EE;
  --blue:      #1565C0;  --blue-lt:   #E3EAF8;
  --orange:    #C05A00;  --orange-lt: #FBF0E6;
  --purple:    #6B3FA0;  --purple-lt: #F0EBF8;
  --red:       #C62828;
  --bg:        #F2F4F7;  --white:     #FFFFFF;
  --border:    #E0E4EA;  --border2:   #EEF0F4;
  --text:      #12202E;  --text2:     #4A5568;  --text3:     #94A3B8;
  --sh1: 0 1px 3px rgba(0,0,0,0.07);
  --sh2: 0 4px 16px rgba(0,0,0,0.10);
  --sh3: 0 8px 32px rgba(0,0,0,0.12);
}

html,body,[class*="css"] { font-family:'Barlow',sans-serif !important; color:var(--text); }
.stApp { background:var(--bg) !important; }
.main .block-container { padding:0 1.8rem 2rem 1.8rem !important; max-width:100% !important; }
#MainMenu,footer { visibility:hidden; }
header[data-testid="stHeader"] { background:transparent !important; height:0 !important; }
[data-testid="stDecoration"],.stDeployButton { display:none !important; }
::-webkit-scrollbar{width:4px;height:4px}
::-webkit-scrollbar-track{background:var(--bg)}
::-webkit-scrollbar-thumb{background:var(--border);border-radius:2px}

/* ─── SIDEBAR ─── */
[data-testid="stSidebar"] {
  background:var(--white) !important;
  border-right:1px solid var(--border) !important;
  box-shadow:2px 0 10px rgba(0,0,0,0.06) !important;
}
[data-testid="stSidebar"],[data-testid="stSidebar"]>div {
  width:220px !important; min-width:220px !important; max-width:220px !important;
}
[data-testid="stSidebarContent"] { padding:0 !important; overflow-y:auto !important; }
[data-testid="stSidebarCollapseButton"],
button[data-testid="baseButton-headerNoPadding"] { display:none !important; }
[data-testid="stSidebar"] section,[data-testid="stSidebar"] .block-container { padding:0 !important; }

/* Logo */
.sbl {
  padding:16px 14px 14px 14px; border-bottom:1px solid var(--border2);
  display:flex; align-items:center; gap:10px; background:var(--white);
}
.sbl-box {
  width:38px; height:38px; background:var(--green); border-radius:8px;
  display:flex; align-items:center; justify-content:center;
  font-family:'Barlow Condensed',sans-serif; font-size:15px; font-weight:800;
  color:white; flex-shrink:0; letter-spacing:.3px;
}
.sbl-img { width:38px; height:38px; object-fit:contain; flex-shrink:0; }
.sbl-name { font-family:'Barlow Condensed',sans-serif; font-size:18px; font-weight:800; color:var(--green); line-height:1.1; }
.sbl-sub  { font-size:8px; color:var(--text3); letter-spacing:1.5px; text-transform:uppercase; margin-top:1px; }

/* Nav section label */
.slbl { font-size:8px; font-weight:700; letter-spacing:2px; text-transform:uppercase; color:var(--text3); padding:14px 14px 4px 14px; }
.shr  { height:1px; background:var(--border2); margin:6px 0; }

/* Nav buttons */
[data-testid="stSidebar"] .stButton button {
  width:100% !important; background:transparent !important; border:none !important;
  border-radius:0 !important; color:var(--text2) !important;
  font-family:'Barlow',sans-serif !important; font-size:13px !important; font-weight:500 !important;
  padding:9px 12px 9px 16px !important; text-align:left !important;
  border-left:3px solid transparent !important; white-space:nowrap !important;
  box-shadow:none !important; transition:background .15s,color .15s !important;
}
[data-testid="stSidebar"] .stButton button:hover {
  background:var(--green-lt) !important; color:var(--green) !important;
  border-left-color:rgba(0,132,61,.4) !important;
}
[data-testid="stSidebar"] .stButton button[kind="primary"] {
  background:var(--green-lt) !important; color:var(--green-dk) !important;
  border-left:3px solid var(--green) !important; font-weight:700 !important;
}

/* ─── TOPBAR ─── */
.topbar {
  background:var(--white); border-bottom:1px solid var(--border);
  padding:12px 1.8rem; margin:0 -1.8rem 20px -1.8rem;
  display:flex; align-items:center; justify-content:space-between;
  box-shadow:var(--sh1);
}
.tb-title { font-family:'Barlow Condensed',sans-serif; font-size:20px; font-weight:700; color:var(--text); }
.tb-bread { font-size:11px; color:var(--text3); margin-top:1px; }
.tb-badge {
  background:var(--green-lt); color:var(--green-dk);
  border:1px solid rgba(0,132,61,.2); border-radius:20px;
  padding:4px 14px; font-size:11px; font-weight:600;
}

/* ─── KPI CARDS ─── */
.kcard {
  background:var(--white); border:1px solid var(--border); border-radius:10px;
  padding:18px 20px; box-shadow:var(--sh1);
  transition:transform .18s,box-shadow .18s; position:relative; overflow:hidden;
  box-sizing:border-box;
  display:flex; flex-direction:column; justify-content:space-between;
}
.kcard:hover { transform:translateY(-2px); box-shadow:var(--sh2); }
.kcard::after { content:''; position:absolute; top:0; left:0; right:0; height:3px; border-radius:10px 10px 0 0; }
.kcard.green::after  { background:var(--green); }
.kcard.blue::after   { background:var(--blue); }
.kcard.orange::after { background:var(--orange); }
.kcard.purple::after { background:var(--purple); }
.kc-lbl   { font-size:9px; font-weight:700; letter-spacing:1.4px; text-transform:uppercase; color:var(--text3); }
.kc-val   { font-family:'Barlow Condensed',sans-serif; font-size:34px; font-weight:700; line-height:1; margin:4px 0; }
.kc-val.green  { color:var(--green); }  .kc-val.blue  { color:var(--blue); }
.kc-val.orange { color:var(--orange); } .kc-val.purple{ color:var(--purple); }
.kc-unit  { font-size:13px; font-weight:500; color:var(--text3); margin-left:2px; }
.kc-sub   { font-size:11px; color:var(--text2); }
.kc-extra { font-size:10px; color:var(--text3); margin-top:2px; }

/* ─── KPI DETAIL ROWS ─── */
.kc-detail {
  margin-top:8px; padding-top:8px; border-top:1px solid var(--border2);
  display:flex; flex-direction:column; gap:3px;
}
.kc-detail-row { display:flex; justify-content:space-between; align-items:center; }
.kc-detail-label { font-size:10px; color:var(--text3); }
.kc-detail-value { font-size:10px; font-weight:700; color:var(--text2); }

/* ─── SECTION TITLE ─── */
.stitle {
  font-family:'Barlow Condensed',sans-serif; font-size:13px; font-weight:700;
  letter-spacing:1px; text-transform:uppercase; color:var(--text2);
  margin:20px 0 10px 0; display:flex; align-items:center; gap:8px;
}
.stitle::before { content:''; width:3px; height:14px; background:var(--green); border-radius:2px; display:inline-block; }
.stitle.blue::before { background:var(--blue); }
.stitle.orange::before { background:var(--orange); }
.stitle.purple::before { background:var(--purple); }

/* ─── CARDS génériques ─── */
.card { background:var(--white); border:1px solid var(--border); border-radius:10px; padding:20px; box-shadow:var(--sh1); }
.card-title {
  font-family:'Barlow Condensed',sans-serif; font-size:14px; font-weight:700;
  text-transform:uppercase; letter-spacing:.5px; color:var(--text2);
  margin-bottom:14px; display:flex; align-items:center; gap:6px;
}

/* ─── DECADE CARDS ─── */
.decade-wrap { background:var(--white); border:1px solid var(--border); border-radius:10px; padding:18px 20px; box-shadow:var(--sh1); height:100%; box-sizing:border-box; }
.decade-header { display:flex; align-items:center; justify-content:space-between; margin-bottom:14px; }
.decade-title { font-family:'Barlow Condensed',sans-serif; font-size:15px; font-weight:700; text-transform:uppercase; letter-spacing:.5px; color:var(--text); }
.decade-badge { font-size:9px; font-weight:700; letter-spacing:1px; text-transform:uppercase; padding:2px 8px; border-radius:10px; }
.decade-badge.current { background:var(--green-lt); color:var(--green-dk); }
.decade-badge.past    { background:var(--border2);   color:var(--text3); }
.decade-badge.future  { background:var(--blue-lt);   color:var(--blue); }
.decade-grid { display:flex; gap:8px; }
.decade-block { flex:1; background:var(--bg); border:1px solid var(--border2); border-radius:8px; padding:10px 12px; text-align:center; transition:border-color .15s; }
.decade-block:hover { border-color:var(--green); }
.decade-block.active { background:var(--green-lt); border-color:rgba(0,132,61,.3); }
.decade-block-label { font-size:9px; font-weight:700; letter-spacing:1.5px; text-transform:uppercase; color:var(--text3); margin-bottom:4px; }
.decade-block.active .decade-block-label { color:var(--green-dk); }
.decade-block-val { font-family:'Barlow Condensed',sans-serif; font-size:22px; font-weight:700; line-height:1; color:var(--text); }
.decade-block.active .decade-block-val { color:var(--green); }
.decade-block-unit { font-size:9px; color:var(--text3); margin-top:2px; }
.decade-total-row { margin-top:12px; padding-top:10px; border-top:1px solid var(--border2); display:flex; justify-content:space-between; align-items:center; }
.decade-total-label { font-size:10px; font-weight:700; color:var(--text2); }
.decade-total-val { font-family:'Barlow Condensed',sans-serif; font-size:16px; font-weight:700; color:var(--green); }

/* ─── HISTORIQUE ITEMS ─── */
.hist-item { display:flex; align-items:center; justify-content:space-between; padding:9px 12px; border-radius:7px; border:1px solid var(--border2); background:var(--bg); margin-bottom:6px; transition:border-color .15s; }
.hist-item:hover { border-color:var(--green); }
.hist-item-name { font-size:12px; font-weight:600; color:var(--text); }
.hist-item-date { font-size:10px; color:var(--text3); margin-top:2px; }
.hist-tag { display:inline-block; padding:2px 8px; border-radius:10px; font-size:9px; font-weight:700; letter-spacing:.5px; text-transform:uppercase; }
.hist-tag.jorf  { background:var(--green-lt); color:var(--green-dk); }
.hist-tag.safi  { background:var(--blue-lt);  color:var(--blue); }
.hist-active { width:7px; height:7px; border-radius:50%; background:var(--green); flex-shrink:0; box-shadow:0 0 5px rgba(0,132,61,.5); }
.hist-inactive { width:7px; height:7px; border-radius:50%; background:var(--border); flex-shrink:0; }

/* ─── UPLOAD ZONE ─── */
.upload-zone { background:var(--white); border:1px solid var(--border); border-radius:10px; padding:20px; box-shadow:var(--sh1); }
.upload-zone .zone-title { font-family:'Barlow Condensed',sans-serif; font-size:14px; font-weight:700; text-transform:uppercase; letter-spacing:.5px; color:var(--text2); margin-bottom:4px; display:flex; align-items:center; gap:6px; }
.upload-zone .zone-desc { font-size:11px; color:var(--text3); margin-bottom:14px; }
[data-testid="stFileUploader"] label { font-size:11px !important; color:var(--text2) !important; font-weight:600 !important; }
[data-testid="stFileUploaderDropzone"] { background:var(--bg) !important; border:1.5px dashed var(--border) !important; border-radius:8px !important; }
[data-testid="stFileUploaderDropzone"] p { font-size:11px !important; color:var(--text3) !important; }

/* ─── FILTRE SECTION ─── */
.filter-panel { background:var(--white); border:1px solid var(--border); border-radius:10px; padding:18px 20px; box-shadow:var(--sh1); margin-bottom:16px; }
.filter-panel-title { font-family:'Barlow Condensed',sans-serif; font-size:13px; font-weight:700; text-transform:uppercase; letter-spacing:.8px; color:var(--text2); margin-bottom:12px; display:flex; align-items:center; gap:6px; }
.filter-panel-title::before { content:''; width:3px; height:12px; background:var(--green); border-radius:2px; display:inline-block; }

/* ─── ACCUEIL HERO ─── */
.hero { background:linear-gradient(135deg, var(--green) 0%, var(--green-dk) 100%); border-radius:12px; padding:28px 32px; color:white; margin-bottom:20px; position:relative; overflow:hidden; box-shadow:var(--sh2); }
.hero::before { content:''; position:absolute; top:-30px; right:-30px; width:160px; height:160px; border-radius:50%; background:rgba(255,255,255,.08); }
.hero::after { content:''; position:absolute; bottom:-50px; right:80px; width:100px; height:100px; border-radius:50%; background:rgba(255,255,255,.05); }
.hero-title { font-family:'Barlow Condensed',sans-serif; font-size:30px; font-weight:800; line-height:1.1; margin-bottom:6px; }
.hero-sub   { font-size:13px; opacity:.85; max-width:480px; line-height:1.5; }
.hero-date  { font-size:11px; opacity:.7; margin-top:12px; letter-spacing:.5px; }
.hero-stat  { text-align:right; position:relative; z-index:1; }
.hero-stat-val  { font-family:'Barlow Condensed',sans-serif; font-size:38px; font-weight:800; line-height:1; }
.hero-stat-lbl  { font-size:10px; opacity:.75; letter-spacing:1px; text-transform:uppercase; margin-top:2px; }

/* ─── MODULE CARDS ─── */
.mcard { background:var(--white); border:1px solid var(--border); border-radius:10px; padding:18px 20px; box-shadow:var(--sh1); transition:transform .18s, box-shadow .18s; cursor:pointer; height:100%; }
.mcard:hover { transform:translateY(-3px); box-shadow:var(--sh2); border-color:var(--green); }
.mcard-title { font-family:'Barlow Condensed',sans-serif; font-size:17px; font-weight:700; color:var(--text); margin-bottom:4px; }
.mcard-desc  { font-size:11px; color:var(--text3); line-height:1.5; }
.mcard-badge { display:inline-block; margin-top:10px; padding:3px 10px; border-radius:10px; font-size:9px; font-weight:700; letter-spacing:.5px; text-transform:uppercase; }
.mcard-badge.active { background:var(--green-lt); color:var(--green-dk); }
.mcard-badge.soon   { background:#F1F3F5; color:var(--text3); }

/* ─── TABS ─── */
[data-testid="stTabs"] [data-baseweb="tab-list"] { background:var(--white) !important; border-bottom:2px solid var(--border) !important; gap:0 !important; }
[data-testid="stTabs"] [data-baseweb="tab"] { background:transparent !important; color:var(--text2) !important; font-family:'Barlow',sans-serif !important; font-size:13px !important; font-weight:500 !important; padding:10px 20px !important; border-bottom:2px solid transparent !important; margin-bottom:-2px !important; }
[data-testid="stTabs"] [data-baseweb="tab"][aria-selected="true"] { color:var(--green) !important; border-bottom-color:var(--green) !important; font-weight:700 !important; }
[data-testid="stTabs"] [data-baseweb="tab-panel"] { background:var(--white) !important; border:1px solid var(--border) !important; border-top:none !important; border-radius:0 0 8px 8px !important; padding:20px !important; }

/* ─── INPUTS ─── */
[data-testid="stNumberInput"] input,[data-testid="stTextInput"] input { background:var(--white) !important; border-color:var(--border) !important; color:var(--text) !important; border-radius:6px !important; }
[data-testid="stNumberInput"] label,[data-testid="stTextInput"] label,
[data-testid="stSelectbox"] label,[data-testid="stCheckbox"] label { color:var(--text2) !important; font-size:12px !important; font-weight:600 !important; }

/* ─── BOUTONS ─── */
.main .stButton button[kind="primary"] { background:var(--green) !important; color:white !important; border:none !important; border-radius:7px !important; font-weight:700 !important; box-shadow:0 2px 8px rgba(0,132,61,.25) !important; }
.main .stButton button[kind="primary"]:hover { background:var(--green-dk) !important; transform:translateY(-1px) !important; }
.main .stButton button[kind="secondary"] { background:var(--white) !important; color:var(--text) !important; border:1px solid var(--border) !important; border-radius:7px !important; }

/* ─── METRICS ─── */
[data-testid="stMetric"] { background:var(--white) !important; border:1px solid var(--border) !important; border-radius:8px !important; padding:14px 16px !important; box-shadow:var(--sh1) !important; }
[data-testid="stMetricLabel"] { color:var(--text2) !important; font-size:11px !important; font-weight:600 !important; }
[data-testid="stMetricValue"] { color:var(--text) !important; font-family:'Barlow Condensed',sans-serif !important; font-size:24px !important; }

/* ─── DATAFRAME ─── */
[data-testid="stDataFrame"] { border:1px solid var(--border) !important; border-radius:8px !important; overflow:hidden !important; box-shadow:var(--sh1) !important; }

/* ─── DIVERS ─── */
hr { border-color:var(--border2) !important; }
[data-baseweb="tag"] { background:var(--green-lt) !important; border-color:rgba(0,132,61,.25) !important; }
[data-baseweb="tag"] span { color:var(--green-dk) !important; }
.stAlert { border-radius:8px !important; }
[data-testid="stExpander"] { background:var(--white) !important; border:1px solid var(--border) !important; border-radius:8px !important; }

/* ─── PLACEHOLDER ─── */
.ph-card { background:var(--white); border:1px solid var(--border); border-radius:12px; padding:56px 40px; text-align:center; margin-top:20px; box-shadow:var(--sh1); }
.ph-card h2 { font-family:'Barlow Condensed',sans-serif; font-size:26px; font-weight:700; color:var(--text); margin-bottom:8px; }
.ph-card p  { font-size:14px; color:var(--text2); max-width:400px; margin:0 auto; line-height:1.6; }
.ph-badge-g { display:inline-block; margin-top:20px; background:var(--green-lt); color:var(--green-dk); border:1px solid rgba(0,132,61,.2); border-radius:20px; padding:5px 18px; font-size:10px; font-weight:700; letter-spacing:1px; }
.ph-badge-b { display:inline-block; margin-top:20px; background:var(--blue-lt);  color:var(--blue);     border:1px solid rgba(21,101,192,.2); border-radius:20px; padding:5px 18px; font-size:10px; font-weight:700; letter-spacing:1px; }

/* ─── VENTES SPÉCIFIQUE ─── */
.ventes-upload { background:var(--white); border:1px solid var(--border); border-radius:10px; padding:20px; box-shadow:var(--sh1); margin-bottom:16px; }
.ventes-upload .vu-title { font-family:'Barlow Condensed',sans-serif; font-size:14px; font-weight:700; text-transform:uppercase; letter-spacing:.5px; color:var(--text2); margin-bottom:4px; }
.ventes-upload .vu-desc { font-size:11px; color:var(--text3); margin-bottom:14px; }
.dcard { background:var(--white); border:1px solid var(--border); border-radius:10px; padding:20px 22px; box-shadow:var(--sh1); position:relative; overflow:hidden; transition:transform .18s,box-shadow .18s; }
.dcard:hover { transform:translateY(-2px); box-shadow:var(--sh2); }
.dcard::after { content:''; position:absolute; top:0; left:0; right:0; height:3px; border-radius:10px 10px 0 0; }
.dcard.d1c::after { background:var(--green); }
.dcard.d2c::after { background:var(--blue); }
.dcard.d3c::after { background:var(--orange); }
.dcard-label { font-size:9px; font-weight:700; letter-spacing:1.5px; text-transform:uppercase; color:var(--text3); margin-bottom:6px; }
.dcard-val { font-family:'Barlow Condensed',sans-serif; font-size:36px; font-weight:700; line-height:1; }
.dcard-val.d1c { color:var(--green); }
.dcard-val.d2c { color:var(--blue); }
.dcard-val.d3c { color:var(--orange); }
.dcard-unit { font-size:13px; font-weight:500; color:var(--text3); margin-left:3px; }
.dcard-sub { font-size:11px; color:var(--text2); margin-top:6px; }
.llm-badge { display:inline-flex; align-items:center; gap:5px; background:var(--purple-lt); color:var(--purple); border:1px solid rgba(107,63,160,.2); border-radius:12px; padding:3px 10px; font-size:10px; font-weight:600; letter-spacing:.3px; margin-bottom:10px; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════
# PERSISTENCE & UTILS
# ══════════════════════════════════════════════════════
CACHE_DIR  = ".ocp_cache"
JORF_CACHE = os.path.join(CACHE_DIR,"jorf.pkl")
SAFI_CACHE = os.path.join(CACHE_DIR,"safi.pkl")
HIST_JORF  = os.path.join(CACHE_DIR,"hist_jorf.json")
HIST_SAFI  = os.path.join(CACHE_DIR,"hist_safi.json")
HIST_FILES = os.path.join(CACHE_DIR,"hist_files")
os.makedirs(CACHE_DIR,exist_ok=True); os.makedirs(HIST_FILES,exist_ok=True)

def save_cache(p,d):
    with open(p,"wb") as f: pickle.dump(d,f)
def load_cache(p):
    if os.path.exists(p):
        try:
            with open(p,"rb") as f: return pickle.load(f)
        except: pass
    return None
def clear_cache(p):
    if os.path.exists(p): os.remove(p)
def load_hist(p):
    if os.path.exists(p):
        try:
            with open(p,"r",encoding="utf-8") as f: return json.load(f)
        except: pass
    return []
def save_hist(p,h):
    with open(p,"w",encoding="utf-8") as f: json.dump(h,f,ensure_ascii=False,indent=2)
def add_hist(p,filename,filebytes,ftype):
    h=load_hist(p); ts=datetime.now().strftime("%Y%m%d_%H%M%S")
    pp=os.path.join(HIST_FILES,f"{ftype}_{ts}_{filename.replace(' ','_')}")
    with open(pp,"wb") as f: f.write(filebytes)
    e={"filename":filename,"date_upload":datetime.now().strftime("%d/%m/%Y %H:%M"),"path":pp,"type":ftype}
    h=[x for x in h if not(x["filename"]==filename and x["date_upload"][:10]==e["date_upload"][:10])]
    h.insert(0,e); save_hist(p,h[:20]); return pp
def get_hist_bytes(e):
    p=e.get("path","")
    if os.path.exists(p):
        with open(p,"rb") as f: return f.read()
    return None

NOMS_MOIS={1:"Jan",2:"Fev",3:"Mar",4:"Avr",5:"Mai",6:"Jun",7:"Jul",8:"Aou",9:"Sep",10:"Oct",11:"Nov",12:"Dec"}
ORDRE_MOIS={v:k for k,v in NOMS_MOIS.items()}

def force_n(v):
    if pd.isna(v): return 0.
    if isinstance(v,(int,float)): return 0. if abs(v)<1e-6 else float(v)
    s=str(v).strip()
    if s in("-","","nan"): return 0.
    n=re.sub(r'[^\d]','',s.replace("\xa0","").replace(" ",""))
    if len(n)>12: return 0.
    try: return float(n)
    except: return 0.

def mil(v): return round(v/1000,1)

def fmt(n):
    """Formate un nombre : séparateur milliers = espace insécable, décimale = virgule.
    Exemple : 1 234,5  (au lieu de 1,234.5)"""
    s = f"{n:,.1f}"
    # virgules (milliers) -> marqueur temporaire
    s = s.replace(",", "THOUSEP")
    # point décimal -> virgule
    s = s.replace(".", ",")
    # marqueur -> espace insécable
    s = s.replace("THOUSEP", "\u00a0")
    return s

def dsort(d):
    try: p=str(d).split("/"); return (int(p[2]),int(p[1]),int(p[0]))
    except: return (9999,99,99)
def msort(m):
    try: p=m.split(); return (int(p[1]),ORDRE_MOIS.get(p[0],99))
    except: return (9999,99)
def mlabel(d):
    try:
        p=str(d).split("/")
        if len(p)==3: return f"{NOMS_MOIS.get(int(p[1]),'?')} {p[2]}"
    except: pass
    return "Inconnu"
def filt(df,sel,col="Date"):
    if not sel: return df
    return df[df[col].isin(sel)]
SKIP=["total","recap","recapitulatif","annee","annuel","bilan","synthese","summary"]
def is_sheet(n): return not any(k in n.strip().lower() for k in SKIP)
def detect_eng(raw):
    for e in ['openpyxl','pyxlsb','calamine']:
        try: pd.ExcelFile(io.BytesIO(raw),engine=e); return e
        except: continue
    raise ValueError("Impossible de lire ce fichier.")
def read_bytes(file):
    file.seek(0); raw=file.read(); fn=getattr(file,'name','').lower().strip()
    if fn.endswith('.xlsb'): return raw,'pyxlsb'
    if fn.endswith(('.xlsm','.xlsx')):
        try: pd.ExcelFile(io.BytesIO(raw),engine='openpyxl'); return raw,'openpyxl'
        except: pass
    if fn.endswith('.xls'):
        try: pd.ExcelFile(io.BytesIO(raw),engine='calamine'); return raw,'calamine'
        except: pass
    return raw,detect_eng(raw)
def last_val(df,col,col_d="Date"):
    if df is None or df.empty: return 0.,None
    t=df[df[col]>0].copy()
    if t.empty: return 0.,None
    t["_s"]=t[col_d].apply(dsort); last=t.sort_values("_s").iloc[-1]
    return round(float(last[col]),1),last[col_d]

# ── DECADE HELPER ──
def get_decade(day):
    if day <= 10: return "D1"
    elif day <= 20: return "D2"
    else: return "D3"

def compute_decades(df, col_total, date_col="Date"):
    if df is None or df.empty: return []
    results = {}
    for _, row in df.iterrows():
        d_str = str(row[date_col])
        try:
            parts = d_str.split("/")
            day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
        except: continue
        key = (year, month)
        if key not in results:
            results[key] = {"annee": year, "mois": month,
                            "mois_label": f"{NOMS_MOIS.get(month,'?')} {year}",
                            "D1": 0., "D2": 0., "D3": 0.}
        dec = get_decade(day)
        val = float(row[col_total]) if pd.notna(row[col_total]) else 0.
        results[key][dec] += val
    out = []
    for key in sorted(results.keys()):
        r = results[key]
        r["D1"] = round(r["D1"], 1); r["D2"] = round(r["D2"], 1); r["D3"] = round(r["D3"], 1)
        r["total"] = round(r["D1"] + r["D2"] + r["D3"], 1)
        out.append(r)
    return out

def decade_status(annee, mois, decade):
    now = datetime.now(); cur_day=now.day; cur_mois=now.month; cur_annee=now.year
    if annee < cur_annee or (annee == cur_annee and mois < cur_mois): return "past"
    if annee > cur_annee or (annee == cur_annee and mois > cur_mois): return "future"
    if decade == "D1":
        if cur_day > 10: return "past"
        else: return "current"
    elif decade == "D2":
        if cur_day > 20: return "past"
        elif cur_day <= 10: return "future"
        else: return "current"
    else:
        if cur_day <= 20: return "future"
        else: return "current"

# ── PLOT THEME ──
PL=dict(
    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(242,244,247,0.6)',
    font=dict(family='Barlow,sans-serif',color='#4A5568'),
    xaxis=dict(gridcolor='#E0E4EA',linecolor='#E0E4EA',tickfont=dict(color='#4A5568',size=11)),
    yaxis=dict(gridcolor='#E0E4EA',linecolor='#E0E4EA',tickfont=dict(color='#4A5568',size=11)),
    legend=dict(bgcolor='rgba(255,255,255,.9)',bordercolor='#E0E4EA',borderwidth=1,font=dict(color='#12202E',size=11)),
    margin=dict(l=12,r=12,t=36,b=12), height=340,
)

# ══════════════════════════════════════════════════════
# PARSERS
# ══════════════════════════════════════════════════════
def parse_jorf(raw,eng):
    df=pd.read_excel(io.BytesIO(raw),sheet_name='EXPORT',header=None,engine=eng)
    co={"E":None,"C":None,"V":None}
    for r in range(len(df)):
        l=" ".join(df.iloc[r,0:3].astype(str)).upper()
        if "EXPORT ENGRAIS" in l: co["E"]=r
        if "EXPORT CAMIONS" in l: co["C"]=r
        if "VL CAMIONS"     in l: co["V"]=r
    ld=df.iloc[2,:]; cd=[j for j in range(3,len(ld)) if pd.notna(ld[j])]
    rows=[]
    for j in cd:
        dt=ld[j]; dl=dt.strftime('%d/%m/%Y') if hasattr(dt,'strftime') else str(dt).split(" ")[0]
        v1=mil(force_n(df.iloc[co["E"],j])) if co["E"] is not None else 0.
        v2=mil(force_n(df.iloc[co["C"],j])) if co["C"] is not None else 0.
        v3=mil(force_n(df.iloc[co["V"],j])) if co["V"] is not None else 0.
        rows.append({"Date":dl,"Export Engrais":v1,"Export Camions":v2,"VL Camions":v3,"TOTAL Jorf":round(v1+v2+v3,1)})
    return pd.DataFrame(rows)

def parse_rade(raw,eng):
    df=pd.read_excel(io.BytesIO(raw),sheet_name='Sit Navire',header=None,engine=eng)
    rows=[]
    for r in range(len(df)):
        dv=df.iloc[r,1]; val=df.iloc[r,3]
        if pd.isna(dv) or pd.isna(val): continue
        sd=str(dv).strip()
        if sd in("","nan","Date"): continue
        dl=dv.strftime('%d/%m/%Y') if hasattr(dv,'strftime') else sd
        rows.append({"Date":dl,"Engrais en attente":mil(force_n(val))})
    return pd.DataFrame(rows) if rows else None

def parse_safi(raw,eng):
    xl=pd.ExcelFile(io.BytesIO(raw),engine=eng); CJ=1;CE=31;CM=32;SR=6
    def norm(s):
        acc={"é":"e","è":"e","ê":"e","à":"a","â":"a","ù":"u","û":"u","ô":"o","î":"i","ç":"c"}
        s=s.lower()
        for a,b in acc.items(): s=s.replace(a,b)
        return s
    def pm(sn):
        mm={"jan":1,"fev":2,"mar":3,"avr":4,"mai":5,"jun":6,"jui":6,"jul":7,"aou":8,"sep":9,"oct":10,"nov":11,"dec":12}
        ml={"janvier":1,"fevrier":2,"mars":3,"avril":4,"mai":5,"juin":6,"juillet":7,"aout":8,"septembre":9,"octobre":10,"novembre":11,"decembre":12}
        pts=sn.strip().split(); mn=None; an=None
        for p in pts:
            pn=norm(p)
            if pn[:3] in mm: mn=mm[pn[:3]]
            if pn in ml: mn=ml[pn]
            try:
                y=int(p)
                if 2000<=y<=2100: an=y
            except: pass
        return mn,an
    rows=[]
    for sheet in xl.sheet_names:
        if not is_sheet(sheet): continue
        mn,an=pm(sheet)
        if mn is None or an is None: continue
        dfs=pd.read_excel(io.BytesIO(raw),sheet_name=sheet,header=None,engine=eng)
        tec=CE; tml=CM
        if dfs.shape[1]<=CM:
            fe=False
            for hr in range(min(8,len(dfs))):
                rv=[str(v).strip().upper() for v in dfs.iloc[hr]]
                for ci,v in enumerate(rv):
                    if "TSP" in v and "EXPORT" in v: tec=ci; fe=True
                    if "TSP" in v and "ML" in v: tml=ci
            if not fe: continue
        for ri in range(SR,len(dfs)):
            jv=dfs.iloc[ri,CJ]
            if pd.isna(jv): continue
            s=str(jv).strip()
            if s in("","nan") or any(k in s.upper() for k in ["TOTAL","CUMUL","MOYENNE","MOY"]): continue
            try: jn=int(float(s))
            except: continue
            if jn<1 or jn>31: continue
            te=mil(force_n(dfs.iloc[ri,tec])) if tec<dfs.shape[1] else 0.
            tm=mil(force_n(dfs.iloc[ri,tml])) if tml<dfs.shape[1] else 0.
            rows.append({"Mois":sheet,"Jour":jn,"Date":f"{jn:02d}/{mn:02d}/{an}","TSP Export":te,"TSP ML":tm,"TOTAL Safi":round(te+tm,1)})
    return pd.DataFrame(rows) if rows else None

def load_jorf(raw,fname):
    ff=io.BytesIO(raw); ff.name=fname; r,e=read_bytes(ff)
    jd=parse_jorf(r,e); rd=None
    try: rd=parse_rade(r,e)
    except: pass
    st.session_state.update({"jorf_df":jd,"rade_df":rd,"jorf_name":fname})
    save_cache(JORF_CACHE,{"jorf_df":jd,"rade_df":rd,"filename":fname})
    return jd
def load_safi(raw,fname):
    ff=io.BytesIO(raw); ff.name=fname; r,e=read_bytes(ff)
    sd=parse_safi(r,e)
    st.session_state.update({"safi_df":sd,"safi_name":fname})
    save_cache(SAFI_CACHE,{"safi_df":sd,"filename":fname})
    return sd

# ══════════════════════════════════════════════════════
# SESSION STATE INIT
# ══════════════════════════════════════════════════════
if "page" not in st.session_state: st.session_state["page"]="accueil"
for key,cache in [("jorf_loaded",JORF_CACHE),("safi_loaded",SAFI_CACHE)]:
    if key not in st.session_state:
        c=load_cache(cache)
        if c:
            if "jorf" in key:
                st.session_state["jorf_df"]=c.get("jorf_df")
                st.session_state["rade_df"]=c.get("rade_df")
                st.session_state["jorf_name"]=c.get("filename","")
            else:
                st.session_state["safi_df"]=c.get("safi_df")
                st.session_state["safi_name"]=c.get("filename","")
        st.session_state[key]=True

EXCEL_T=["xlsx","xls","xlsm","xlsb"]

# ══════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════
with st.sidebar:
    if os.path.exists("logo_ocp.png"):
        b64=base64.b64encode(open("logo_ocp.png","rb").read()).decode()
        logo_html=f'<img src="data:image/png;base64,{b64}" class="sbl-img"/>'
    else:
        logo_html='<div class="sbl-box">OCP</div>'
    st.markdown(f"""
    <div class="sbl">
      {logo_html}
      <div>
        <div class="sbl-name">OCP</div>
        <div class="sbl-sub">Manufacturing</div>
      </div>
    </div>""", unsafe_allow_html=True)

    st.markdown('<div class="slbl">Navigation</div>', unsafe_allow_html=True)

    NAV = [
        ("accueil","Accueil"),
        ("suivi","Suivi Chargement"),
        ("stock","Simulation Stock"),
        ("ventes","Pipeline des Ventes"),
        ("navires","Export Navire"),
    ]
    for key,label in NAV:
        t="primary" if st.session_state["page"]==key else "secondary"
        if st.button(label,key=f"nav_{key}",type=t,use_container_width=True):
            st.session_state["page"]=key; st.rerun()

    st.markdown('<div class="shr"></div>', unsafe_allow_html=True)
    st.markdown('<div class="slbl">Données actives</div>', unsafe_allow_html=True)
    jn=st.session_state.get("jorf_name",""); sn=st.session_state.get("safi_name","")
    dj="●" if jn else "○"; ds="●" if sn else "○"
    st.markdown(f"""
    <div style="padding:6px 14px 10px 14px;font-size:11px;color:#4A5568;line-height:2">
      {dj} <b>Jorf :</b> <span style="color:{'#00843D' if jn else '#94A3B8'}">{jn or 'Non chargé'}</span><br/>
      {ds} <b>Safi :</b> <span style="color:{'#00843D' if sn else '#94A3B8'}">{sn or 'Non chargé'}</span>
    </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════
# RE-READ SESSION
# ══════════════════════════════════════════════════════
jorf_df=st.session_state.get("jorf_df"); rade_df=st.session_state.get("rade_df")
safi_df=st.session_state.get("safi_df"); page=st.session_state["page"]

# ══════════════════════════════════════════════════════
# TOPBAR
# ══════════════════════════════════════════════════════
TITLES={
    "accueil": ("Tableau de Bord",    "Vue d'ensemble & historique"),
    "suivi":   ("Suivi Chargement",   "Jorf Lasfar & Safi — données par jour"),
    "stock":   ("Simulation Stock",   "Projection matières premières"),
    "ventes":  ("Pipeline des Ventes","Performances commerciales"),
    "navires": ("Export Navire",       "Planification chargements"),
}
t_title,t_sub=TITLES[page]
st.markdown(f"""
<div class="topbar">
  <div>
    <div class="tb-title">{t_title}</div>
    <div class="tb-bread">OCP Manufacturing &nbsp;›&nbsp; {t_title.split(' ',1)[1] if ' ' in t_title else t_title}</div>
  </div>
  <div class="tb-badge">{t_sub}</div>
</div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE : ACCUEIL
# ══════════════════════════════════════════════════════════════════════════════
if page=="accueil":
    jorf_kpi=jorf_df; safi_kpi=safi_df

    cj   = round(float(jorf_kpi["TOTAL Jorf"].sum()),1)    if jorf_kpi is not None else 0.
    cs   = round(float(safi_kpi["TOTAL Safi"].sum()),1)    if safi_kpi is not None else 0.
    ct   = round(cj+cs,1)
    today= datetime.now().strftime("%A %d %B %Y")

    cj_eng = round(float(jorf_kpi["Export Engrais"].sum()),1) if jorf_kpi is not None else 0.
    cj_cam = round(float(jorf_kpi["Export Camions"].sum()),1) if jorf_kpi is not None else 0.
    cj_vl  = round(float(jorf_kpi["VL Camions"].sum()),1)     if jorf_kpi is not None else 0.
    cs_exp = round(float(safi_kpi["TSP Export"].sum()),1) if safi_kpi is not None else 0.
    cs_ml  = round(float(safi_kpi["TSP ML"].sum()),1)     if safi_kpi is not None else 0.

    st.markdown(f"""
    <div style="display:flex;gap:16px;margin-bottom:20px;align-items:stretch">
      <div class="hero" style="flex:2;margin-bottom:0">
        <div class="hero-title">OCP Manufacturing Dashboard</div>
        <div class="hero-sub">Suivi consolidé des chargements, simulation de stock et pilotage des opérations — Jorf Lasfar & Safi.</div>
        <div class="hero-date">{today}</div>
      </div>
      <div class="hero" style="flex:1;margin-bottom:0;display:flex;flex-direction:column;justify-content:center;text-align:center">
        <div class="hero-stat-val">{fmt(ct)}</div>
        <div class="hero-stat-lbl">KT — Production Totale Cumulée — Jorf + Safi</div>
        <div style="margin-top:14px;opacity:.75;font-size:11px;letter-spacing:.3px">Jorf Lasfar : {fmt(cj)} KT &nbsp;|&nbsp; Safi : {fmt(cs)} KT</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="stitle">Synthèse cumulée — toutes données</div>', unsafe_allow_html=True)
    k1, k2, k3 = st.columns(3)

    with k1:
        if jorf_kpi is not None:
            st.markdown(f"""
            <div class="kcard green">
              <div>
                <div class="kc-lbl">Total Jorf Lasfar</div>
                <div class="kc-val green">{fmt(cj)}<span class="kc-unit">KT</span></div>
              </div>
              <div class="kc-detail">
                <div class="kc-detail-row"><span class="kc-detail-label">Export Engrais</span><span class="kc-detail-value">{fmt(cj_eng)} KT</span></div>
                <div class="kc-detail-row"><span class="kc-detail-label">Export Camions</span><span class="kc-detail-value">{fmt(cj_cam)} KT</span></div>
                <div class="kc-detail-row"><span class="kc-detail-label">VL Camions</span><span class="kc-detail-value">{fmt(cj_vl)} KT</span></div>
              </div>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown("""<div class="kcard green"><div class="kc-lbl">Total Jorf Lasfar</div><div class="kc-val green">—</div><div class="kc-sub" style="color:#94A3B8">Fichier non chargé</div></div>""", unsafe_allow_html=True)

    with k2:
        if safi_kpi is not None:
            st.markdown(f"""
            <div class="kcard blue">
              <div>
                <div class="kc-lbl">Total Safi</div>
                <div class="kc-val blue">{fmt(cs)}<span class="kc-unit">KT</span></div>
              </div>
              <div class="kc-detail">
                <div class="kc-detail-row"><span class="kc-detail-label">TSP Export</span><span class="kc-detail-value">{fmt(cs_exp)} KT</span></div>
                <div class="kc-detail-row"><span class="kc-detail-label">TSP ML</span><span class="kc-detail-value">{fmt(cs_ml)} KT</span></div>
              </div>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown("""<div class="kcard blue"><div class="kc-lbl">Total Safi</div><div class="kc-val blue">—</div><div class="kc-sub" style="color:#94A3B8">Fichier non chargé</div></div>""", unsafe_allow_html=True)

    with k3:
        st.markdown(f"""
        <div class="kcard orange">
          <div>
            <div class="kc-lbl">Jorf + Safi — Consolidé</div>
            <div class="kc-val orange">{fmt(ct)}<span class="kc-unit">KT</span></div>
          </div>
          <div class="kc-detail">
            <div class="kc-detail-row"><span class="kc-detail-label">Jorf Lasfar</span><span class="kc-detail-value">{fmt(cj)} KT</span></div>
            <div class="kc-detail-row"><span class="kc-detail-label">Safi</span><span class="kc-detail-value">{fmt(cs)} KT</span></div>
          </div>
        </div>""", unsafe_allow_html=True)

    st.markdown('<div class="stitle orange">Chargements par décade — D1 · D2 · D3</div>', unsafe_allow_html=True)
    dec_jorf = compute_decades(jorf_df, "TOTAL Jorf")  if jorf_df is not None else []
    dec_safi = compute_decades(safi_df, "TOTAL Safi")  if safi_df is not None else []

    if dec_jorf:
        st.markdown("""<div style="font-family:'Barlow Condensed',sans-serif;font-size:12px;font-weight:700;letter-spacing:1px;text-transform:uppercase;color:#00843D;margin-bottom:8px">▶ Jorf Lasfar</div>""", unsafe_allow_html=True)
        for i in range(0, len(dec_jorf), 3):
            cols = st.columns(min(3, len(dec_jorf)-i))
            for ci, r in enumerate(dec_jorf[i:i+3]):
                with cols[ci]:
                    d1s=decade_status(r["annee"],r["mois"],"D1"); d2s=decade_status(r["annee"],r["mois"],"D2"); d3s=decade_status(r["annee"],r["mois"],"D3")
                    b1="current" if d1s=="current" else ("past" if d1s=="past" else "future")
                    b2="current" if d2s=="current" else ("past" if d2s=="past" else "future")
                    b3="current" if d3s=="current" else ("past" if d3s=="past" else "future")
                    a1="active" if d1s=="current" else ""; a2="active" if d2s=="current" else ""; a3="active" if d3s=="current" else ""
                    lbl={"past":"Passé","current":"En cours","future":"À venir"}
                    st.markdown(f"""
                    <div class="decade-wrap">
                      <div class="decade-header"><div class="decade-title">{r['mois_label']}</div></div>
                      <div class="decade-grid">
                        <div class="decade-block {a1}"><div class="decade-block-label">D1 <span class="decade-badge {b1}">{lbl[d1s]}</span></div><div class="decade-block-val">{fmt(r['D1'])}</div><div class="decade-block-unit">KT · J1–10</div></div>
                        <div class="decade-block {a2}"><div class="decade-block-label">D2 <span class="decade-badge {b2}">{lbl[d2s]}</span></div><div class="decade-block-val">{fmt(r['D2'])}</div><div class="decade-block-unit">KT · J11–20</div></div>
                        <div class="decade-block {a3}"><div class="decade-block-label">D3 <span class="decade-badge {b3}">{lbl[d3s]}</span></div><div class="decade-block-val">{fmt(r['D3'])}</div><div class="decade-block-unit">KT · J21–fin</div></div>
                      </div>
                      <div class="decade-total-row"><span class="decade-total-label">Total mensuel</span><span class="decade-total-val">{fmt(r['total'])} KT</span></div>
                    </div>""", unsafe_allow_html=True)
    else:
        st.markdown("""<div style="background:#F2F4F7;border:1px dashed #E0E4EA;border-radius:10px;padding:20px;text-align:center;color:#94A3B8;font-size:12px;margin-bottom:12px">Aucune donnée Jorf — chargez un fichier pour voir les décades</div>""", unsafe_allow_html=True)

    if dec_safi:
        st.markdown("""<div style="font-family:'Barlow Condensed',sans-serif;font-size:12px;font-weight:700;letter-spacing:1px;text-transform:uppercase;color:#1565C0;margin:14px 0 8px 0">▶ Safi</div>""", unsafe_allow_html=True)
        for i in range(0, len(dec_safi), 3):
            cols = st.columns(min(3, len(dec_safi)-i))
            for ci, r in enumerate(dec_safi[i:i+3]):
                with cols[ci]:
                    d1s=decade_status(r["annee"],r["mois"],"D1"); d2s=decade_status(r["annee"],r["mois"],"D2"); d3s=decade_status(r["annee"],r["mois"],"D3")
                    b1="current" if d1s=="current" else ("past" if d1s=="past" else "future")
                    b2="current" if d2s=="current" else ("past" if d2s=="past" else "future")
                    b3="current" if d3s=="current" else ("past" if d3s=="past" else "future")
                    a1="active" if d1s=="current" else ""; a2="active" if d2s=="current" else ""; a3="active" if d3s=="current" else ""
                    lbl={"past":"Passé","current":"En cours","future":"À venir"}
                    st.markdown(f"""
                    <div class="decade-wrap">
                      <div class="decade-header"><div class="decade-title">{r['mois_label']}</div></div>
                      <div class="decade-grid">
                        <div class="decade-block {a1}"><div class="decade-block-label">D1 <span class="decade-badge {b1}">{lbl[d1s]}</span></div><div class="decade-block-val">{fmt(r['D1'])}</div><div class="decade-block-unit">KT · J1–10</div></div>
                        <div class="decade-block {a2}"><div class="decade-block-label">D2 <span class="decade-badge {b2}">{lbl[d2s]}</span></div><div class="decade-block-val">{fmt(r['D2'])}</div><div class="decade-block-unit">KT · J11–20</div></div>
                        <div class="decade-block {a3}"><div class="decade-block-label">D3 <span class="decade-badge {b3}">{lbl[d3s]}</span></div><div class="decade-block-val">{fmt(r['D3'])}</div><div class="decade-block-unit">KT · J21–fin</div></div>
                      </div>
                      <div class="decade-total-row"><span class="decade-total-label">Total mensuel</span><span class="decade-total-val">{fmt(r['total'])} KT</span></div>
                    </div>""", unsafe_allow_html=True)
    else:
        st.markdown("""<div style="background:#F2F4F7;border:1px dashed #E0E4EA;border-radius:10px;padding:20px;text-align:center;color:#94A3B8;font-size:12px;margin-bottom:12px">Aucune donnée Safi — chargez un fichier pour voir les décades</div>""", unsafe_allow_html=True)

    st.markdown('<div class="stitle">Modules disponibles</div>', unsafe_allow_html=True)
    m1,m2,m3,m4=st.columns(4)
    modules=[
        (m1,"Suivi Chargement","Tableau consolidé des chargements journaliers par site.","active","suivi"),
        (m2,"Simulation Stock","Projection du stock matières premières avec arrivées navires.","active","stock"),
        (m3,"Pipeline des Ventes","Suivi des ventes par décade avec détection IA des colonnes.","active","ventes"),
        (m4,"Export Navire","Planification et suivi des chargements et escales navires.","soon","navires"),
    ]
    for col,title,desc,status,nav_key in modules:
        with col:
            badge="Disponible" if status=="active" else "Prochainement"
            st.markdown(f"""<div class="mcard"><div class="mcard-title">{title}</div><div class="mcard-desc">{desc}</div><div class="mcard-badge {status}">{badge}</div></div>""", unsafe_allow_html=True)
            if status=="active":
                if st.button(f"Ouvrir →",key=f"open_{nav_key}",use_container_width=True):
                    st.session_state["page"]=nav_key; st.rerun()

    st.markdown('<div class="stitle">Historique des fichiers chargés</div>', unsafe_allow_html=True)
    hj=load_hist(HIST_JORF); hs=load_hist(HIST_SAFI)
    col_hj,col_hs=st.columns(2)
    for col,hist,hist_path,label,color,loader_fn in [
        (col_hj,hj,HIST_JORF,"Jorf Lasfar","jorf",load_jorf),
        (col_hs,hs,HIST_SAFI,"Safi","safi",load_safi),
    ]:
        with col:
            st.markdown(f"""<div class="card"><div class="card-title">Historique — {label}</div>""", unsafe_allow_html=True)
            if hist:
                active_name=st.session_state.get(f"{color}_name","")
                for i,e in enumerate(hist[:8]):
                    is_act=e["filename"]==active_name
                    dot_cls="hist-active" if is_act else "hist-inactive"
                    act_txt=" — <b style='color:#00843D'>Actif</b>" if is_act else ""
                    st.markdown(f"""
                    <div class="hist-item">
                      <div>
                        <div style="display:flex;align-items:center;gap:8px"><span class="{dot_cls}"></span><span class="hist-item-name">{e['filename']}</span><span class="hist-tag {color}">{color.upper()}</span></div>
                        <div class="hist-item-date" style="margin-left:15px">{e['date_upload']}{act_txt}</div>
                      </div>
                    </div>""", unsafe_allow_html=True)
                    if not is_act:
                        if st.button(f"↩ Recharger",key=f"rl_{color}_{i}",use_container_width=True):
                            raw=get_hist_bytes(e)
                            if raw:
                                try: loader_fn(raw,e["filename"]); st.rerun()
                                except Exception as ex: st.error(str(ex))
                            else: st.error("Fichier introuvable.")
            else:
                st.markdown(f'<div style="color:#94A3B8;font-size:12px;padding:12px 0">Aucun fichier {label} dans l\'historique.</div>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE : SUIVI CHARGEMENT
# ══════════════════════════════════════════════════════════════════════════════
elif page=="suivi":
    st.markdown('<div class="stitle">Chargement des fichiers</div>', unsafe_allow_html=True)
    uc1,uc2=st.columns(2)

    with uc1:
        st.markdown("""<div class="upload-zone"><div class="zone-title">Fichier Jorf Lasfar</div><div class="zone-desc">Fichier Excel avec feuille EXPORT et Sit Navire</div>""", unsafe_allow_html=True)
        file_jorf=st.file_uploader("Choisir fichier Jorf",type=EXCEL_T,key="jorf_up",label_visibility="collapsed")
        jn=st.session_state.get("jorf_name","")
        if jn: st.success(f"Actif : {jn}")
        if file_jorf:
            try:
                jb,eng=read_bytes(file_jorf); jd=parse_jorf(jb,eng); rd=None
                try: rd=parse_rade(jb,eng)
                except: pass
                clear_cache(JORF_CACHE)
                st.session_state.update({"jorf_df":jd,"rade_df":rd,"jorf_name":file_jorf.name})
                save_cache(JORF_CACHE,{"jorf_df":jd,"rade_df":rd,"filename":file_jorf.name})
                file_jorf.seek(0); add_hist(HIST_JORF,file_jorf.name,file_jorf.read(),"jorf")
                jorf_df=jd; rade_df=rd; st.success("Jorf chargé avec succès")
            except Exception as e: st.error(f"Erreur : {e}")
        st.markdown("</div>", unsafe_allow_html=True)

    with uc2:
        st.markdown("""<div class="upload-zone"><div class="zone-title">Fichier Safi</div><div class="zone-desc">Fichier Excel avec feuilles mensuelles TSP Export / ML</div>""", unsafe_allow_html=True)
        file_safi=st.file_uploader("Choisir fichier Safi",type=EXCEL_T,key="safi_up",label_visibility="collapsed")
        sn=st.session_state.get("safi_name","")
        if sn: st.success(f"Actif : {sn}")
        if file_safi:
            try:
                sb,eng=read_bytes(file_safi); sd=parse_safi(sb,eng)
                clear_cache(SAFI_CACHE)
                st.session_state.update({"safi_df":sd,"safi_name":file_safi.name})
                save_cache(SAFI_CACHE,{"safi_df":sd,"filename":file_safi.name})
                file_safi.seek(0); add_hist(HIST_SAFI,file_safi.name,file_safi.read(),"safi")
                safi_df=sd
                if sd is not None: st.success("Safi chargé avec succès")
                else: st.warning("Aucune feuille mensuelle détectée.")
            except Exception as e: st.error(f"Erreur : {e}")
        st.markdown("</div>", unsafe_allow_html=True)

    jorf_df=st.session_state.get("jorf_df"); rade_df=st.session_state.get("rade_df"); safi_df=st.session_state.get("safi_df")

    st.markdown('<div class="stitle">Filtrage des données</div>', unsafe_allow_html=True)

    def filtre_widget(df,label,key):
        mois_map={}; annees=set()
        for d in df["Date"].unique():
            try:
                p=str(d).split("/"); annees.add(int(p[2]))
                ml=f"{NOMS_MOIS.get(int(p[1]),'?')} {p[2]}"
            except: ml="Autre"
            mois_map.setdefault(ml,[]).append(d)
        for an in annees:
            for num,nom in NOMS_MOIS.items():
                ml=f"{nom} {an}"
                if ml not in mois_map: mois_map[ml]=[]
        mois_tries=sorted(mois_map.keys(),key=msort)
        opts=[m if mois_map[m] else f"{m} —" for m in mois_tries]
        mode=st.radio(f"Filtrer **{label}** par",["Tout","Mois","Dates"],horizontal=True,key=f"{key}_mode")
        if mode=="Tout": return [],"Toute la période"
        elif mode=="Mois":
            choix=st.multiselect("Sélectionner les mois",options=opts,default=[],key=f"{key}_mois")
            if not choix: return [],"Toute la période"
            ds=[]; lb=[]
            for m in choix:
                cl=m.rstrip(" —"); ds+=mois_map.get(cl,[]); lb.append(cl)
            return ds,", ".join(lb)
        else:
            all_d=sorted(df["Date"].unique().tolist(),key=lambda x:tuple(int(v) for v in str(x).split("/"))[::-1])
            choix=st.multiselect("Sélectionner les dates",all_d,key=f"{key}_dates")
            if not choix: return [],"Toute la période"
            return choix,f"{len(choix)} date(s)"

    fc1,fc2=st.columns(2)
    with fc1:
        st.markdown('<div class="filter-panel"><div class="filter-panel-title">Jorf Lasfar</div>', unsafe_allow_html=True)
        if jorf_df is not None:
            sel_jorf,lbl_jorf=filtre_widget(jorf_df,"Jorf","jorf")
        else:
            st.info("Chargez le fichier Jorf pour activer les filtres."); sel_jorf,lbl_jorf=[],"Toute la période"
        st.markdown('</div>', unsafe_allow_html=True)
    with fc2:
        st.markdown('<div class="filter-panel"><div class="filter-panel-title">Safi</div>', unsafe_allow_html=True)
        if safi_df is not None:
            sel_safi,lbl_safi=filtre_widget(safi_df,"Safi","safi")
        else:
            st.info("Chargez le fichier Safi pour activer les filtres."); sel_safi,lbl_safi=[],"Toute la période"
        st.markdown('</div>', unsafe_allow_html=True)

    jorf_k=filt(jorf_df,sel_jorf) if jorf_df is not None else None
    safi_k=filt(safi_df,sel_safi) if safi_df is not None else None
    rade_k=filt(rade_df,sel_jorf) if rade_df is not None else None
    cj=round(float(jorf_k["TOTAL Jorf"].sum()),1) if jorf_k is not None else 0.
    cs=round(float(safi_k["TOTAL Safi"].sum()),1) if safi_k is not None else 0.
    ct=round(cj+cs,1)
    rv,rd_=last_val(rade_k,"Engrais en attente") if rade_k is not None else (0.,None)

    periode=f"Filtre : {lbl_jorf} / {lbl_safi}" if (sel_jorf or sel_safi) else "Toute la période"
    st.markdown(f'<div class="stitle">Cumul à date — {periode}</div>', unsafe_allow_html=True)

    k1,k2,k3,k4=st.columns(4)
    def kpi(col,color,lbl,val,sub,extra=""):
        with col:
            st.markdown(f"""
            <div class="kcard {color}">
              <div class="kc-lbl">{lbl}</div>
              <div class="kc-val {color}">{fmt(val)}<span class="kc-unit">KT</span></div>
              <div class="kc-sub">{sub}</div>
              {f'<div style="font-size:10px;color:#94A3B8;margin-top:3px">{extra}</div>' if extra else ''}
            </div>""", unsafe_allow_html=True)

    kpi(k1,"green","Total Jorf",cj,"Export Engrais · Camions · VL" if jorf_df is not None else "Non chargé")
    with k2:
        if rade_df is not None and rd_:
            st.markdown(f"""<div class="kcard purple"><div class="kc-lbl">Rade Jorf</div><div class="kc-val purple">{fmt(rv)}<span class="kc-unit">KT</span></div><div class="kc-sub">Engrais en attente</div><div style="font-size:10px;color:#94A3B8;margin-top:3px">{rd_}</div></div>""", unsafe_allow_html=True)
        else: kpi(k2,"purple","Rade Jorf",0.,"Non chargé")
    kpi(k3,"blue","Total Safi",cs,"TSP Export · TSP ML" if safi_df is not None else "Non chargé")
    kpi(k4,"orange","Jorf + Safi",ct,"Consolidé toutes unités")

    st.markdown("<div style='margin-top:6px'></div>", unsafe_allow_html=True)
    st.markdown('<div class="stitle">Tableau consolidé — par jour (KT)</div>', unsafe_allow_html=True)

    any_data=jorf_df is not None or safi_df is not None or rade_df is not None
    if any_data:
        jf=filt(jorf_df,sel_jorf) if jorf_df is not None else None
        rf=filt(rade_df,sel_jorf) if rade_df is not None else None
        sf=filt(safi_df,sel_safi) if safi_df is not None else None
        all_d=set()
        if jf is not None: all_d|=set(jf["Date"].unique())
        if rf is not None: all_d|=set(rf["Date"].unique())
        if sf is not None: all_d|=set(sf["Date"].unique())
        all_d=sorted(all_d,key=dsort)
        rows=[]
        for d in all_d:
            row={"Date":d}
            if jf is not None:
                r=jf[jf["Date"]==d]
                row["J_Eng"]=round(r["Export Engrais"].sum(),1) if not r.empty else 0.
                row["J_Cam"]=round(r["Export Camions"].sum(),1) if not r.empty else 0.
                row["J_VL"] =round(r["VL Camions"].sum(),1)     if not r.empty else 0.
            if sf is not None:
                r=sf[sf["Date"]==d]
                row["S_Eng"]=round(r["TSP Export"].sum(),1) if not r.empty else 0.
                row["S_VL"] =round(r["TSP ML"].sum(),1)     if not r.empty else 0.
            jt=round(row.get("J_Eng",0)+row.get("J_Cam",0)+row.get("J_VL",0),1) if jf is not None else 0.
            st_=round(row.get("S_Eng",0)+row.get("S_VL",0),1) if sf is not None else 0.
            if jf is not None: row["J_TOT"]=jt
            if sf is not None: row["S_TOT"]=st_
            row["TOTAL"]=round(jt+st_,1)
            if rf is not None:
                r=rf[rf["Date"]==d]; row["RADE"]=round(r["Engrais en attente"].sum(),1) if not r.empty else 0.
            rows.append(row)
        udf=pd.DataFrame(rows)
        co=["Date"]
        if jf is not None: co+=["J_Eng","J_Cam","J_VL","J_TOT"]
        if sf is not None: co+=["S_Eng","S_VL","S_TOT"]
        co+=["TOTAL"]
        if rf is not None: co+=["RADE"]
        co=[c for c in co if c in udf.columns]; udf=udf[co]
        tr={"Date":"TOTAL GÉNÉRAL"}
        for c in udf.columns:
            if c=="Date": continue
            elif c=="RADE": tr[c]=None
            else: tr[c]=round(udf[c].sum(),1)
        disp=pd.concat([udf,pd.DataFrame([tr])],ignore_index=True)
        nm={"J_Eng":"Engrais","J_Cam":"Camions","J_VL":"VL","J_TOT":"▶ Total Jorf",
            "S_Eng":"TSP Export","S_VL":"TSP ML","S_TOT":"▶ Total Safi",
            "TOTAL":"▶ Total Cumulé","RADE":"Rade Jorf"}
        cfg={"Date":st.column_config.TextColumn("Date",width=90)}
        for c,n in nm.items():
            if c in disp.columns: cfg[c]=st.column_config.NumberColumn(n,format="%.1f")
        st.dataframe(disp,use_container_width=True,hide_index=True,height=min(660,45+35*len(disp)),column_config=cfg)

        cb1,cb2,cb3,cb4,_=st.columns([1,1,1,1,1])
        def copy_btn(container, df, col, lbl, key):
            vals = df[df["Date"] != "TOTAL GÉNÉRAL"][col].dropna().tolist()
            txt = "\t".join(str(round(float(v), 1)) for v in vals)
            bid = f"cb_{key}"
            with container:
                st.components.v1.html(f"""
                <button id="{bid}" onclick="navigator.clipboard.writeText('{txt}').then(()=>{{
                  this.innerHTML='✓ Copié !';this.style.background='#E8F5EE';this.style.color='#005C2A';this.style.borderColor='rgba(0,132,61,.3)';
                  setTimeout(()=>{{this.innerHTML='{lbl}';this.style.background='';this.style.color='';this.style.borderColor='';}},2000)
                }})">
                  {lbl}
                </button>
                <style>
                  #{bid}{{background:#F2F4F7;color:#4A5568;border:1px solid #E0E4EA;padding:6px 14px;border-radius:6px;cursor:pointer;font-size:12px;font-weight:600;font-family:Barlow,sans-serif;transition:all .15s;width:100%;}}
                  #{bid}:hover{{background:#E8F5EE;color:#005C2A;border-color:rgba(0,132,61,.3);}}
                </style>""", height=40)

        if jf is not None and "J_TOT" in udf.columns: copy_btn(cb1, udf, "J_TOT", "Copier Jorf", "j")
        if sf is not None and "S_TOT" in udf.columns: copy_btn(cb2, udf, "S_TOT", "Copier Safi", "s")
        if "TOTAL" in udf.columns: copy_btn(cb3, udf, "TOTAL", "Copier Total", "t")
        if rf is not None and "RADE" in udf.columns: copy_btn(cb4, udf, "RADE", "Copier Rade", "r")

        st.markdown("<div style='margin-top:6px'></div>", unsafe_allow_html=True)
        g1,g2=st.columns(2)
        with g1:
            st.markdown('<div class="stitle purple">Rade Jorf — Engrais en attente</div>', unsafe_allow_html=True)
            if rf is not None and "RADE" in udf.columns:
                rc=udf[udf["RADE"]>0].copy()
                if len(rc)>0:
                    fig=go.Figure()
                    fig.add_trace(go.Bar(x=rc["Date"],y=rc["RADE"],name="Rade",marker=dict(color="#6B3FA0",opacity=.85),hovertemplate='<b>%{x}</b><br>%{y:.1f} KT<extra></extra>'))
                    fig.update_layout(**PL,title=dict(text="Rade Jorf (KT)",font=dict(size=13,color="#4A5568")))
                    st.plotly_chart(fig,use_container_width=True)
                else: st.info("Pas de données Rade.")
            else: st.info("Chargez le fichier Jorf.")
        with g2:
            st.markdown('<div class="stitle">Jorf vs Safi — production journalière</div>', unsafe_allow_html=True)
            djs=[c for c in ["J_TOT","S_TOT"] if c in udf.columns]
            nm2={"J_TOT":"Jorf","S_TOT":"Safi"}
            if djs and len(udf)>1:
                fig=go.Figure()
                for c in djs:
                    clr="#00843D" if c=="J_TOT" else "#1565C0"
                    fc="rgba(0,132,61,0.07)" if c=="J_TOT" else "rgba(21,101,192,0.07)"
                    fig.add_trace(go.Scatter(x=udf["Date"],y=udf[c],mode='lines',name=nm2[c],line=dict(color=clr,width=2),fill='tozeroy',fillcolor=fc,hovertemplate=f'<b>%{{x}}</b><br>{nm2[c]}: %{{y:.1f}} KT<extra></extra>'))
                fig.update_layout(**PL,title=dict(text="Total Jorf & Safi (KT/jour)",font=dict(size=13,color="#4A5568")))
                st.plotly_chart(fig,use_container_width=True)
            else: st.info("Chargez les fichiers pour voir les graphiques.")
    else:
        st.info("Chargez au moins un fichier Excel ci-dessus pour afficher les données.")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE : SIMULATION STOCK
# ══════════════════════════════════════════════════════════════════════════════
elif page=="stock":

    def sim_stock(si,cj,navires,retards,cr=None):
        navires=sorted(navires,key=lambda x:x[0])
        t=pd.Timestamp.today(); debut=pd.Timestamp(t.year,t.month,1)
        cal=pd.date_range(start=debut,end=debut+pd.DateOffset(days=60),freq='D')
        stock=si; sv=[]; dates=[]; na=[]; nq=[]
        for j in cal:
            for (dp,qty) in navires:
                de=dp+pd.Timedelta(days=retards.get(dp,0))
                if j==de: stock+=qty; na.append(j); nq.append(qty)
            c=cr.get(j.date(),cj) if cr else cj
            stock-=c; sv.append(stock); dates.append(j)
        return dates,sv,na,nq

    def show_sim(dates,sv,na,nq,titre,seuil=36000):
        fig=go.Figure()
        fig.add_hrect(y0=0,y1=seuil,fillcolor="rgba(198,40,40,0.05)",line_width=0)
        fig.add_trace(go.Scatter(x=dates,y=sv,mode='lines',name='Stock',line=dict(color='#00843D',width=2.5),fill='tozeroy',fillcolor='rgba(0,132,61,0.07)',hovertemplate='<b>%{x|%d/%m/%Y}</b><br>Stock : %{y:,.0f} T<extra></extra>'))
        fig.add_trace(go.Scatter(x=dates,y=[seuil]*len(dates),mode='lines',name=f'Seuil ({seuil:,} T)',line=dict(dash='dash',color='#C62828',width=1.5)))
        for i,d in enumerate(na):
            idx=dates.index(d)
            fig.add_trace(go.Scatter(x=[d],y=[sv[idx]],mode='markers+text',name=f'Navire {i+1}',marker=dict(symbol='triangle-up',color='#1565C0',size=13,line=dict(color='white',width=1.5)),text=[f"+{nq[i]:,} T"],textposition='top center',textfont=dict(size=11,color='#1565C0'),showlegend=True))
        lyt=dict(**PL); lyt['height']=400; lyt['title']=dict(text=titre,font=dict(size=14,color='#12202E'))
        fig.update_layout(**lyt); st.plotly_chart(fig,use_container_width=True)
        m1,m2,m3=st.columns(3)
        mn=min(sv); mn_d=dates[sv.index(mn)]; jc=sum(1 for v in sv if v<seuil)
        m1.metric("Stock minimum",f"{mn:,.0f} T",f"le {mn_d.strftime('%d/%m/%Y')}")
        m2.metric("Stock final",f"{sv[-1]:,.0f} T")
        m3.metric(f"Jours critiques",f"{jc} j",delta="Risque" if jc>0 else "OK")

    tab_sa,tab_jo=st.tabs(["Site de Safi","Site de Jorf"])

    with tab_sa:
        ms=st.selectbox("Matière première",["Soufre"],key="ss_mat")
        ps=f"ss_{ms.lower()}"
        c1,c2=st.columns(2)
        with c1: si_s=st.number_input("Stock initial (T)",key=f"{ps}_si",min_value=0,value=40000,step=1000)
        with c2: cj_s=st.number_input("Conso journalière (T)",key=f"{ps}_cj",min_value=0,value=3600,step=100)
        ucr=st.checkbox("Consommations réelles par jour ?",key=f"{ps}_ucr")
        cr={}
        if ucr:
            dm=pd.Timestamp.today().replace(day=1); jours=pd.date_range(dm,dm+pd.offsets.MonthEnd(1),freq='D')
            cols=st.columns(4)
            for i,j in enumerate(jours):
                with cols[i%4]: cr[j.date()]=st.number_input(j.strftime('%d/%m'),min_value=0,value=int(cj_s),step=100,key=f"{ps}_cr{j.strftime('%Y%m%d')}")
        st.markdown('<div class="stitle blue">Navires prévus</div>', unsafe_allow_html=True)
        nav,ret=[],{}; nn=st.number_input("Nombre de navires",key=f"{ps}_n",min_value=0,value=3)
        for i in range(int(nn)):
            cd,cq,cr2=st.columns(3)
            with cd: da=st.date_input(f"Date navire {i+1}",pd.Timestamp.today(),key=f"{ps}_d{i}")
            with cq: qty=st.number_input(f"Quantité {i+1} (T)",0,500000,30000,1000,key=f"{ps}_q{i}")
            with cr2: r=st.number_input(f"Retard (j) {i+1}",0,30,0,1,key=f"{ps}_r{i}")
            nav.append((pd.Timestamp(da),qty))
            if r>0: ret[pd.Timestamp(da)]=r
        if st.button(f"Lancer la simulation — Safi / {ms}",key=f"{ps}_btn",type="primary"):
            d,sv,na,nq=sim_stock(si_s,cj_s,nav,ret,cr if ucr else None)
            show_sim(d,sv,na,nq,f"Stock — Safi / {ms}")

    with tab_jo:
        mj=st.selectbox("Matière première",["Soufre","NH3","KCL","ACS"],key="sj_mat")
        pj=f"sj_{mj.lower()}"
        if mj=="ACS":
            st.markdown('<div class="stitle">Paramètres ACS</div>', unsafe_allow_html=True)
            c1,c2,c3,c4=st.columns(4)
            with c1: ce=st.number_input("Conso engrais (T)",key=f"{pj}_ce",min_value=0,value=12000)
            with c2: si_a=st.number_input("Stock initial (T)",key=f"{pj}_si",min_value=0,value=300000)
            with c3: rv2=st.number_input("Rade (T)",key=f"{pj}_rv",min_value=0,value=60000)
            with c4: dc=st.number_input("Déchargement (T)",key=f"{pj}_dc",min_value=0,value=300000)
            dm=pd.Timestamp.today().replace(day=1); cal=pd.date_range(start=dm,end=dm+pd.DateOffset(days=60),freq='D')
            pjj={d.normalize():0 for d in cal}
            def rl(lignes,pfx,cad_def):
                tot=0
                for i,t in enumerate(st.tabs([f"{l}" for l in lignes])):
                    with t:
                        la=lignes[i]; jar_str=st.text_input(f"Arrêts (ex: 1-3,15)",key=f"{pfx}_{la}_a")
                        jar=[]
                        if jar_str:
                            for pt in jar_str.split(","):
                                pt=pt.strip()
                                if "-" in pt:
                                    a_,b_=pt.split("-"); jar.extend(range(int(a_),int(b_)+1))
                                else: jar.append(int(pt))
                            jar=sorted(set(jar))
                        nb=st.number_input("Périodes",min_value=1,value=1,key=f"{pfx}_{la}_nb"); pl=0
                        for p2 in range(int(nb)):
                            ca,cb,cc=st.columns(3)
                            with ca: dd=st.date_input(f"Début {p2+1}",dm,key=f"{pfx}_{la}_dd{p2}")
                            with cb: df2=st.date_input(f"Fin {p2+1}",dm+pd.Timedelta(days=5),key=f"{pfx}_{la}_df{p2}")
                            with cc: cad=st.number_input(f"Cadence T/j",min_value=0,value=cad_def,key=f"{pfx}_{la}_cd{p2}")
                            for d in pd.date_range(pd.Timestamp(dd),pd.Timestamp(df2),freq='D'):
                                if d.day not in jar: pjj[d.normalize()]=pjj.get(d.normalize(),0)+cad; pl+=cad
                        tot+=pl; st.info(f"**{la}** : {pl:,.0f} T")
                return tot
            st.markdown('<div class="stitle">Lignes ACS</div>', unsafe_allow_html=True)
            la_acs=["01A","01B","01C","01X","01Y","01Z","101D","101E","101U","JFC1","JFC2","JFC3","JFC4","JFC5","IMACID","PMP"]
            pa=rl(la_acs,f"{pj}_a",2600)
            st.markdown('<div class="stitle blue">Lignes ACP29</div>', unsafe_allow_html=True)
            la_acp=["JFC1_ACP29","JFC2_ACP29","JFC3_ACP29","JFC4_ACP29","JFC5_ACP29","JLN_03AB","JLN_03CD","JLN_03XY","JLN_03ZU","JLN_03E","JLN_03F","PMP_ACP29","IMACID_ACP29"]
            pp=rl(la_acp,f"{pj}_p",1000)
            st.markdown('<div class="stitle orange">Résultats</div>', unsafe_allow_html=True)
            c29=3.14*pp; sf2=si_a+dc+rv2+pa-c29-ce
            r1,r2,r3,r4=st.columns(4)
            r1.metric("Production ACS",f"{pa:,.0f} T"); r2.metric("Production ACP29",f"{pp:,.0f} T")
            r3.metric("Conso ACP29 (x3.14)",f"{c29:,.0f} T"); r4.metric("Stock final",f"{sf2:,.0f} T",delta="Excédent" if sf2>0 else "Déficit")
            nb2=len(cal); pjr=pa/nb2 if nb2>0 else 0; cjr=(c29+ce)/nb2 if nb2>0 else 0
            stk2=si_a; svacs=[]
            for i_d,d in enumerate(cal):
                if i_d==0: stk2+=rv2+dc
                stk2+=pjr; stk2-=cjr; svacs.append(stk2)
            fig=go.Figure()
            fig.add_trace(go.Scatter(x=cal,y=svacs,mode='lines',name='Stock ACS',line=dict(color='#00843D',width=2.5),fill='tozeroy',fillcolor='rgba(0,132,61,0.07)'))
            fig.add_trace(go.Scatter(x=cal,y=[0]*len(cal),mode='lines',name='Zéro',line=dict(dash='dash',color='#C62828',width=1.5)))
            lyt2=dict(**PL); lyt2['height']=380; lyt2['title']=dict(text="Évolution stock ACS",font=dict(size=13,color='#12202E'))
            fig.update_layout(**lyt2); st.plotly_chart(fig,use_container_width=True)
        else:
            SEUILS={"Soufre":36000,"NH3":5000,"KCL":10000}; seuil=SEUILS.get(mj,36000)
            c1,c2=st.columns(2)
            with c1: si_j=st.number_input("Stock initial (T)",key=f"{pj}_si",min_value=0,value=100000,step=1000)
            with c2: cj_j=st.number_input("Conso journalière (T)",key=f"{pj}_cj",min_value=0,value=17500,step=100)
            ucr2=st.checkbox("Consommations réelles ?",key=f"{pj}_ucr"); cr2={}
            if ucr2:
                dm=pd.Timestamp.today().replace(day=1); jours=pd.date_range(dm,dm+pd.offsets.MonthEnd(1),freq='D')
                cols=st.columns(4)
                for i,j in enumerate(jours):
                    with cols[i%4]: cr2[j.date()]=st.number_input(j.strftime('%d/%m'),min_value=0,value=int(cj_j),step=100,key=f"{pj}_cr{j.strftime('%Y%m%d')}")
            st.markdown('<div class="stitle blue">Navires prévus</div>', unsafe_allow_html=True)
            nav2,ret2=[],{}; nn2=st.number_input(f"Navires ({mj})",key=f"{pj}_n",min_value=0,value=3)
            for i in range(int(nn2)):
                cd,cq,cr3=st.columns(3)
                with cd: da=st.date_input(f"Date {i+1}",pd.Timestamp.today(),key=f"{pj}_d{i}")
                with cq: qty=st.number_input(f"Qté {i+1} (T)",0,500000,30000,1000,key=f"{pj}_q{i}")
                with cr3: r=st.number_input(f"Retard {i+1}j",0,30,0,1,key=f"{pj}_r{i}")
                nav2.append((pd.Timestamp(da),qty))
                if r>0: ret2[pd.Timestamp(da)]=r
            if st.button(f"Lancer la simulation — Jorf / {mj}",key=f"{pj}_btn",type="primary"):
                d,sv,na,nq=sim_stock(si_j,cj_j,nav2,ret2,cr2 if ucr2 else None)
                show_sim(d,sv,na,nq,f"Stock — Jorf / {mj}",seuil=seuil)

elif page=="ventes":
    # ─── 1. FONCTIONS ET INITIALISATION ──────────────────────────────────
    if "ventes_df" not in st.session_state:
        st.session_state["ventes_df"] = None
        st.session_state["ventes_mapping"] = {}

    def clean_numeric_v(series):
        return pd.to_numeric(series, errors='coerce').fillna(0)

    st.markdown('<div class="stitle">Pipeline des Ventes — Vue Restreinte (7 Colonnes)</div>', unsafe_allow_html=True)
    
    # ─── 2. CHARGEMENT SANS FILTRES EXCEL ────────────────────────────────
    file_v = st.file_uploader("Charger le fichier Excel", type=EXCEL_T)

    if file_v:
        try:
            raw_v, eng_v = read_bytes(file_v)
            xl = pd.ExcelFile(io.BytesIO(raw_v), engine=eng_v)
            target = "January" if "January" in xl.sheet_names else xl.sheet_names[0]
            # On lit tout le fichier (Pandas ignore les filtres visuels d'Excel)
            df_full = pd.read_excel(io.BytesIO(raw_v), sheet_name=target, engine=eng_v)
            df_full.columns = [str(c).strip() for c in df_full.columns]
            
            st.session_state["ventes_df"] = df_full
            st.success(f"✅ Fichier chargé : {len(df_full)} lignes détectées.")
        except Exception as e:
            st.error(f"Erreur de lecture : {e}")

    # ─── 3. LOGIQUE D'AFFICHAGE ET FILTRES ───────────────────────────────
    df_raw = st.session_state.get("ventes_df")
    vmap = st.session_state.get("ventes_mapping", {})

    if df_raw is not None:
        # Configuration des 7 colonnes cibles
        with st.expander("⚙️ CONFIGURATION : Mapper vos 7 colonnes"):
            new_map = {}
            roles = {
                "mois": "Mois", "site": "Site / Port", "status": "Statut Planif",
                "conf": "Confirmation", "d1": "D1 (KT)", "d2": "D2 (KT)", "d3": "D3 (KT)"
            }
            c_m = st.columns(4)
            for i, (rk, rl) in enumerate(roles.items()):
                opts = ["(non mappé)"] + df_raw.columns.tolist()
                curr = vmap.get(rk)
                with c_m[i%4]:
                    sel = st.selectbox(f"{rl}", opts, index=opts.index(curr) if curr in opts else 0, key=f"map_{rk}")
                    new_map[rk] = sel if sel != "(non mappé)" else None
            
            if st.button("💾 Valider et Filtrer"):
                st.session_state["ventes_mapping"] = new_map
                st.rerun()

        # --- APPLICATION DES FILTRES ---
        df_f = df_raw.copy()
        
        # A. Filtre de sécurité Statut (Nommée, Rade, Chargement)
        c_status = vmap.get("status")
        if c_status:
            mots_cles = ["nomm", "rade", "cours", "charg"]
            df_f = df_f[df_f[c_status].astype(str).str.lower().str.contains('|'.join(mots_cles), na=False)]

        # B. Barre de filtres (Mois, Site, Confirmation)
        st.markdown('<div class="filter-panel">', unsafe_allow_html=True)
        f1, f2, f3 = st.columns(3)
        
        c_mois, c_site, c_conf = vmap.get("mois"), vmap.get("site"), vmap.get("conf")
        
        if c_mois:
            m_list = ["Tous"] + sorted(df_raw[c_mois].dropna().unique().tolist())
            sel_m = f1.selectbox("📅 Mois", m_list)
            if sel_m != "Tous": df_f = df_f[df_f[c_mois] == sel_m]
            
        if c_site:
            s_list = ["Tous"] + sorted(df_raw[c_site].dropna().unique().tolist())
            sel_s = f2.selectbox("📍 Site / Port", s_list)
            if sel_s != "Tous": df_f = df_f[df_f[c_site] == sel_s]
            
        if c_conf:
            co_list = ["Tous"] + sorted(df_raw[c_conf].dropna().unique().tolist())
            sel_co = f3.selectbox("✅ Confirmation", co_list)
            if sel_co != "Tous": df_f = df_f[df_f[c_conf] == sel_co]
        st.markdown('</div>', unsafe_allow_html=True)

        # ─── 4. CALCULS ET TABLEAU FINAL (LES 7 COLONNES) ─────────────────
        # On vérifie que les colonnes D1, D2, D3 sont mappées pour le calcul
        v_d1, v_d2, v_d3 = vmap.get("d1"), vmap.get("d2"), vmap.get("d3")
        
        t1 = clean_numeric_v(df_f[v_d1]).sum() if v_d1 else 0
        t2 = clean_numeric_v(df_f[v_d2]).sum() if v_d2 else 0
        t3 = clean_numeric_v(df_f[v_d3]).sum() if v_d3 else 0
        total_kt = round(t1 + t2 + t3, 1)

        st.markdown(f"""<div style="background:#f0f2f6; padding:15px; border-radius:10px; border-left:5px solid #00843D; margin:10px 0;">
            <span style="font-weight:bold; color:#333;">TOTAL DU PÉRIMITRE : </span>
            <span style="font-size:22px; font-weight:800; color:#00843D;">{total_kt} KT</span>
        </div>""", unsafe_allow_html=True)

        # Affichage STRICT des 7 colonnes demandées
        cols_finales = [vmap[k] for k in ["mois", "site", "status", "conf", "d1", "d2", "d3"] if vmap.get(k)]
        
        if not df_f.empty:
            st.dataframe(df_f[cols_finales], use_container_width=True, hide_index=True)
        else:
            st.warning("Aucune donnée ne correspond aux filtres sélectionnés.")
# ══════════════════════════════════════════════════════════════════════════════
# PAGE : EXPORT NAVIRE (placeholder)
# ══════════════════════════════════════════════════════════════════════════════
elif page=="navires":
    st.markdown("""<div class="ph-card"><h2>Export Navire</h2>
    <p>Ce module permettra de planifier et suivre les chargements navires, les escales et les volumes exportés.</p>
    <div class="ph-badge-b">PROCHAINEMENT</div></div>""", unsafe_allow_html=True)
