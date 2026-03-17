import streamlit as st
import pandas as pd
import re
import os
import io
import pickle
import json
from datetime import datetime
import plotly.graph_objects as go

st.set_page_config(
    page_title="OCP Manufacturing Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ══════════════════════════════════════════════════════════════════════════════
# THEME & GLOBAL CSS
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow:wght@300;400;500;600;700&family=Barlow+Condensed:wght@500;600;700;800&display=swap');

:root {
  --green:        #00843D;
  --green-dk:     #005C2A;
  --green-lt:     #E8F5EE;
  --blue:         #1565C0;
  --blue-lt:      #E3EAF8;
  --orange:       #C05A00;
  --orange-lt:    #FBF0E6;
  --purple:       #6B3FA0;
  --purple-lt:    #F0EBF8;
  --red:          #C62828;
  --bg:           #F4F6F8;
  --white:        #FFFFFF;
  --border:       #DDE1E7;
  --text:         #1A2332;
  --text-2:       #4A5568;
  --text-3:       #9AAABB;
  --shadow-sm:    0 1px 3px rgba(0,0,0,0.08);
  --shadow-md:    0 4px 12px rgba(0,0,0,0.10);
}

html, body, [class*="css"] { font-family: 'Barlow', sans-serif !important; color: var(--text); }

/* ── App background ── */
.stApp { background: var(--bg) !important; }
.main .block-container { padding: 0 1.5rem 2rem 1.5rem !important; max-width: 100% !important; }

/* ── Hide Streamlit chrome ── */
#MainMenu, footer { visibility: hidden; }
header[data-testid="stHeader"] { background: transparent !important; height: 0 !important; }
[data-testid="stDecoration"] { display: none !important; }
.stDeployButton { display: none !important; }

/* ════════════════════════════
   SIDEBAR — clé du problème
   ════════════════════════════ */
[data-testid="stSidebar"] {
  background: var(--white) !important;
  border-right: 1px solid var(--border) !important;
  box-shadow: 2px 0 8px rgba(0,0,0,0.06) !important;
}
/* Forcer la largeur et l'affichage */
[data-testid="stSidebar"],
[data-testid="stSidebar"] > div {
  width: 252px !important;
  min-width: 252px !important;
  max-width: 252px !important;
}
[data-testid="stSidebarContent"] { padding: 0 !important; overflow-y: auto !important; }

/* Cacher le chevron de repli */
button[data-testid="baseButton-headerNoPadding"],
[data-testid="stSidebarCollapseButton"],
button[kind="header"] { display: none !important; visibility: hidden !important; }

/* Enlever le padding Streamlit dans la sidebar */
[data-testid="stSidebar"] section { padding: 0 !important; }
[data-testid="stSidebar"] .block-container { padding: 0 !important; }

/* ── Logo zone ── */
.nav-logo {
  padding: 18px 16px 14px 16px;
  border-bottom: 1px solid #EEF0F3;
  display: flex; align-items: center; gap: 10px;
  background: var(--white);
}
.nav-logo-img { width: 40px; height: 40px; object-fit: contain; flex-shrink: 0; }
.nav-logo-box {
  width: 40px; height: 40px; background: var(--green); border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  font-family: 'Barlow Condensed', sans-serif; font-size: 16px; font-weight: 800;
  color: white; flex-shrink: 0; letter-spacing: 0.5px;
}
.nav-logo-name {
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 19px; font-weight: 800; color: var(--green); line-height: 1.1;
}
.nav-logo-sub { font-size: 9px; color: var(--text-3); letter-spacing: 1.5px; text-transform: uppercase; }

/* ── Nav section label ── */
.nav-sep {
  font-size: 9px; font-weight: 700; letter-spacing: 2px; text-transform: uppercase;
  color: var(--text-3); padding: 14px 16px 5px 16px;
}
.nav-hr { height: 1px; background: #EEF0F3; margin: 6px 0; }

/* ── Nav buttons in sidebar ── */
[data-testid="stSidebar"] .stButton button {
  width: 100% !important;
  background: transparent !important;
  border: none !important;
  border-radius: 0 !important;
  color: var(--text-2) !important;
  font-family: 'Barlow', sans-serif !important;
  font-size: 13px !important; font-weight: 500 !important;
  padding: 9px 14px 9px 18px !important;
  text-align: left !important;
  border-left: 3px solid transparent !important;
  white-space: nowrap !important;
  box-shadow: none !important;
  transition: background 0.15s, color 0.15s !important;
}
[data-testid="stSidebar"] .stButton button:hover {
  background: var(--green-lt) !important;
  color: var(--green) !important;
  border-left-color: rgba(0,132,61,0.4) !important;
}
[data-testid="stSidebar"] .stButton button[kind="primary"] {
  background: var(--green-lt) !important;
  color: var(--green-dk) !important;
  border-left: 3px solid var(--green) !important;
  font-weight: 700 !important;
}

/* ── File uploader in sidebar ── */
[data-testid="stSidebar"] [data-testid="stFileUploader"] { padding: 0 8px; }
[data-testid="stSidebar"] [data-testid="stFileUploader"] label {
  font-size: 11px !important; color: var(--text-2) !important; font-weight: 600 !important;
}
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {
  background: var(--bg) !important;
  border: 1px dashed var(--border) !important; border-radius: 6px !important;
}
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] p { font-size: 10px !important; }
[data-testid="stSidebar"] .stAlert { margin: 2px 8px !important; font-size: 11px !important; }

/* ── Expander in sidebar ── */
[data-testid="stSidebar"] [data-testid="stExpander"] {
  margin: 2px 8px !important; border-radius: 6px !important;
  border: 1px solid var(--border) !important; background: var(--bg) !important;
}
[data-testid="stSidebar"] [data-testid="stExpander"] summary { font-size: 11px !important; }

/* ── Radio & multiselect in sidebar ── */
[data-testid="stSidebar"] [data-testid="stRadio"] { padding: 0 8px !important; }
[data-testid="stSidebar"] [data-testid="stRadio"] label p { font-size: 12px !important; }
[data-testid="stSidebar"] [data-testid="stMultiSelect"] { padding: 0 8px !important; }
[data-testid="stSidebar"] .stMarkdown { padding: 0 8px !important; }
[data-testid="stSidebar"] .stMarkdown p { font-size: 12px !important; font-weight: 600 !important; color: var(--text-2) !important; }

/* ════════════════════════════
   TOP BAR
   ════════════════════════════ */
.topbar {
  background: var(--white);
  border-bottom: 1px solid var(--border);
  padding: 12px 1.5rem;
  margin: 0 -1.5rem 20px -1.5rem;
  display: flex; align-items: center; justify-content: space-between;
  box-shadow: var(--shadow-sm);
}
.topbar-title {
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 21px; font-weight: 700; color: var(--text);
}
.topbar-bread { font-size: 11px; color: var(--text-3); margin-top: 1px; }
.topbar-badge {
  background: var(--green-lt); color: var(--green-dk);
  border: 1px solid rgba(0,132,61,0.2);
  border-radius: 20px; padding: 4px 14px;
  font-size: 11px; font-weight: 600;
}

/* ════════════════════════════
   KPI CARDS
   ════════════════════════════ */
.kpi-card {
  background: var(--white); border: 1px solid var(--border);
  border-radius: 10px; padding: 16px 18px;
  box-shadow: var(--shadow-sm);
  transition: transform 0.18s, box-shadow 0.18s;
  position: relative; overflow: hidden;
}
.kpi-card:hover { transform: translateY(-2px); box-shadow: var(--shadow-md); }
.kpi-card::after {
  content: ''; position: absolute;
  top: 0; left: 0; right: 0; height: 3px; border-radius: 10px 10px 0 0;
}
.kpi-card.green::after  { background: var(--green); }
.kpi-card.blue::after   { background: var(--blue); }
.kpi-card.orange::after { background: var(--orange); }
.kpi-card.purple::after { background: var(--purple); }
.kpi-icon  { font-size: 18px; margin-bottom: 8px; display: block; }
.kpi-label { font-size: 10px; font-weight: 700; letter-spacing: 1.2px; text-transform: uppercase; color: var(--text-3); margin-bottom: 4px; }
.kpi-value { font-family: 'Barlow Condensed', sans-serif; font-size: 34px; font-weight: 700; line-height: 1; }
.kpi-value.green  { color: var(--green); }
.kpi-value.blue   { color: var(--blue); }
.kpi-value.orange { color: var(--orange); }
.kpi-value.purple { color: var(--purple); }
.kpi-unit { font-size: 13px; font-weight: 500; color: var(--text-3); margin-left: 2px; }
.kpi-sub  { font-size: 11px; color: var(--text-2); margin-top: 5px; }

/* ════════════════════════════
   SECTION TITLE
   ════════════════════════════ */
.section-title {
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 13px; font-weight: 700; letter-spacing: 1px; text-transform: uppercase;
  color: var(--text-2); margin: 22px 0 10px 0;
  display: flex; align-items: center; gap: 8px;
}
.section-title::before {
  content: ''; width: 3px; height: 14px;
  background: var(--green); border-radius: 2px; display: inline-block;
}
.section-title.blue::before   { background: var(--blue); }
.section-title.orange::before { background: var(--orange); }
.section-title.purple::before { background: var(--purple); }

/* ════════════════════════════
   DATAFRAME
   ════════════════════════════ */
[data-testid="stDataFrame"] {
  border: 1px solid var(--border) !important;
  border-radius: 8px !important; overflow: hidden !important;
  box-shadow: var(--shadow-sm) !important;
}

/* ════════════════════════════
   TABS
   ════════════════════════════ */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
  background: var(--white) !important;
  border-bottom: 2px solid var(--border) !important; gap: 0 !important;
}
[data-testid="stTabs"] [data-baseweb="tab"] {
  background: transparent !important; color: var(--text-2) !important;
  font-family: 'Barlow', sans-serif !important; font-size: 13px !important;
  font-weight: 500 !important; padding: 10px 20px !important;
  border-bottom: 2px solid transparent !important; margin-bottom: -2px !important;
}
[data-testid="stTabs"] [data-baseweb="tab"][aria-selected="true"] {
  color: var(--green) !important; border-bottom-color: var(--green) !important; font-weight: 700 !important;
}
[data-testid="stTabs"] [data-baseweb="tab-panel"] {
  background: var(--white) !important;
  border: 1px solid var(--border) !important; border-top: none !important;
  border-radius: 0 0 8px 8px !important; padding: 20px !important;
}

/* ════════════════════════════
   INPUTS
   ════════════════════════════ */
[data-testid="stNumberInput"] input, [data-testid="stTextInput"] input {
  background: var(--white) !important; border-color: var(--border) !important;
  color: var(--text) !important; border-radius: 6px !important;
}
[data-testid="stNumberInput"] label, [data-testid="stTextInput"] label,
[data-testid="stSelectbox"] label, [data-testid="stCheckbox"] label {
  color: var(--text-2) !important; font-size: 12px !important; font-weight: 600 !important;
}

/* ════════════════════════════
   BUTTONS (main area)
   ════════════════════════════ */
.main .stButton button[kind="primary"] {
  background: var(--green) !important; color: white !important;
  border: none !important; border-radius: 7px !important;
  font-weight: 700 !important; font-size: 13px !important;
  padding: 10px 24px !important;
  box-shadow: 0 2px 8px rgba(0,132,61,0.25) !important;
}
.main .stButton button[kind="primary"]:hover {
  background: var(--green-dk) !important; transform: translateY(-1px) !important;
}
.main .stButton button[kind="secondary"] {
  background: var(--white) !important; color: var(--text) !important;
  border: 1px solid var(--border) !important; border-radius: 7px !important;
}

/* ════════════════════════════
   METRICS
   ════════════════════════════ */
[data-testid="stMetric"] {
  background: var(--white) !important; border: 1px solid var(--border) !important;
  border-radius: 8px !important; padding: 14px 16px !important;
  box-shadow: var(--shadow-sm) !important;
}
[data-testid="stMetricLabel"] { color: var(--text-2) !important; font-size: 11px !important; font-weight: 600 !important; }
[data-testid="stMetricValue"] { color: var(--text) !important; font-family: 'Barlow Condensed', sans-serif !important; font-size: 26px !important; }

/* ════════════════════════════
   PLACEHOLDER PAGES
   ════════════════════════════ */
.placeholder-card {
  background: var(--white); border: 1px solid var(--border); border-radius: 12px;
  padding: 56px 40px; text-align: center; margin-top: 40px; box-shadow: var(--shadow-sm);
}
.placeholder-card .emoji { font-size: 52px; margin-bottom: 16px; }
.placeholder-card h2 {
  font-family: 'Barlow Condensed', sans-serif; font-size: 26px; font-weight: 700;
  color: var(--text); margin-bottom: 8px;
}
.placeholder-card p { font-size: 14px; color: var(--text-2); max-width: 400px; margin: 0 auto; line-height: 1.6; }
.badge-soon-green {
  display: inline-block; margin-top: 24px;
  background: var(--green-lt); color: var(--green-dk);
  border: 1px solid rgba(0,132,61,0.2); border-radius: 20px;
  padding: 5px 18px; font-size: 11px; font-weight: 700; letter-spacing: 1px;
}
.badge-soon-blue {
  display: inline-block; margin-top: 24px;
  background: var(--blue-lt); color: var(--blue);
  border: 1px solid rgba(21,101,192,0.2); border-radius: 20px;
  padding: 5px 18px; font-size: 11px; font-weight: 700; letter-spacing: 1px;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }

/* ── Misc ── */
hr { border-color: var(--border) !important; }
[data-baseweb="tag"] { background: var(--green-lt) !important; border-color: rgba(0,132,61,0.25) !important; }
[data-baseweb="tag"] span { color: var(--green-dk) !important; }
.stAlert { border-radius: 8px !important; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PERSISTENCE & UTILS
# ══════════════════════════════════════════════════════════════════════════════
CACHE_DIR  = ".ocp_cache"
JORF_CACHE = os.path.join(CACHE_DIR, "jorf.pkl")
SAFI_CACHE = os.path.join(CACHE_DIR, "safi.pkl")
HIST_JORF  = os.path.join(CACHE_DIR, "hist_jorf.json")
HIST_SAFI  = os.path.join(CACHE_DIR, "hist_safi.json")
HIST_FILES = os.path.join(CACHE_DIR, "hist_files")
os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(HIST_FILES, exist_ok=True)

def save_cache(path, data):
    with open(path, "wb") as f: pickle.dump(data, f)

def load_cache(path):
    if os.path.exists(path):
        try:
            with open(path, "rb") as f: return pickle.load(f)
        except: pass
    return None

def clear_cache(path):
    if os.path.exists(path): os.remove(path)

def load_historique(hist_path):
    if os.path.exists(hist_path):
        try:
            with open(hist_path, "r", encoding="utf-8") as f: return json.load(f)
        except: pass
    return []

def save_historique(hist_path, hist_list):
    with open(hist_path, "w", encoding="utf-8") as f:
        json.dump(hist_list, f, ensure_ascii=False, indent=2)

def add_to_historique(hist_path, filename, file_bytes, file_type):
    hist = load_historique(hist_path)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    phys_path = os.path.join(HIST_FILES, f"{file_type}_{ts}_{filename.replace(' ','_')}")
    with open(phys_path, "wb") as f: f.write(file_bytes)
    entry = {"filename": filename, "date_upload": datetime.now().strftime("%d/%m/%Y %H:%M"),
             "path": phys_path, "type": file_type}
    hist = [h for h in hist if not (h["filename"] == filename and h["date_upload"][:10] == entry["date_upload"][:10])]
    hist.insert(0, entry)
    save_historique(hist_path, hist[:20])
    return phys_path

def load_from_hist_entry(entry):
    path = entry.get("path", "")
    if os.path.exists(path):
        with open(path, "rb") as f: return f.read()
    return None

# ── Data helpers ──
NOMS_MOIS  = {1:"Jan",2:"Fev",3:"Mar",4:"Avr",5:"Mai",6:"Jun",7:"Jul",8:"Aou",9:"Sep",10:"Oct",11:"Nov",12:"Dec"}
ORDRE_MOIS = {v:k for k,v in NOMS_MOIS.items()}

def force_nombre(v):
    if pd.isna(v): return 0.0
    if isinstance(v,(int,float)): return 0.0 if abs(v)<1e-6 else float(v)
    s=str(v).strip()
    if s in("-","","nan"): return 0.0
    n=re.sub(r'[^\d]','',s.replace("\xa0","").replace(" ",""))
    if len(n)>12: return 0.0
    try: return float(n)
    except: return 0.0

def en_milliers(v): return round(v/1000,1)
def fmt_number(n):  return f"{n:,.1f}".replace(",", "\u202f")

def date_sort_key(d):
    try: p=str(d).split("/"); return (int(p[2]),int(p[1]),int(p[0]))
    except: return (9999,99,99)

def mois_sort_key(m):
    try: p=m.split(); return (int(p[1]),ORDRE_MOIS.get(p[0],99))
    except: return (9999,99)

def extract_mois_label(date_str):
    try:
        p=str(date_str).split("/")
        if len(p)==3: return f"{NOMS_MOIS.get(int(p[1]),'?')} {p[2]}"
    except: pass
    return "Inconnu"

SKIP_KW = ["total","recap","recapitulatif","annee","annuel","bilan","synthese","summary"]
def is_data_sheet(n): return not any(k in n.strip().lower() for k in SKIP_KW)

def detect_engine(raw):
    for e in ['openpyxl','pyxlsb','calamine']:
        try: pd.ExcelFile(io.BytesIO(raw),engine=e); return e
        except: continue
    raise ValueError("Impossible de lire ce fichier.")

def read_file_bytes(file):
    file.seek(0); raw=file.read()
    fn=getattr(file,'name','').lower().strip()
    if fn.endswith('.xlsb'): return raw,'pyxlsb'
    if fn.endswith(('.xlsm','.xlsx')):
        try: pd.ExcelFile(io.BytesIO(raw),engine='openpyxl'); return raw,'openpyxl'
        except: pass
    if fn.endswith('.xls'):
        try: pd.ExcelFile(io.BytesIO(raw),engine='calamine'); return raw,'calamine'
        except: pass
    return raw,detect_engine(raw)

def get_derniere_valeur(df,col,col_date="Date"):
    if df is None or df.empty: return 0.0,None
    tmp=df[df[col]>0].copy()
    if tmp.empty: return 0.0,None
    tmp["_s"]=tmp[col_date].apply(date_sort_key)
    last=tmp.sort_values("_s").iloc[-1]
    return round(float(last[col]),1),last[col_date]

def appliquer_filtre(df,sel,col="Date"):
    if not sel: return df
    return df[df[col].isin(sel)]

# ── Plotly theme ──
PLOT_LAYOUT = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(247,248,250,0.8)',
    font=dict(family='Barlow, sans-serif', color='#5A6A7A'),
    xaxis=dict(gridcolor='#E2E6EA', linecolor='#E2E6EA', tickfont=dict(color='#5A6A7A',size=11)),
    yaxis=dict(gridcolor='#E2E6EA', linecolor='#E2E6EA', tickfont=dict(color='#5A6A7A',size=11)),
    legend=dict(bgcolor='rgba(255,255,255,0.9)', bordercolor='#E2E6EA', borderwidth=1,
                font=dict(color='#1A2332', size=11)),
    margin=dict(l=16,r=16,t=40,b=16),
    height=360,
)

# ══════════════════════════════════════════════════════════════════════════════
# PARSERS
# ══════════════════════════════════════════════════════════════════════════════
def parse_jorf(raw_bytes,engine):
    df_raw=pd.read_excel(io.BytesIO(raw_bytes),sheet_name='EXPORT',header=None,engine=engine)
    coords={"ENGRAIS":None,"CAMIONS":None,"VL":None}
    for r in range(len(df_raw)):
        lbl=" ".join(df_raw.iloc[r,0:3].astype(str)).upper()
        if "EXPORT ENGRAIS" in lbl: coords["ENGRAIS"]=r
        if "EXPORT CAMIONS" in lbl: coords["CAMIONS"]=r
        if "VL CAMIONS"     in lbl: coords["VL"]=r
    ld=df_raw.iloc[2,:]
    cd=[j for j in range(3,len(ld)) if pd.notna(ld[j])]
    rows=[]
    for j in cd:
        dt=ld[j]; dl=dt.strftime('%d/%m/%Y') if hasattr(dt,'strftime') else str(dt).split(" ")[0]
        v1=en_milliers(force_nombre(df_raw.iloc[coords["ENGRAIS"],j])) if coords["ENGRAIS"] is not None else 0.0
        v2=en_milliers(force_nombre(df_raw.iloc[coords["CAMIONS"],j])) if coords["CAMIONS"] is not None else 0.0
        v3=en_milliers(force_nombre(df_raw.iloc[coords["VL"],j]))      if coords["VL"]      is not None else 0.0
        rows.append({"Date":dl,"Export Engrais":v1,"Export Camions":v2,"VL Camions":v3,"TOTAL Jorf":round(v1+v2+v3,1)})
    return pd.DataFrame(rows)

def parse_rade(raw_bytes,engine):
    df=pd.read_excel(io.BytesIO(raw_bytes),sheet_name='Sit Navire',header=None,engine=engine)
    rows=[]
    for r in range(len(df)):
        dv=df.iloc[r,1]; val=df.iloc[r,3]
        if pd.isna(dv) or pd.isna(val): continue
        sd=str(dv).strip()
        if sd in("","nan","Date"): continue
        dl=dv.strftime('%d/%m/%Y') if hasattr(dv,'strftime') else sd
        rows.append({"Date":dl,"Engrais en attente":en_milliers(force_nombre(val))})
    return pd.DataFrame(rows) if rows else None

def parse_safi(raw_bytes,engine):
    xl=pd.ExcelFile(io.BytesIO(raw_bytes),engine=engine)
    CJ=1; CE=31; CM=32; SR=6
    def norm(s):
        acc={"é":"e","è":"e","ê":"e","ë":"e","à":"a","â":"a","ù":"u","û":"u","ô":"o","î":"i","ï":"i","ç":"c","ü":"u","ö":"o"}
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
        if not is_data_sheet(sheet): continue
        mn,an=pm(sheet)
        if mn is None or an is None: continue
        dfs=pd.read_excel(io.BytesIO(raw_bytes),sheet_name=sheet,header=None,engine=engine)
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
            te=en_milliers(force_nombre(dfs.iloc[ri,tec])) if tec<dfs.shape[1] else 0.0
            tm=en_milliers(force_nombre(dfs.iloc[ri,tml])) if tml<dfs.shape[1] else 0.0
            rows.append({"Mois":sheet,"Jour":jn,"Date":f"{jn:02d}/{mn:02d}/{an}","TSP Export":te,"TSP ML":tm,"TOTAL Safi":round(te+tm,1)})
    return pd.DataFrame(rows) if rows else None

def charger_jorf(raw_bytes, filename):
    ff=io.BytesIO(raw_bytes); ff.name=filename
    raw,eng=read_file_bytes(ff)
    jd=parse_jorf(raw,eng); rd=None
    try: rd=parse_rade(raw,eng)
    except: pass
    st.session_state.update({"jorf_df":jd,"rade_df":rd,"jorf_name":filename})
    save_cache(JORF_CACHE,{"jorf_df":jd,"rade_df":rd,"filename":filename})
    return jd

def charger_safi(raw_bytes, filename):
    ff=io.BytesIO(raw_bytes); ff.name=filename
    raw,eng=read_file_bytes(ff)
    sd=parse_safi(raw,eng)
    st.session_state.update({"safi_df":sd,"safi_name":filename})
    save_cache(SAFI_CACHE,{"safi_df":sd,"filename":filename})
    return sd

# ══════════════════════════════════════════════════════════════════════════════
# SESSION STATE INIT
# ══════════════════════════════════════════════════════════════════════════════
if "page" not in st.session_state:
    st.session_state["page"] = "suivi"

if "jorf_loaded" not in st.session_state:
    c=load_cache(JORF_CACHE)
    if c:
        st.session_state["jorf_df"]  =c.get("jorf_df")
        st.session_state["rade_df"]  =c.get("rade_df")
        st.session_state["jorf_name"]=c.get("filename","")
    st.session_state["jorf_loaded"]=True

if "safi_loaded" not in st.session_state:
    c=load_cache(SAFI_CACHE)
    if c:
        st.session_state["safi_df"]  =c.get("safi_df")
        st.session_state["safi_name"]=c.get("filename","")
    st.session_state["safi_loaded"]=True

jorf_df = st.session_state.get("jorf_df",None)
rade_df = st.session_state.get("rade_df",None)
safi_df = st.session_state.get("safi_df",None)

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR — VERTICAL NAVIGATION
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    # Logo — image OCP si disponible, sinon placeholder vert
    if os.path.exists("logo_ocp.png"):
        import base64 as _b64
        logo_b64 = _b64.b64encode(open("logo_ocp.png","rb").read()).decode()
        logo_html = f'<img src="data:image/png;base64,{logo_b64}" class="nav-logo-img"/>'
    else:
        logo_html = '<div class="nav-logo-box">OCP</div>'

    st.markdown(f"""
    <div class="nav-logo">
        {logo_html}
        <div>
            <div class="nav-logo-name">OCP</div>
            <div class="nav-logo-sub">Manufacturing</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Navigation ──
    st.markdown('<div class="nav-sep">Navigation</div>', unsafe_allow_html=True)

    NAV_ITEMS = [
        ("suivi",    "🏭",  "Suivi Chargement"),
        ("stock",    "📦",  "Simulation Stock"),
        ("ventes",   "📊",  "Pipeline des Ventes"),
        ("navires",  "🚢",  "Export Navire"),
    ]

    for key, icon, label in NAV_ITEMS:
        is_active = st.session_state["page"] == key
        btn_type = "primary" if is_active else "secondary"
        if st.button(f"{icon}  {label}", key=f"nav_{key}", type=btn_type, use_container_width=True):
            st.session_state["page"] = key
            st.rerun()

    st.markdown('<div class="nav-hr"></div>', unsafe_allow_html=True)

    # ── Files ──
    st.markdown('<div class="nav-sep">Fichiers de données</div>', unsafe_allow_html=True)

    EXCEL_TYPES = ["xlsx","xls","xlsm","xlsb"]
    jorf_name = st.session_state.get("jorf_name","")
    safi_name = st.session_state.get("safi_name","")

    # Status indicators
    dot_j = '<span class="status-dot ok"></span>' if jorf_name else '<span class="status-dot none"></span>'
    dot_s = '<span class="status-dot ok"></span>' if safi_name else '<span class="status-dot none"></span>'
    st.markdown(f"""
    <div style="padding:8px 12px 4px 16px;font-size:11px;color:#5A6A7A">
      {dot_j} Jorf : <span style="color:{'#00843D' if jorf_name else '#9AAABB'};font-weight:600">{jorf_name or '—'}</span><br/>
      {dot_s} Safi : <span style="color:{'#00843D' if safi_name else '#9AAABB'};font-weight:600">{safi_name or '—'}</span>
    </div>
    """, unsafe_allow_html=True)

    file_jorf = st.file_uploader("📂 Charger Jorf", type=EXCEL_TYPES, key="jorf_up")
    file_safi = st.file_uploader("📂 Charger Safi", type=EXCEL_TYPES, key="safi_up")

    if file_jorf:
        try:
            jb,eng=read_file_bytes(file_jorf)
            jd=parse_jorf(jb,eng); rd=None
            try: rd=parse_rade(jb,eng)
            except: pass
            clear_cache(JORF_CACHE)
            st.session_state.update({"jorf_df":jd,"rade_df":rd,"jorf_name":file_jorf.name})
            save_cache(JORF_CACHE,{"jorf_df":jd,"rade_df":rd,"filename":file_jorf.name})
            file_jorf.seek(0); add_to_historique(HIST_JORF,file_jorf.name,file_jorf.read(),"jorf")
            jorf_df=jd; rade_df=rd
            st.success("✅ Jorf chargé")
        except Exception as e: st.error(f"Erreur : {e}")

    if file_safi:
        try:
            sb,eng=read_file_bytes(file_safi)
            sd=parse_safi(sb,eng)
            clear_cache(SAFI_CACHE)
            st.session_state.update({"safi_df":sd,"safi_name":file_safi.name})
            save_cache(SAFI_CACHE,{"safi_df":sd,"filename":file_safi.name})
            file_safi.seek(0); add_to_historique(HIST_SAFI,file_safi.name,file_safi.read(),"safi")
            safi_df=sd
            if sd is not None:
                st.success("✅ Safi chargé")
            else:
                st.warning("Aucune feuille mensuelle détectée.")
        except Exception as e: st.error(f"Erreur : {e}")

    st.markdown('<div class="nav-hr"></div>', unsafe_allow_html=True)

    # ── Historique ──
    st.markdown('<div class="nav-sep">Historique</div>', unsafe_allow_html=True)
    hist_jorf = load_historique(HIST_JORF)
    hist_safi = load_historique(HIST_SAFI)

    if hist_jorf:
        with st.expander(f"Jorf ({len(hist_jorf)})", expanded=False):
            for i,entry in enumerate(hist_jorf):
                is_active=entry["filename"]==st.session_state.get("jorf_name","")
                c1,c2=st.columns([3,1])
                with c1:
                    dot='🟢' if is_active else '⬜'
                    st.markdown(f"<div style='font-size:11px;color:#1A2332'>{dot} {entry['filename']}<br/><span style='color:#9AAABB;font-size:10px'>{entry['date_upload']}</span></div>",unsafe_allow_html=True)
                with c2:
                    if not is_active:
                        if st.button("↩️",key=f"rj_{i}"):
                            raw=load_from_hist_entry(entry)
                            if raw:
                                try: charger_jorf(raw,entry["filename"]); st.rerun()
                                except Exception as e: st.error(str(e))
                            else: st.error("Introuvable.")
    if hist_safi:
        with st.expander(f"Safi ({len(hist_safi)})", expanded=False):
            for i,entry in enumerate(hist_safi):
                is_active=entry["filename"]==st.session_state.get("safi_name","")
                c1,c2=st.columns([3,1])
                with c1:
                    dot='🟢' if is_active else '⬜'
                    st.markdown(f"<div style='font-size:11px;color:#1A2332'>{dot} {entry['filename']}<br/><span style='color:#9AAABB;font-size:10px'>{entry['date_upload']}</span></div>",unsafe_allow_html=True)
                with c2:
                    if not is_active:
                        if st.button("↩️",key=f"rs_{i}"):
                            raw=load_from_hist_entry(entry)
                            if raw:
                                try: charger_safi(raw,entry["filename"]); st.rerun()
                                except Exception as e: st.error(str(e))
                            else: st.error("Introuvable.")

    # ── Filtres (Suivi seulement) ──
    if st.session_state["page"] == "suivi":
        st.markdown('<div class="nav-hr"></div>', unsafe_allow_html=True)
        st.markdown('<div class="nav-sep">Filtres — Suivi</div>', unsafe_allow_html=True)

        def filtre_sidebar(df, label, key):
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
            mois_tries=sorted(mois_map.keys(),key=mois_sort_key)
            options=[m if mois_map[m] else f"{m} —" for m in mois_tries]
            mode=st.radio(label,["Tout","Mois","Dates"],horizontal=True,key=f"{key}_mode")
            if mode=="Tout": return [],"Toute la période"
            elif mode=="Mois":
                choix=st.multiselect("Mois",options=options,default=[],key=f"{key}_mois")
                if not choix: return [],"Toute la période"
                ds=[]; lb=[]
                for m in choix:
                    cle=m.rstrip(" —"); ds+=mois_map.get(cle,[]); lb.append(cle)
                return ds,", ".join(lb)
            else:
                all_d=sorted(df["Date"].unique().tolist(),key=lambda d:tuple(int(x) for x in str(d).split("/"))[::-1])
                choix=st.multiselect("Dates",all_d,key=f"{key}_dates")
                if not choix: return [],"Toute la période"
                return choix,f"{len(choix)} date(s)"

        if jorf_df is not None:
            st.markdown("**Jorf Lasfar**")
            sel_jorf,label_jorf=filtre_sidebar(jorf_df,"Jorf","jorf")
        else: sel_jorf,label_jorf=[],"Toute la période"

        if safi_df is not None:
            st.markdown("**Safi**")
            sel_safi,label_safi=filtre_sidebar(safi_df,"Safi","safi")
        else: sel_safi,label_safi=[],"Toute la période"

        st.session_state["sel_jorf"]=sel_jorf
        st.session_state["label_jorf"]=label_jorf
        st.session_state["sel_safi"]=sel_safi
        st.session_state["label_safi"]=label_safi

# Re-read data after possible upload
jorf_df = st.session_state.get("jorf_df",None)
rade_df = st.session_state.get("rade_df",None)
safi_df = st.session_state.get("safi_df",None)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE ROUTER
# ══════════════════════════════════════════════════════════════════════════════
page = st.session_state["page"]

PAGE_TITLES = {
    "suivi":   ("🏭 Suivi Chargement",   "Jorf Lasfar & Safi — Données consolidées par jour"),
    "stock":   ("📦 Simulation de Stock","Projection matières premières — navires & consommation"),
    "ventes":  ("📊 Pipeline des Ventes","Suivi des opportunités et performances commerciales"),
    "navires": ("🚢 Export Navire",       "Planification et suivi des chargements navires"),
}
title, subtitle = PAGE_TITLES[page]

# Top bar
st.markdown(f"""
<div class="topbar">
  <div class="topbar-left">
    <div>
      <div class="topbar-title">{title}</div>
      <div class="topbar-breadcrumb">OCP Manufacturing &nbsp;›&nbsp; {title.split(' ',1)[1]}</div>
    </div>
  </div>
  <div class="topbar-badge">{subtitle}</div>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: SUIVI CHARGEMENT
# ══════════════════════════════════════════════════════════════════════════════
if page == "suivi":
    sel_jorf   = st.session_state.get("sel_jorf",  [])
    label_jorf = st.session_state.get("label_jorf","Toute la période")
    sel_safi   = st.session_state.get("sel_safi",  [])
    label_safi = st.session_state.get("label_safi","Toute la période")

    jorf_kpi = appliquer_filtre(jorf_df,sel_jorf) if jorf_df is not None else None
    safi_kpi = appliquer_filtre(safi_df,sel_safi) if safi_df is not None else None
    rade_kpi = appliquer_filtre(rade_df,sel_jorf) if rade_df is not None else None

    cumul_jorf  = round(float(jorf_kpi["TOTAL Jorf"].sum()),1) if jorf_kpi is not None else 0.0
    cumul_safi  = round(float(safi_kpi["TOTAL Safi"].sum()),1) if safi_kpi is not None else 0.0
    cumul_total = round(cumul_jorf+cumul_safi,1)
    rade_j_val,rade_j_date = get_derniere_valeur(rade_kpi,"Engrais en attente") if rade_kpi is not None else (0.0,None)

    # KPI row
    k1,k2,k3,k4 = st.columns(4)
    def kpi(col, color, icon, label, value, sub, extra=""):
        with col:
            st.markdown(f"""
            <div class="kpi-card {color}">
                <span class="kpi-icon">{icon}</span>
                <div class="kpi-label">{label}</div>
                <div class="kpi-value {color}">{fmt_number(value)}<span class="kpi-unit">KT</span></div>
                <div class="kpi-sub">{sub}</div>
                {f'<div style="font-size:10px;color:var(--text-3);margin-top:4px">{extra}</div>' if extra else ''}
            </div>""", unsafe_allow_html=True)

    kpi(k1,"green","🏭","Total Jorf",cumul_jorf,
        "Export Engrais · Camions · VL" if jorf_df is not None else "Fichier non chargé")
    with k2:
        if rade_df is not None and rade_j_date:
            st.markdown(f"""
            <div class="kpi-card purple">
                <span class="kpi-icon">⚓</span>
                <div class="kpi-label">Rade Jorf</div>
                <div class="kpi-value purple">{fmt_number(rade_j_val)}<span class="kpi-unit">KT</span></div>
                <div class="kpi-sub">Engrais en attente</div>
                <div style="font-size:10px;color:var(--text-2);margin-top:4px">📅 {rade_j_date}</div>
            </div>""", unsafe_allow_html=True)
        else:
            kpi(k2,"purple","⚓","Rade Jorf",0.0,"Fichier non chargé")
    kpi(k3,"blue","🌊","Total Safi",cumul_safi,
        "TSP Export · TSP ML" if safi_df is not None else "Fichier non chargé")
    kpi(k4,"orange","📊","Jorf + Safi",cumul_total,"Consolidé toutes unités")

    st.markdown("<div style='margin-top:8px'></div>", unsafe_allow_html=True)

    # Table consolidated
    st.markdown('<div class="section-title">Tableau consolidé — par jour (KT)</div>', unsafe_allow_html=True)

    any_data = jorf_df is not None or safi_df is not None or rade_df is not None
    if any_data:
        jorf_f = appliquer_filtre(jorf_df,sel_jorf) if jorf_df is not None else None
        rade_f = appliquer_filtre(rade_df,sel_jorf) if rade_df is not None else None
        safi_f = appliquer_filtre(safi_df,sel_safi) if safi_df is not None else None

        all_dates=set()
        if jorf_f is not None: all_dates|=set(jorf_f["Date"].unique())
        if rade_f is not None: all_dates|=set(rade_f["Date"].unique())
        if safi_f is not None: all_dates|=set(safi_f["Date"].unique())
        all_dates=sorted(all_dates,key=date_sort_key)

        unified_rows=[]
        for d in all_dates:
            row={"Date":d}
            if jorf_f is not None:
                r=jorf_f[jorf_f["Date"]==d]
                row["J_Engrais"]=round(r["Export Engrais"].sum(),1) if not r.empty else 0.0
                row["J_Camions"]=round(r["Export Camions"].sum(),1) if not r.empty else 0.0
                row["J_VL"]     =round(r["VL Camions"].sum(),1)     if not r.empty else 0.0
            if safi_f is not None:
                r=safi_f[safi_f["Date"]==d]
                row["S_Engrais"]=round(r["TSP Export"].sum(),1) if not r.empty else 0.0
                row["S_VL"]     =round(r["TSP ML"].sum(),1)     if not r.empty else 0.0
            jt=round(row.get("J_Engrais",0)+row.get("J_Camions",0)+row.get("J_VL",0),1) if jorf_f is not None else 0.0
            st_=round(row.get("S_Engrais",0)+row.get("S_VL",0),1) if safi_f is not None else 0.0
            if jorf_f is not None: row["J_TOTAL"]=jt
            if safi_f is not None: row["S_TOTAL"]=st_
            row["TOTAL"]=round(jt+st_,1)
            if rade_f is not None:
                r=rade_f[rade_f["Date"]==d]
                row["RADE_J"]=round(r["Engrais en attente"].sum(),1) if not r.empty else 0.0
            unified_rows.append(row)

        unified_df=pd.DataFrame(unified_rows)
        col_order=["Date"]
        if jorf_f is not None: col_order+=["J_Engrais","J_Camions","J_VL","J_TOTAL"]
        if safi_f is not None: col_order+=["S_Engrais","S_VL","S_TOTAL"]
        col_order+=["TOTAL"]
        if rade_f is not None: col_order+=["RADE_J"]
        col_order=[c for c in col_order if c in unified_df.columns]
        unified_df=unified_df[col_order]

        total_row={"Date":"TOTAL GÉNÉRAL"}
        for col in unified_df.columns:
            if col=="Date": continue
            elif col=="RADE_J": total_row[col]=None
            else: total_row[col]=round(unified_df[col].sum(),1)
        disp=pd.concat([unified_df,pd.DataFrame([total_row])],ignore_index=True)

        col_cfg={"Date":st.column_config.TextColumn("Date",width=90)}
        names={"J_Engrais":"Engrais","J_Camions":"Camions","J_VL":"VL","J_TOTAL":"▶ Total Jorf",
               "S_Engrais":"Engrais","S_VL":"TSP ML","S_TOTAL":"▶ Total Safi",
               "TOTAL":"▶ Total Cumulé","RADE_J":"Rade Jorf"}
        for c,n in names.items():
            if c in disp.columns:
                col_cfg[c]=st.column_config.NumberColumn(n,format="%.1f")

        st.dataframe(disp,use_container_width=True,hide_index=True,
                     height=min(680,45+35*len(disp)),column_config=col_cfg)

        # Copy buttons
        cb1,cb2,cb3,_ = st.columns([1,1,1,2])
        def copy_btn(container, df, col, label, key):
            vals = df[df["Date"]!="TOTAL GÉNÉRAL"][col].dropna().tolist()
            txt = "\t".join(str(round(v,1)) for v in vals)
            bid = f"cbtn_{key}"
            with container:
                st.components.v1.html(f"""
                <button class="copy-btn" id="{bid}"
                  onclick="navigator.clipboard.writeText('{txt}').then(()=>{{
                    this.innerHTML='✓ Copié'; this.classList.add('copied');
                    setTimeout(()=>{{this.innerHTML='📋 {label}'; this.classList.remove('copied')}},2000)
                  }})">📋 {label}</button>
                <style>.copy-btn{{background:#F7F8FA;color:#5A6A7A;border:1px solid #E2E6EA;padding:6px 14px;border-radius:6px;cursor:pointer;font-size:12px;font-weight:600;font-family:Barlow,sans-serif;transition:all .15s}}.copy-btn:hover,.copy-btn.copied{{background:#E8F5EE;color:#005C2A;border-color:rgba(0,132,61,.3)}}</style>
                """, height=40)

        if jorf_f is not None and "J_TOTAL" in unified_df.columns:
            copy_btn(cb1, unified_df, "J_TOTAL", "Copier Jorf", "jorf")
        if safi_f is not None and "S_TOTAL" in unified_df.columns:
            copy_btn(cb2, unified_df, "S_TOTAL", "Copier Safi", "safi")
        if "TOTAL" in unified_df.columns:
            copy_btn(cb3, unified_df, "TOTAL", "Copier Total", "total")

        # Charts
        st.markdown("<div style='margin-top:8px'></div>",unsafe_allow_html=True)
        g1,g2 = st.columns(2)

        with g1:
            st.markdown('<div class="section-title purple">Rade Jorf — Engrais en attente</div>', unsafe_allow_html=True)
            if rade_f is not None and "RADE_J" in unified_df.columns:
                rc=unified_df[unified_df["RADE_J"]>0].copy()
                if len(rc)>0:
                    fig=go.Figure()
                    fig.add_trace(go.Bar(x=rc["Date"],y=rc["RADE_J"],name="Rade Jorf",
                        marker=dict(color="#8B5CF6",opacity=0.85),
                        hovertemplate='<b>%{x}</b><br>Rade : %{y:.1f} KT<extra></extra>'))
                    fig.update_layout(**PLOT_LAYOUT,title=dict(text="Rade Jorf (KT)",font=dict(size=13,color="#5A6A7A")))
                    st.plotly_chart(fig,use_container_width=True)
                else: st.info("Pas de données Rade disponibles.")
            else: st.info("Chargez le fichier Jorf pour voir la Rade.")

        with g2:
            st.markdown('<div class="section-title">Production journalière — Jorf vs Safi</div>', unsafe_allow_html=True)
            djs=[c for c in ["J_TOTAL","S_TOTAL"] if c in unified_df.columns]
            names_={"J_TOTAL":"Jorf","S_TOTAL":"Safi"}
            if djs and len(unified_df)>1:
                fig=go.Figure()
                for c in djs:
                    clr = "#00843D" if c=="J_TOTAL" else "#1565C0"
                    fill_clr = "rgba(0,132,61,0.07)" if c=="J_TOTAL" else "rgba(21,101,192,0.07)"
                    fig.add_trace(go.Scatter(x=unified_df["Date"],y=unified_df[c],mode='lines',
                        name=names_[c],line=dict(color=clr,width=2),fill='tozeroy',
                        fillcolor=fill_clr,
                        hovertemplate=f'<b>%{{x}}</b><br>{names_[c]}: %{{y:.1f}} KT<extra></extra>'))
                fig.update_layout(**PLOT_LAYOUT,title=dict(text="Total Jorf & Safi (KT/jour)",font=dict(size=13,color="#5A6A7A")))
                st.plotly_chart(fig,use_container_width=True)
            else: st.info("Chargez les fichiers pour voir les graphiques.")
    else:
        st.info("Chargez au moins un fichier Excel depuis la barre latérale pour commencer.")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: SIMULATION DE STOCK
# ══════════════════════════════════════════════════════════════════════════════
elif page == "stock":

    def simulation_stock(si, cj, navires, retards, conso_reelle=None):
        navires=sorted(navires,key=lambda x:x[0])
        today=pd.Timestamp.today()
        debut=pd.Timestamp(today.year,today.month,1)
        cal=pd.date_range(start=debut,end=debut+pd.DateOffset(days=60),freq='D')
        stock=si; sv=[]; dates=[]; nav_arr=[]; nav_qty=[]
        for jour in cal:
            for (dp,qty) in navires:
                de=dp+pd.Timedelta(days=retards.get(dp,0))
                if jour==de: stock+=qty; nav_arr.append(jour); nav_qty.append(qty)
            conso=conso_reelle.get(jour.date(),cj) if conso_reelle else cj
            stock-=conso; sv.append(stock); dates.append(jour)
        return dates,sv,nav_arr,nav_qty

    def afficher_sim(dates,sv,nav_arr,nav_qty,titre,seuil=36000):
        fig=go.Figure()
        # Critical zone
        fig.add_hrect(y0=0,y1=seuil,fillcolor="rgba(232,72,90,0.06)",line_width=0)
        # Stock line
        colors=['#00C46A' if v>=seuil else '#E8485A' for v in sv]
        fig.add_trace(go.Scatter(x=dates,y=sv,mode='lines',name='Stock',
            line=dict(color='#00843D',width=2.5),fill='tozeroy',
            fillcolor='rgba(0,132,61,0.07)',
            hovertemplate='<b>%{x|%d/%m/%Y}</b><br>Stock : %{y:,.0f} T<extra></extra>'))
        fig.add_trace(go.Scatter(x=dates,y=[seuil]*len(dates),mode='lines',
            name=f'Seuil ({seuil:,} T)',line=dict(dash='dash',color='#C62828',width=1.5)))
        for i,date in enumerate(nav_arr):
            idx=dates.index(date)
            fig.add_trace(go.Scatter(x=[date],y=[sv[idx]],mode='markers+text',
                name=f'Navire {i+1}',
                marker=dict(symbol='triangle-up',color='#1A9ED4',size=14,
                           line=dict(color='white',width=1.5)),
                text=[f"+{nav_qty[i]:,} T"],textposition='top center',
                textfont=dict(size=11,color='#1A9ED4'),showlegend=True))
        layout=dict(**PLOT_LAYOUT)
        layout['height']=400
        layout['title']=dict(text=titre,font=dict(size=15,color='#1A2332'))
        fig.update_layout(**layout)
        st.plotly_chart(fig,use_container_width=True)
        # Stats
        m1,m2,m3=st.columns(3)
        mn_v=min(sv); mn_d=dates[sv.index(mn_v)]
        jc=sum(1 for v in sv if v<seuil)
        m1.metric("Stock minimum",f"{mn_v:,.0f} T",f"le {mn_d.strftime('%d/%m/%Y')}")
        m2.metric("Stock final",f"{sv[-1]:,.0f} T")
        m3.metric(f"Jours critiques (<{seuil//1000}k T)",f"{jc} j",delta=f"{'⚠️' if jc>0 else '✅'}")

    tab_safi,tab_jorf = st.tabs(["🌊  Site de Safi","⚓  Site de Jorf"])

    # ── SAFI ──
    with tab_safi:
        mat_s=st.selectbox("Matière première (Safi)",["Soufre"],key="sim_safi_mat")
        ps=f"ss_{mat_s.lower()}"
        c1,c2=st.columns(2)
        with c1: si_s=st.number_input("Stock initial (T)",key=f"{ps}_si",min_value=0,value=40000,step=1000)
        with c2: cj_s=st.number_input("Consommation journalière (T)",key=f"{ps}_cj",min_value=0,value=3600,step=100)
        ucr_s=st.checkbox("Utiliser des consommations journalières réelles ?",key=f"{ps}_ucr")
        cr_s={}
        if ucr_s:
            st.markdown('<div class="section-title">Consommation réelle par jour</div>',unsafe_allow_html=True)
            dm=pd.Timestamp.today().replace(day=1)
            jours=pd.date_range(dm,dm+pd.offsets.MonthEnd(1),freq='D')
            cols4=st.columns(4)
            for i,j in enumerate(jours):
                with cols4[i%4]:
                    cr_s[j.date()]=st.number_input(j.strftime('%d/%m'),min_value=0,value=int(cj_s),step=100,key=f"{ps}_cr_{j.strftime('%Y%m%d')}")
        st.markdown('<div class="section-title blue">Navires prévus</div>',unsafe_allow_html=True)
        nav_s,ret_s=[],{}
        nn=st.number_input("Nombre de navires",key=f"{ps}_n",min_value=0,value=3)
        for i in range(int(nn)):
            cd,cq,cr=st.columns(3)
            with cd: da=st.date_input(f"Date navire {i+1}",pd.Timestamp.today(),key=f"{ps}_d{i}")
            with cq: qty=st.number_input(f"Quantité {i+1} (T)",0,500000,30000,1000,key=f"{ps}_q{i}")
            with cr: ret=st.number_input(f"Retard (j) {i+1}",0,30,0,1,key=f"{ps}_r{i}")
            nav_s.append((pd.Timestamp(da),qty))
            if ret>0: ret_s[pd.Timestamp(da)]=ret
        if st.button(f"🚀 Lancer la simulation — Safi ({mat_s})",key=f"{ps}_btn",type="primary"):
            d,sv,na,nq=simulation_stock(si_s,cj_s,nav_s,ret_s,cr_s if ucr_s else None)
            afficher_sim(d,sv,na,nq,f"Évolution du stock — Safi / {mat_s}")

    # ── JORF ──
    with tab_jorf:
        mat_j=st.selectbox("Matière première",["Soufre","NH3","KCL","ACS"],key="sim_jorf_mat")
        pj=f"sj_{mat_j.lower()}"

        if mat_j=="ACS":
            st.markdown('<div class="section-title">Paramètres généraux ACS</div>',unsafe_allow_html=True)
            c1,c2,c3,c4=st.columns(4)
            with c1: ce_acs=st.number_input("Conso engrais (T)",key=f"{pj}_ce",min_value=0,value=12000)
            with c2: si_acs=st.number_input("Stock initial (T)",key=f"{pj}_si",min_value=0,value=300000)
            with c3: rade_v=st.number_input("Rade (T)",key=f"{pj}_rade",min_value=0,value=60000)
            with c4: dech=st.number_input("Déchargement (T)",key=f"{pj}_dech",min_value=0,value=300000)

            dm=pd.Timestamp.today().replace(day=1)
            cal_acs=pd.date_range(start=dm,end=dm+pd.DateOffset(days=60),freq='D')
            prod_jj={d.normalize():0 for d in cal_acs}

            def render_lignes(lignes, prefix, default_cad):
                prod_tot=0
                for i,ligne in enumerate(st.tabs([f"{l}" for l in lignes])):
                    with ligne:
                        la=lignes[i]
                        jal=st.text_input(f"Jours d'arrêt (ex: 1-3,15)",key=f"{prefix}_{la}_ar")
                        jar=[]
                        if jal:
                            for part in jal.split(","):
                                part=part.strip()
                                if "-" in part:
                                    a_,b_=part.split("-"); jar.extend(range(int(a_),int(b_)+1))
                                else: jar.append(int(part))
                            jar=sorted(set(jar))
                        nb=st.number_input(f"Périodes",min_value=1,value=1,key=f"{prefix}_{la}_nb")
                        plt=0
                        for p in range(int(nb)):
                            ca,cb,cc=st.columns(3)
                            with ca: dd=st.date_input(f"Début {p+1}",dm,key=f"{prefix}_{la}_dd{p}")
                            with cb: df__=st.date_input(f"Fin {p+1}",dm+pd.Timedelta(days=5),key=f"{prefix}_{la}_df{p}")
                            with cc: cad=st.number_input(f"Cadence T/j",min_value=0,value=default_cad,key=f"{prefix}_{la}_cad{p}")
                            for d in pd.date_range(pd.Timestamp(dd),pd.Timestamp(df__),freq='D'):
                                if d.day not in jar:
                                    prod_jj[d.normalize()]=prod_jj.get(d.normalize(),0)+cad; plt+=cad
                        prod_tot+=plt
                        st.info(f"Total **{la}** : {plt:,.0f} T")
                return prod_tot

            st.markdown('<div class="section-title">Lignes ACS</div>',unsafe_allow_html=True)
            lignes_acs=["01A","01B","01C","01X","01Y","01Z","101D","101E","101U","JFC1","JFC2","JFC3","JFC4","JFC5","IMACID","PMP"]
            prod_acs_tot=render_lignes(lignes_acs,f"{pj}_acs",2600)

            st.markdown('<div class="section-title blue">Lignes ACP29</div>',unsafe_allow_html=True)
            lignes_acp29=["JFC1_ACP29","JFC2_ACP29","JFC3_ACP29","JFC4_ACP29","JFC5_ACP29","JLN_03AB","JLN_03CD","JLN_03XY","JLN_03ZU","JLN_03E","JLN_03F","PMP_ACP29","IMACID_ACP29"]
            prod_acp29_tot=render_lignes(lignes_acp29,f"{pj}_acp",1000)

            st.markdown('<div class="section-title orange">Résultats</div>',unsafe_allow_html=True)
            c29=3.14*prod_acp29_tot
            sf=si_acs+dech+rade_v+prod_acs_tot-c29-ce_acs
            r1,r2,r3,r4=st.columns(4)
            r1.metric("Production ACS",f"{prod_acs_tot:,.0f} T")
            r2.metric("Production ACP29",f"{prod_acp29_tot:,.0f} T")
            r3.metric("Conso ACP29 (×3.14)",f"{c29:,.0f} T")
            r4.metric("Stock final estimé",f"{sf:,.0f} T",delta="positif ✅" if sf>0 else "déficit ❌")

            nb_j=len(cal_acs)
            pj__=prod_acs_tot/nb_j if nb_j>0 else 0
            cj__=(c29+ce_acs)/nb_j if nb_j>0 else 0
            stk=si_acs; svacs=[]
            for i_d,d in enumerate(cal_acs):
                if i_d==0: stk+=rade_v+dech
                stk+=pj__; stk-=cj__; svacs.append(stk)
            fig=go.Figure()
            fig.add_trace(go.Scatter(x=cal_acs,y=svacs,mode='lines',name='Stock ACS',
                line=dict(color='#00843D',width=2.5),fill='tozeroy',fillcolor='rgba(0,132,61,0.07)'))
            fig.add_trace(go.Scatter(x=cal_acs,y=[0]*len(cal_acs),mode='lines',name='Zéro stock',
                line=dict(dash='dash',color='#C62828',width=1.5)))
            lyt=dict(**PLOT_LAYOUT); lyt['height']=380
            lyt['title']=dict(text="Évolution du stock ACS (simulation linéaire)",font=dict(size=14,color='#1A2332'))
            fig.update_layout(**lyt)
            st.plotly_chart(fig,use_container_width=True)

        else:
            SEUILS={"Soufre":36000,"NH3":5000,"KCL":10000}
            seuil=SEUILS.get(mat_j,36000)
            c1,c2=st.columns(2)
            with c1: si_j=st.number_input("Stock initial (T)",key=f"{pj}_si",min_value=0,value=100000,step=1000)
            with c2: cj_j=st.number_input("Consommation journalière (T)",key=f"{pj}_cj",min_value=0,value=17500,step=100)
            ucr_j=st.checkbox("Consommations journalières réelles ?",key=f"{pj}_ucr")
            cr_j={}
            if ucr_j:
                st.markdown('<div class="section-title">Consommation réelle par jour</div>',unsafe_allow_html=True)
                dm=pd.Timestamp.today().replace(day=1)
                jours=pd.date_range(dm,dm+pd.offsets.MonthEnd(1),freq='D')
                cols4=st.columns(4)
                for i,j in enumerate(jours):
                    with cols4[i%4]:
                        cr_j[j.date()]=st.number_input(j.strftime('%d/%m'),min_value=0,value=int(cj_j),step=100,key=f"{pj}_cr_{j.strftime('%Y%m%d')}")
            st.markdown('<div class="section-title blue">Navires prévus</div>',unsafe_allow_html=True)
            nav_j,ret_j=[],{}
            nn_j=st.number_input(f"Nombre de navires ({mat_j})",key=f"{pj}_n",min_value=0,value=3)
            for i in range(int(nn_j)):
                cd,cq,cr=st.columns(3)
                with cd: da=st.date_input(f"Date navire {i+1}",pd.Timestamp.today(),key=f"{pj}_d{i}")
                with cq: qty=st.number_input(f"Quantité {i+1} (T)",0,500000,30000,1000,key=f"{pj}_q{i}")
                with cr: ret=st.number_input(f"Retard (j) {i+1}",0,30,0,1,key=f"{pj}_r{i}")
                nav_j.append((pd.Timestamp(da),qty))
                if ret>0: ret_j[pd.Timestamp(da)]=ret
            if st.button(f"🚀 Lancer la simulation — Jorf / {mat_j}",key=f"{pj}_btn",type="primary"):
                d,sv,na,nq=simulation_stock(si_j,cj_j,nav_j,ret_j,cr_j if ucr_j else None)
                afficher_sim(d,sv,na,nq,f"Évolution du stock — Jorf / {mat_j}",seuil=seuil)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: PIPELINE DES VENTES (placeholder)
# ══════════════════════════════════════════════════════════════════════════════
elif page == "ventes":
    st.markdown("""
    <div class="placeholder-card">
      <div class="emoji">📊</div>
      <h2>Pipeline des Ventes</h2>
      <p>Ce module est en cours de développement.<br/>
      Il permettra de suivre les opportunités commerciales, les performances par produit et par marché.</p>
      <div class="badge-soon-green">PROCHAINEMENT</div>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: EXPORT NAVIRE (placeholder)
# ══════════════════════════════════════════════════════════════════════════════
elif page == "navires":
    st.markdown("""
    <div class="placeholder-card">
      <div class="emoji">🚢</div>
      <h2>Export Navire</h2>
      <p>Ce module est en cours de développement.<br/>
      Il permettra de planifier et suivre les chargements navires, les escales, et les volumes exportés.</p>
      <div class="badge-soon-blue">PROCHAINEMENT</div>
    </div>
    """, unsafe_allow_html=True)
