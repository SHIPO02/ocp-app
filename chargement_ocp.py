import streamlit as st
import pandas as pd
import re
import os
import io
import pickle
import json
from datetime import datetime
import plotly.graph_objects as go

st.set_page_config(page_title="OCP - Manufacturing Dashboard", layout="wide")

st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Barlow:wght@400;600;700&family=Barlow+Condensed:wght@600;700&display=swap');
        :root { --ocp-green: #00843D; --ocp-dark: #005C2A; --jorf-color: #00843D; --safi-color: #1A6FA8; --total-color: #C05A00; --rade-color: #6B3FA0; }
        html, body, [class*="css"] { font-family: 'Barlow', sans-serif; }
        .stApp { background-color: #F4F7F5; }
        h1, h2, h3 { color: var(--ocp-dark) !important; font-family: 'Barlow Condensed', sans-serif !important; }
        .kpi-card { border-radius: 12px; padding: 16px 18px; color: white; box-shadow: 0 4px 16px rgba(0,0,0,0.12); position: relative; overflow: hidden; min-height: 160px; height: 160px; display: flex; flex-direction: column; justify-content: space-between; box-sizing: border-box; }
        .kpi-card::before { content: ''; position: absolute; top: -20px; right: -20px; width: 80px; height: 80px; border-radius: 50%; background: rgba(255,255,255,0.1); }
        .kpi-card.jorf  { background: linear-gradient(135deg, #00843D, #005C2A); }
        .kpi-card.safi  { background: linear-gradient(135deg, #1A6FA8, #0D4A73); }
        .kpi-card.total { background: linear-gradient(135deg, #C05A00, #8A3F00); }
        .kpi-card.rade  { background: linear-gradient(135deg, #6B3FA0, #4A2A73); }
        .kpi-label { font-size: 11px; font-weight: 700; opacity: 0.9; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 4px; }
        .kpi-value { font-family: 'Barlow Condensed', sans-serif; font-size: 32px; font-weight: 700; line-height: 1.1; margin: 4px 0; word-break: break-word; }
        .kpi-sub   { font-size: 10px; opacity: 0.75; margin-top: 2px; line-height: 1.3; }
        .kpi-date  { font-size: 10px; opacity: 0.9; margin-top: 4px; font-weight: 600; letter-spacing: 0.3px; }
        .section-header { display: flex; align-items: center; gap: 10px; padding: 10px 16px; border-radius: 8px; margin: 20px 0 10px 0; font-family: 'Barlow Condensed', sans-serif; font-size: 20px; font-weight: 700; color: white; }
        .section-header.jorf  { background: var(--jorf-color); }
        .section-header.safi  { background: var(--safi-color); }
        .section-header.total { background: var(--total-color); }
        .section-header.rade  { background: var(--rade-color); }
        .section-header.sim   { background: #2C7BB6; }
        [data-testid="stSidebar"] { border-right: 3px solid var(--ocp-green); background: #FAFFF9; }
        hr { border-color: #D0E8D9 !important; }
        div[data-testid="stTabs"] button { font-family: 'Barlow Condensed', sans-serif !important; font-size: 17px !important; font-weight: 700 !important; }
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

NOMS_MOIS  = {1:"Jan",2:"Fev",3:"Mar",4:"Avr",5:"Mai",6:"Jun",7:"Jul",8:"Aou",9:"Sep",10:"Oct",11:"Nov",12:"Dec"}
ORDRE_MOIS = {v:k for k,v in NOMS_MOIS.items()}

def force_nombre(valeur):
    if pd.isna(valeur): return 0.0
    if isinstance(valeur, (int, float)): return 0.0 if abs(valeur) < 1e-6 else float(valeur)
    s = str(valeur).strip()
    if s in ("-", "", "nan"): return 0.0
    nettoye = re.sub(r'[^\d]', '', s.replace("\xa0","").replace(" ",""))
    if len(nettoye) > 12: return 0.0
    try: return float(nettoye)
    except: return 0.0

def en_milliers(v): return round(v / 1000, 1)
def fmt_number(n):  return f"{n:,.1f}".replace(",", " ")

def date_sort_key(d):
    try:
        parts = str(d).split("/")
        return (int(parts[2]), int(parts[1]), int(parts[0]))
    except: return (9999,99,99)

def mois_sort_key(m):
    try:
        parts = m.split()
        return (int(parts[1]), ORDRE_MOIS.get(parts[0], 99))
    except: return (9999,99)

def extract_mois_label(date_str):
    try:
        parts = str(date_str).split("/")
        if len(parts) == 3: return f"{NOMS_MOIS.get(int(parts[1]),'?')} {parts[2]}"
    except: pass
    return "Inconnu"

SKIP_KEYWORDS = ["total","recap","recapitulatif","annee","annuel","bilan","synthese","summary"]
def is_data_sheet(name): return not any(kw in name.strip().lower() for kw in SKIP_KEYWORDS)

def detect_engine(raw_bytes):
    for eng in ['openpyxl','pyxlsb','calamine']:
        try: pd.ExcelFile(io.BytesIO(raw_bytes), engine=eng); return eng
        except: continue
    raise ValueError("Aucun engine ne peut lire ce fichier.")

def read_file_bytes(file):
    file.seek(0); raw = file.read()
    fn = getattr(file,'name','').lower().strip()
    if fn.endswith('.xlsb'): return raw,'pyxlsb'
    if fn.endswith(('.xlsm','.xlsx')):
        try: pd.ExcelFile(io.BytesIO(raw), engine='openpyxl'); return raw,'openpyxl'
        except: pass
    if fn.endswith('.xls'):
        try: pd.ExcelFile(io.BytesIO(raw), engine='calamine'); return raw,'calamine'
        except: pass
    return raw, detect_engine(raw)

def get_derniere_valeur(df, col_valeur, col_date="Date"):
    if df is None or df.empty: return 0.0, None
    tmp = df[df[col_valeur] > 0].copy()
    if tmp.empty: return 0.0, None
    tmp["_sort"] = tmp[col_date].apply(date_sort_key)
    last = tmp.sort_values("_sort").iloc[-1]
    return round(float(last[col_valeur]), 1), last[col_date]

def appliquer_filtre(df, sel, col="Date"):
    if not sel: return df
    return df[df[col].isin(sel)]

def copier_ligne_btn(df, total_col, label, key):
    vals = df[df["Date"] != "TOTAL GENERAL"][total_col].dropna().tolist()
    ligne_txt = "\t".join(str(round(v,1)) for v in vals)
    btn_id = f"btn_{key}"
    st.components.v1.html(f"""
        <style>#{btn_id}{{background:#00843D;color:white;border:none;padding:7px 18px;border-radius:7px;cursor:pointer;font-family:Barlow,sans-serif;font-size:14px;font-weight:600}}#{btn_id}.copied{{background:#1A6FA8}}</style>
        <button id="{btn_id}" onclick="navigator.clipboard.writeText('{ligne_txt}').then(()=>{{this.innerHTML='Copie effectuee';this.classList.add('copied');setTimeout(()=>{{this.innerHTML='Copier {label} en ligne';this.classList.remove('copied')}},2000)}})">Copier {label} en ligne</button>
    """, height=45)

# ══════════════════════════════════════════════════════════════════════════════
# PARSERS
# ══════════════════════════════════════════════════════════════════════════════
def parse_jorf(raw_bytes, engine):
    df_raw = pd.read_excel(io.BytesIO(raw_bytes), sheet_name='EXPORT', header=None, engine=engine)
    coords = {"ENGRAIS": None, "CAMIONS": None, "VL": None}
    for r in range(len(df_raw)):
        lbl = " ".join(df_raw.iloc[r, 0:3].astype(str)).upper()
        if "EXPORT ENGRAIS" in lbl: coords["ENGRAIS"] = r
        if "EXPORT CAMIONS" in lbl: coords["CAMIONS"] = r
        if "VL CAMIONS"     in lbl: coords["VL"] = r
    ligne_dates = df_raw.iloc[2, :]
    cols_data = [j for j in range(3, len(ligne_dates)) if pd.notna(ligne_dates[j])]
    rows = []
    for j in cols_data:
        dt = ligne_dates[j]
        dl = dt.strftime('%d/%m/%Y') if hasattr(dt,'strftime') else str(dt).split(" ")[0]
        v1 = en_milliers(force_nombre(df_raw.iloc[coords["ENGRAIS"], j])) if coords["ENGRAIS"] is not None else 0.0
        v2 = en_milliers(force_nombre(df_raw.iloc[coords["CAMIONS"], j])) if coords["CAMIONS"] is not None else 0.0
        v3 = en_milliers(force_nombre(df_raw.iloc[coords["VL"],      j])) if coords["VL"]      is not None else 0.0
        rows.append({"Date":dl,"Export Engrais":v1,"Export Camions":v2,"VL Camions":v3,"TOTAL Jorf":round(v1+v2+v3,1)})
    return pd.DataFrame(rows)

def parse_rade(raw_bytes, engine):
    df_rade = pd.read_excel(io.BytesIO(raw_bytes), sheet_name='Sit Navire', header=None, engine=engine)
    rows = []
    for r in range(len(df_rade)):
        date_val = df_rade.iloc[r, 1]; val = df_rade.iloc[r, 3]
        if pd.isna(date_val) or pd.isna(val): continue
        s_date = str(date_val).strip()
        if s_date in ("","nan","Date"): continue
        date_label = date_val.strftime('%d/%m/%Y') if hasattr(date_val,'strftime') else s_date
        rows.append({"Date": date_label, "Engrais en attente": en_milliers(force_nombre(val))})
    return pd.DataFrame(rows) if rows else None

def parse_safi(raw_bytes, engine):
    xl = pd.ExcelFile(io.BytesIO(raw_bytes), engine=engine)
    COL_JOUR=1; COL_TSP_EXP=31; COL_TSP_ML=32; START_ROW=6
    def normaliser(s):
        acc={"é":"e","è":"e","ê":"e","ë":"e","à":"a","â":"a","ù":"u","û":"u","ô":"o","î":"i","ï":"i","ç":"c","ü":"u","ö":"o"}
        s=s.lower()
        for a,b in acc.items(): s=s.replace(a,b)
        return s
    def parse_mois_annee(sheet_name):
        mm={"jan":1,"fev":2,"mar":3,"avr":4,"mai":5,"jun":6,"jui":6,"jul":7,"aou":8,"sep":9,"oct":10,"nov":11,"dec":12}
        ml={"janvier":1,"fevrier":2,"mars":3,"avril":4,"mai":5,"juin":6,"juillet":7,"aout":8,"septembre":9,"octobre":10,"novembre":11,"decembre":12}
        parts=sheet_name.strip().split(); mn=None; an=None
        for p in parts:
            pn=normaliser(p)
            if pn[:3] in mm: mn=mm[pn[:3]]
            if pn in ml: mn=ml[pn]
            try:
                y=int(p)
                if 2000<=y<=2100: an=y
            except: pass
        return mn, an
    rows=[]
    for sheet in xl.sheet_names:
        if not is_data_sheet(sheet): continue
        mn,an=parse_mois_annee(sheet)
        if mn is None or an is None: continue
        dfs=pd.read_excel(io.BytesIO(raw_bytes), sheet_name=sheet, header=None, engine=engine)
        tec=COL_TSP_EXP; tml=COL_TSP_ML
        if dfs.shape[1]<=COL_TSP_ML:
            fe=False
            for hrow in range(min(8,len(dfs))):
                rv=[str(v).strip().upper() for v in dfs.iloc[hrow]]
                for ci,v in enumerate(rv):
                    if "TSP" in v and "EXPORT" in v: tec=ci; fe=True
                    if "TSP" in v and "ML" in v: tml=ci
            if not fe: continue
        for ri in range(START_ROW,len(dfs)):
            jv=dfs.iloc[ri,COL_JOUR]
            if pd.isna(jv): continue
            s=str(jv).strip()
            if s in ("","nan") or any(k in s.upper() for k in ["TOTAL","CUMUL","MOYENNE","MOY"]): continue
            try: jn=int(float(s))
            except: continue
            if jn<1 or jn>31: continue
            te=en_milliers(force_nombre(dfs.iloc[ri,tec])) if tec<dfs.shape[1] else 0.0
            tm=en_milliers(force_nombre(dfs.iloc[ri,tml])) if tml<dfs.shape[1] else 0.0
            rows.append({"Mois":sheet,"Jour":jn,"Date":f"{jn:02d}/{mn:02d}/{an}","TSP Export":te,"TSP ML":tm,"TOTAL Safi":round(te+tm,1)})
    return pd.DataFrame(rows) if rows else None

def charger_jorf_depuis_bytes(raw_bytes, filename):
    ff=io.BytesIO(raw_bytes); ff.name=filename
    raw,engine=read_file_bytes(ff)
    jd=parse_jorf(raw,engine); rd=None
    try: rd=parse_rade(raw,engine)
    except: pass
    st.session_state["jorf_df"]=jd; st.session_state["rade_df"]=rd; st.session_state["jorf_name"]=filename
    save_cache(JORF_CACHE,{"jorf_df":jd,"rade_df":rd,"filename":filename})
    return jd

def charger_safi_depuis_bytes(raw_bytes, filename):
    ff=io.BytesIO(raw_bytes); ff.name=filename
    raw,engine=read_file_bytes(ff)
    sd=parse_safi(raw,engine)
    st.session_state["safi_df"]=sd; st.session_state["safi_name"]=filename
    save_cache(SAFI_CACHE,{"safi_df":sd,"filename":filename})
    return sd

# ══════════════════════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════════════════════
col_logo, col_title = st.columns([1, 5])
with col_logo:
    if os.path.exists("logo_ocp.png"):
        st.image("logo_ocp.png", width=110)
    else:
        st.markdown("<div style='font-size:34px;font-weight:900;color:#00843D;font-family:Barlow Condensed,sans-serif;'>OCP</div>", unsafe_allow_html=True)
with col_title:
    st.title("Manufacturing Dashboard")
    st.markdown("##### Jorf Lasfar & Safi — Suivi Chargement & Simulation Stock")

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
st.sidebar.header("📂 Chargement des fichiers")
EXCEL_TYPES = ["xlsx","xls","xlsm","xlsb"]

if "jorf_loaded" not in st.session_state:
    cached=load_cache(JORF_CACHE)
    if cached:
        st.session_state["jorf_df"]=cached.get("jorf_df")
        st.session_state["rade_df"]=cached.get("rade_df")
        st.session_state["jorf_name"]=cached.get("filename","")
    st.session_state["jorf_loaded"]=True

if "safi_loaded" not in st.session_state:
    cached=load_cache(SAFI_CACHE)
    if cached:
        st.session_state["safi_df"]=cached.get("safi_df")
        st.session_state["safi_name"]=cached.get("filename","")
    st.session_state["safi_loaded"]=True

file_jorf = st.sidebar.file_uploader("📂 Fichier Jorf", type=EXCEL_TYPES, key="jorf_uploader")
file_safi = st.sidebar.file_uploader("📂 Fichier Safi", type=EXCEL_TYPES, key="safi_uploader")

if not file_jorf and st.session_state.get("jorf_name"):
    st.sidebar.success(f"✅ Jorf : **{st.session_state['jorf_name']}**")
if not file_safi and st.session_state.get("safi_name"):
    st.sidebar.success(f"✅ Safi : **{st.session_state['safi_name']}**")

if file_jorf:
    try:
        jb,eng=read_file_bytes(file_jorf)
        jd=parse_jorf(jb,eng); rd=None
        try: rd=parse_rade(jb,eng)
        except: pass
        clear_cache(JORF_CACHE)
        st.session_state["jorf_df"]=jd; st.session_state["rade_df"]=rd; st.session_state["jorf_name"]=file_jorf.name
        save_cache(JORF_CACHE,{"jorf_df":jd,"rade_df":rd,"filename":file_jorf.name})
        file_jorf.seek(0); add_to_historique(HIST_JORF,file_jorf.name,file_jorf.read(),"jorf")
        st.sidebar.success("✅ Jorf chargé !")
    except Exception as e: st.sidebar.error(f"Erreur Jorf : {e}")

if file_safi:
    try:
        sb,eng=read_file_bytes(file_safi)
        sd=parse_safi(sb,eng)
        clear_cache(SAFI_CACHE)
        st.session_state["safi_df"]=sd; st.session_state["safi_name"]=file_safi.name
        save_cache(SAFI_CACHE,{"safi_df":sd,"filename":file_safi.name})
        file_safi.seek(0); add_to_historique(HIST_SAFI,file_safi.name,file_safi.read(),"safi")
        if sd is not None:
            st.sidebar.success("✅ Safi chargé !")
        else:
            st.sidebar.warning("Aucune feuille mensuelle détectée.")
    except Exception as e: st.sidebar.error(f"Erreur Safi : {e}")

# Historique
st.sidebar.divider()
st.sidebar.markdown("### 🕓 Historique")
hist_jorf = load_historique(HIST_JORF)
hist_safi = load_historique(HIST_SAFI)

if hist_jorf:
    with st.sidebar.expander(f"📋 Jorf ({len(hist_jorf)})", expanded=False):
        for i, entry in enumerate(hist_jorf):
            is_active = entry["filename"] == st.session_state.get("jorf_name","")
            c1,c2 = st.columns([3,1])
            with c1: st.markdown(f"{'🟢 ' if is_active else '⬜ '}{entry['filename']}  \n`{entry['date_upload']}`")
            with c2:
                if not is_active:
                    if st.button("↩️", key=f"rj_{i}"):
                        raw=load_from_hist_entry(entry)
                        if raw:
                            try: charger_jorf_depuis_bytes(raw,entry["filename"]); st.rerun()
                            except Exception as e: st.error(str(e))
                        else: st.error("Fichier introuvable.")
                else: st.markdown("✅")
else: st.sidebar.caption("Aucun fichier Jorf.")

if hist_safi:
    with st.sidebar.expander(f"📋 Safi ({len(hist_safi)})", expanded=False):
        for i, entry in enumerate(hist_safi):
            is_active = entry["filename"] == st.session_state.get("safi_name","")
            c1,c2 = st.columns([3,1])
            with c1: st.markdown(f"{'🟢 ' if is_active else '⬜ '}{entry['filename']}  \n`{entry['date_upload']}`")
            with c2:
                if not is_active:
                    if st.button("↩️", key=f"rs_{i}"):
                        raw=load_from_hist_entry(entry)
                        if raw:
                            try: charger_safi_depuis_bytes(raw,entry["filename"]); st.rerun()
                            except Exception as e: st.error(str(e))
                        else: st.error("Fichier introuvable.")
                else: st.markdown("✅")
else: st.sidebar.caption("Aucun fichier Safi.")

# Filtres (sidebar - pour onglet Suivi)
jorf_df = st.session_state.get("jorf_df", None)
rade_df = st.session_state.get("rade_df", None)
safi_df = st.session_state.get("safi_df", None)

st.sidebar.divider()
st.sidebar.header("🔎 Filtrage (Suivi)")

def filtre_dates_sidebar(df, label_prefix, key_prefix):
    mois_map = {}; annees = set()
    for d in df["Date"].unique():
        try:
            parts=str(d).split("/"); annees.add(int(parts[2]))
            m_label=f"{NOMS_MOIS.get(int(parts[1]),'?')} {parts[2]}"
        except: m_label="Autre"
        mois_map.setdefault(m_label,[]).append(d)
    for an in annees:
        for num,nom in NOMS_MOIS.items():
            ml=f"{nom} {an}"
            if ml not in mois_map: mois_map[ml]=[]
    mois_tries=sorted(mois_map.keys(), key=mois_sort_key)
    options=[m if mois_map[m] else f"{m} —" for m in mois_tries]
    mode=st.sidebar.radio(f"{label_prefix}",["Tout","Mois","Dates"],horizontal=True,key=f"{key_prefix}_mode")
    if mode=="Tout": return [],"Toute la periode"
    elif mode=="Mois":
        choix=st.sidebar.multiselect(f"Mois {label_prefix}",options=options,default=[],key=f"{key_prefix}_mois")
        if not choix: return [],"Toute la periode"
        dates_sel=[]; labels=[]
        for m in choix:
            cle=m.rstrip(" —"); dates_sel+=mois_map.get(cle,[]); labels.append(cle)
        return dates_sel,", ".join(labels)
    else:
        all_d=sorted(df["Date"].unique().tolist(),key=lambda d:tuple(int(x) for x in str(d).split("/"))[::-1])
        choix=st.sidebar.multiselect(f"Dates {label_prefix}",all_d,key=f"{key_prefix}_dates")
        if not choix: return [],"Toute la periode"
        return choix,f"{len(choix)} date(s)"

if jorf_df is not None:
    st.sidebar.markdown("**Jorf Lasfar**")
    sel_jorf, label_jorf = filtre_dates_sidebar(jorf_df,"Jorf","jorf")
else: sel_jorf,label_jorf=[],  "Toute la periode"

if safi_df is not None:
    st.sidebar.markdown("**Safi**")
    sel_safi, label_safi = filtre_dates_sidebar(safi_df,"Safi","safi")
else: sel_safi,label_safi=[],"Toute la periode"

# ══════════════════════════════════════════════════════════════════════════════
# ONGLETS PRINCIPAUX
# ══════════════════════════════════════════════════════════════════════════════
tab_suivi, tab_sim = st.tabs(["🏭  Suivi Chargement", "📦  Simulation de Stock"])


# ══════════════════════════════════════════════════════════════════════════════
# ONGLET 1 — SUIVI CHARGEMENT
# ══════════════════════════════════════════════════════════════════════════════
with tab_suivi:
    jorf_kpi = appliquer_filtre(jorf_df, sel_jorf) if jorf_df is not None else None
    safi_kpi = appliquer_filtre(safi_df, sel_safi) if safi_df is not None else None
    rade_kpi = appliquer_filtre(rade_df, sel_jorf) if rade_df is not None else None

    cumul_jorf  = round(float(jorf_kpi["TOTAL Jorf"].sum()),1) if jorf_kpi is not None else 0.0
    cumul_safi  = round(float(safi_kpi["TOTAL Safi"].sum()),1) if safi_kpi is not None else 0.0
    cumul_total = round(cumul_jorf + cumul_safi, 1)
    rade_j_val, rade_j_date = get_derniere_valeur(rade_kpi,"Engrais en attente") if rade_kpi is not None else (0.0,None)

    periode_label = f"Filtre : {label_jorf} / {label_safi}" if (sel_jorf or sel_safi) else "Toute la Periode"
    st.markdown(f"### Cumul à Date — {periode_label}")

    k1,k2,k3,k4 = st.columns(4)
    with k1:
        sub1="Export Engrais + Camions + VL" if jorf_df is not None else "Fichier non chargé"
        st.markdown(f'<div class="kpi-card jorf"><div class="kpi-label">Total Jorf</div><div class="kpi-value">{fmt_number(cumul_jorf)}</div><div class="kpi-sub">{sub1}</div></div>', unsafe_allow_html=True)
    with k2:
        if rade_df is not None and rade_j_date:
            st.markdown(f'<div class="kpi-card rade"><div class="kpi-label">Rade Jorf</div><div class="kpi-value">{fmt_number(rade_j_val)}</div><div class="kpi-sub">Engrais en attente</div><div class="kpi-date">📅 {rade_j_date}</div></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="kpi-card rade"><div class="kpi-label">Rade Jorf</div><div class="kpi-value">—</div><div class="kpi-sub">Fichier non chargé</div></div>', unsafe_allow_html=True)
    with k3:
        sub2="TSP Export + TSP ML" if safi_df is not None else "Fichier non chargé"
        st.markdown(f'<div class="kpi-card safi"><div class="kpi-label">Total Safi</div><div class="kpi-value">{fmt_number(cumul_safi)}</div><div class="kpi-sub">{sub2}</div></div>', unsafe_allow_html=True)
    with k4:
        st.markdown(f'<div class="kpi-card total"><div class="kpi-label">Total Jorf + Safi</div><div class="kpi-value">{fmt_number(cumul_total)}</div><div class="kpi-sub">Consolidé toutes unités</div></div>', unsafe_allow_html=True)

    st.divider()
    st.markdown('<div class="section-header total">Tableau Consolidé — Toutes Données par Jour (KT)</div>', unsafe_allow_html=True)
    st.markdown("""<style>.grp-header{display:flex;width:100%;margin-bottom:4px;font-family:'Barlow Condensed',sans-serif;font-weight:700;font-size:13px}.grp-jorf{background:#00843D;color:white;padding:4px 10px;border-radius:4px;margin-right:4px;flex:4;text-align:center}.grp-safi{background:#1A6FA8;color:white;padding:4px 10px;border-radius:4px;margin-right:4px;flex:3;text-align:center}.grp-rade{background:#6B3FA0;color:white;padding:4px 10px;border-radius:4px;margin-right:4px;flex:1;text-align:center}.grp-total{background:#C05A00;color:white;padding:4px 10px;border-radius:4px;flex:1;text-align:center}</style>
    <div class="grp-header"><div style="min-width:90px;flex:0"></div><div class="grp-jorf">JORF LASFAR</div><div class="grp-safi">SAFI</div><div class="grp-rade">RADE JORF</div><div class="grp-total">TOTAL</div></div>""", unsafe_allow_html=True)

    any_data = jorf_df is not None or safi_df is not None or rade_df is not None
    if any_data:
        jorf_f = appliquer_filtre(jorf_df,sel_jorf) if jorf_df is not None else None
        rade_f = appliquer_filtre(rade_df,sel_jorf) if rade_df is not None else None
        safi_f = appliquer_filtre(safi_df,sel_safi) if safi_df is not None else None

        all_dates=set()
        if jorf_f is not None: all_dates|=set(jorf_f["Date"].unique())
        if rade_f is not None: all_dates|=set(rade_f["Date"].unique())
        if safi_f is not None: all_dates|=set(safi_f["Date"].unique())
        all_dates=sorted(all_dates, key=date_sort_key)

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
        if jorf_f is not None: col_order+=["J_Engrais","J_Camions","J_VL"]
        if safi_f is not None: col_order+=["S_Engrais","S_VL"]
        if jorf_f is not None: col_order+=["J_TOTAL"]
        if safi_f is not None: col_order+=["S_TOTAL"]
        col_order+=["TOTAL"]
        if rade_f is not None: col_order+=["RADE_J"]
        col_order=[c for c in col_order if c in unified_df.columns]
        unified_df=unified_df[col_order]

        total_row={"Date":"TOTAL GENERAL"}
        for col in unified_df.columns:
            if col=="Date": continue
            elif col=="RADE_J": total_row[col]=None
            else: total_row[col]=round(unified_df[col].sum(),1)
        disp_unified=pd.concat([unified_df,pd.DataFrame([total_row])],ignore_index=True)

        col_cfg={"Date":st.column_config.TextColumn("Date")}
        if jorf_f is not None:
            col_cfg["J_Engrais"]=st.column_config.NumberColumn("Export Engrais",format="%.1f")
            col_cfg["J_Camions"]=st.column_config.NumberColumn("Export Camions",format="%.1f")
            col_cfg["J_VL"]     =st.column_config.NumberColumn("VL Camions",    format="%.1f")
        if safi_f is not None:
            col_cfg["S_Engrais"]=st.column_config.NumberColumn("Export Engrais",format="%.1f")
            col_cfg["S_VL"]     =st.column_config.NumberColumn("VL Camions",    format="%.1f")
        if jorf_f is not None: col_cfg["J_TOTAL"]=st.column_config.NumberColumn("Total Jorf",    format="%.1f")
        if safi_f is not None: col_cfg["S_TOTAL"]=st.column_config.NumberColumn("Total Safi",    format="%.1f")
        col_cfg["TOTAL"]=st.column_config.NumberColumn("Total Jorf+Safi",format="%.1f")
        if rade_f is not None: col_cfg["RADE_J"]=st.column_config.NumberColumn("Rade Jorf",format="%.1f")

        st.dataframe(disp_unified, use_container_width=True, hide_index=True,
                     height=min(700, 45+35*len(disp_unified)), column_config=col_cfg)

        cc1,cc2,cc3=st.columns(3)
        with cc1:
            if jorf_f is not None: copier_ligne_btn(unified_df,"J_TOTAL","Total Jorf","copy_jorf")
        with cc2:
            if safi_f is not None: copier_ligne_btn(unified_df,"S_TOTAL","Total Safi","copy_safi")
        with cc3:
            copier_ligne_btn(unified_df,"TOTAL","Total Jorf+Safi","copy_total")

        st.divider()
        g_left,g_right=st.columns(2)

        with g_left:
            st.markdown('<div class="section-header rade">Rade Jorf — Engrais en Attente</div>', unsafe_allow_html=True)
            if rade_f is not None and "RADE_J" in unified_df.columns and len(unified_df)>1:
                rc=unified_df[unified_df["RADE_J"]>0].copy()
                if len(rc)>0: st.bar_chart(rc.set_index("Date")[["RADE_J"]].rename(columns={"RADE_J":"Rade Jorf"}),color="#6B3FA0")
                else: st.info("Pas de données Rade disponibles.")
            else: st.info("Chargez le fichier Jorf pour voir la Rade.")

        with g_right:
            cols_line=[c for c in ["J_TOTAL","S_TOTAL","TOTAL"] if c in unified_df.columns]
            if cols_line and len(unified_df)>1:
                line_df=unified_df.copy()
                line_df["Mois"]=line_df["Date"].apply(extract_mois_label)
                line_df=line_df[line_df["Mois"]!="Inconnu"]
                mois_line=line_df.groupby("Mois")[cols_line].sum().reset_index()
                mois_line["_sort"]=mois_line["Mois"].apply(mois_sort_key)
                mois_line=mois_line.sort_values("_sort").drop(columns=["_sort"]).reset_index(drop=True)
                mois_line=mois_line.rename(columns={"J_TOTAL":"Total Jorf","S_TOTAL":"Total Safi","TOTAL":"Total Jorf+Safi"}).set_index("Mois")

                st.markdown('<div class="section-header jorf" style="font-size:15px;padding:7px 14px;">Total Jorf vs Total Safi par Jour</div>', unsafe_allow_html=True)
                djs=[c for c in ["J_TOTAL","S_TOTAL"] if c in unified_df.columns]
                if djs and len(unified_df)>1:
                    dj=unified_df.set_index("Date")[djs].rename(columns={"J_TOTAL":"Total Jorf","S_TOTAL":"Total Safi"})
                    cj=["#00843D" if c=="Total Jorf" else "#1A6FA8" for c in dj.columns]
                    st.line_chart(dj, color=cj)

                st.markdown('<div class="section-header total" style="font-size:15px;padding:7px 14px;">Total Jorf+Safi par Mois</div>', unsafe_allow_html=True)
                if "Total Jorf+Safi" in mois_line.columns and len(mois_line)>0:
                    st.line_chart(mois_line[["Total Jorf+Safi"]],color="#C05A00")
            else: st.info("Chargez les fichiers pour voir les graphiques.")
    else:
        st.info("Chargez au moins un fichier pour voir le tableau consolidé.")


# ══════════════════════════════════════════════════════════════════════════════
# ONGLET 2 — SIMULATION DE STOCK
# ══════════════════════════════════════════════════════════════════════════════
with tab_sim:
    st.markdown('<div class="section-header sim">📦 Simulation du Stock — Matières Premières</div>', unsafe_allow_html=True)

    def simulation_stock(stock_initial, conso_j, navires, retards, conso_reelle=None):
        navires=sorted(navires, key=lambda x:x[0])
        today=pd.Timestamp.today()
        debut=pd.Timestamp(today.year, today.month, 1)
        cal=pd.date_range(start=debut, end=debut+pd.DateOffset(days=60), freq='D')
        stock=stock_initial; sv=[]; dates=[]; nav_arr=[]; nav_qty=[]
        for jour in cal:
            for (dp,qty) in navires:
                de=dp+pd.Timedelta(days=retards.get(dp,0))
                if jour==de: stock+=qty; nav_arr.append(jour); nav_qty.append(qty)
            conso=conso_reelle.get(jour.date(),conso_j) if conso_reelle else conso_j
            stock-=conso; sv.append(stock); dates.append(jour)
        return dates,sv,nav_arr,nav_qty

    def afficher_graphique_sim(dates, sv, nav_arr, nav_qty, titre, seuil=36000):
        fig=go.Figure()
        fig.add_hrect(y0=0,y1=seuil,fillcolor="rgba(255,0,0,0.05)",line_width=0)
        fig.add_trace(go.Scatter(x=dates,y=sv,mode='lines+markers',name='Stock',
            line=dict(color='#00843D',width=2),marker=dict(size=4),
            hovertemplate='<b>%{x|%d/%m/%Y}</b><br>Stock : %{y:,.0f} T<extra></extra>'))
        fig.add_trace(go.Scatter(x=dates,y=[seuil]*len(dates),mode='lines',
            name=f'Seuil critique ({seuil:,} T)',line=dict(dash='dash',color='red',width=1.5)))
        for i,date in enumerate(nav_arr):
            idx=dates.index(date)
            fig.add_trace(go.Scatter(x=[date],y=[sv[idx]],mode='markers+text',
                name=f'Navire {i+1}',marker=dict(symbol='triangle-up',color='#1A6FA8',size=12),
                text=[f"+{nav_qty[i]:,} T"],textposition='top center',
                textfont=dict(size=11,color='#1A6FA8'),showlegend=True))
        fig.update_layout(title=dict(text=titre,font=dict(size=18,family="Barlow Condensed")),
            xaxis_title='Date',yaxis_title='Stock (tonnes)',hovermode='x unified',
            plot_bgcolor='rgba(244,247,245,0.5)',paper_bgcolor='rgba(0,0,0,0)',
            legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1),height=450)
        st.plotly_chart(fig, use_container_width=True)
        # Métriques
        m1,m2,m3=st.columns(3)
        m1.metric("Stock minimum",f"{min(sv):,.0f} T",f"le {dates[sv.index(min(sv))].strftime('%d/%m/%Y')}")
        m2.metric("Stock final",f"{sv[-1]:,.0f} T")
        m3.metric(f"Jours sous seuil ({seuil:,} T)",f"{sum(1 for v in sv if v<seuil)} j")

    # Sous-onglets Safi / Jorf
    sim_safi, sim_jorf = st.tabs(["🌊 Site de Safi", "⚓ Site de Jorf"])

    # ── SAFI ─────────────────────────────────────────────────────────────────
    with sim_safi:
        matiere_safi=st.selectbox("Matière première (Safi)",["Soufre"],key="sim_safi_mat")
        ps=f"ss_{matiere_safi.lower()}"
        c1,c2=st.columns(2)
        with c1: si_safi=st.number_input("Stock initial (T)",key=f"{ps}_stock",min_value=0,value=40000,step=1000)
        with c2: cj_safi=st.number_input("Consommation journalière (T)",key=f"{ps}_cons",min_value=0,value=3600,step=100)

        ucr_safi=st.checkbox("Consommations journalières réelles ?",key=f"{ps}_ucr")
        cr_safi={}
        if ucr_safi:
            st.markdown("#### 📅 Consommation réelle par jour")
            dm=pd.Timestamp.today().replace(day=1)
            jours=pd.date_range(dm,dm+pd.offsets.MonthEnd(1),freq='D')
            cols=st.columns(4)
            for i,j in enumerate(jours):
                with cols[i%4]:
                    cr_safi[j.date()]=st.number_input(j.strftime('%d/%m'),min_value=0,value=int(cj_safi),step=100,key=f"{ps}_cr_{j.strftime('%Y%m%d')}")

        st.markdown("#### 🚢 Navires")
        nav_safi,ret_safi=[],{}
        n_nav=st.number_input("Nombre de navires",key=f"{ps}_n",min_value=0,value=3)
        for i in range(int(n_nav)):
            cd,cq,cr=st.columns(3)
            with cd: da=st.date_input(f"Date navire {i+1}",pd.Timestamp.today(),key=f"{ps}_d{i}")
            with cq: qty=st.number_input(f"Quantité {i+1} (T)",0,500000,30000,1000,key=f"{ps}_q{i}")
            with cr: ret=st.number_input(f"Retard (j) {i+1}",0,30,0,1,key=f"{ps}_r{i}")
            nav_safi.append((pd.Timestamp(da),qty))
            if ret>0: ret_safi[pd.Timestamp(da)]=ret

        if st.button(f"🚀 Lancer la simulation — Safi ({matiere_safi})",key=f"{ps}_btn",type="primary"):
            d,sv,na,nq=simulation_stock(si_safi,cj_safi,nav_safi,ret_safi,cr_safi if ucr_safi else None)
            afficher_graphique_sim(d,sv,na,nq,f"📈 Évolution du stock — Safi ({matiere_safi})")

    # ── JORF ─────────────────────────────────────────────────────────────────
    with sim_jorf:
        matiere=st.selectbox("Matière première",["Soufre","NH3","KCL","ACS"],key="sim_jorf_mat")
        pj=f"sj_{matiere.lower()}"

        # ── ACS ──────────────────────────────────────────────────────────────
        if matiere=="ACS":
            st.subheader("📊 Production ACS multi-périodes")
            c1,c2,c3,c4=st.columns(4)
            with c1: ce=st.number_input("Conso engrais (T)",key=f"{pj}_ce",min_value=0,value=12000)
            with c2: si_acs=st.number_input("Stock initial ACS (T)",key=f"{pj}_si",min_value=0,value=300000)
            with c3: rade_acs=st.number_input("Rade (T)",key=f"{pj}_rade",min_value=0,value=60000)
            with c4: dech=st.number_input("Déchargement (T)",key=f"{pj}_dech",min_value=0,value=300000)

            dm=pd.Timestamp.today().replace(day=1)
            cal_acs=pd.date_range(start=dm,end=dm+pd.DateOffset(days=60),freq='D')
            prod_j={d.normalize():0 for d in cal_acs}

            st.markdown("### 🚆 Lignes ACS")
            lignes_acs=["01A","01B","01C","01X","01Y","01Z","101D","101E","101U","JFC1","JFC2","JFC3","JFC4","JFC5","IMACID","PMP"]
            prod_acs_tot=0
            for i,ligne in enumerate(st.tabs([f"Ligne {l}" for l in lignes_acs])):
                with ligne:
                    la=lignes_acs[i]
                    jal=st.text_input(f"Jours d'arrêt (ex: 1-3,15) — {la}",key=f"{pj}_{la}_ar")
                    jar=[]
                    if jal:
                        for part in jal.split(","):
                            part=part.strip()
                            if "-" in part:
                                a_,b_=part.split("-"); jar.extend(range(int(a_),int(b_)+1))
                            else: jar.append(int(part))
                        jar=sorted(set(jar))
                    nb=st.number_input(f"Périodes ({la})",min_value=1,value=1,key=f"{pj}_{la}_nb")
                    plt=0
                    for p in range(int(nb)):
                        ca,cb,cc=st.columns(3)
                        with ca: dd=st.date_input(f"Début {p+1}",dm,key=f"{pj}_{la}_dd{p}")
                        with cb: df_=st.date_input(f"Fin {p+1}",dm+pd.Timedelta(days=5),key=f"{pj}_{la}_df{p}")
                        with cc: cad=st.number_input(f"Cadence T/j {p+1}",min_value=0,value=2600,key=f"{pj}_{la}_cad{p}")
                        for d in pd.date_range(pd.Timestamp(dd),pd.Timestamp(df_),freq='D'):
                            if d.day not in jar:
                                prod_j[d.normalize()]=prod_j.get(d.normalize(),0)+cad; plt+=cad
                    prod_acs_tot+=plt
                    st.info(f"Production totale {la} : **{plt:,.0f} T**")

            st.markdown("### 🚆 Lignes ACP29")
            lignes_acp29=["JFC1_ACP29","JFC2_ACP29","JFC3_ACP29","JFC4_ACP29","JFC5_ACP29","JLN_ACP29_03AB","JLN_ACP29_03CD","JLN_ACP29_03XY","JLN_ACP29_03ZU","JLN_ACP29_03E","JLN_ACP29_03F","PMP_ACP29","IMACID_ACP29"]
            prod_acp29_tot=0
            for i,ligne in enumerate(st.tabs([f"Ligne {l}" for l in lignes_acp29])):
                with ligne:
                    la=lignes_acp29[i]
                    jal=st.text_input(f"Jours d'arrêt (ex: 1-3,15) — {la}",key=f"{pj}_{la}_ar")
                    jar=[]
                    if jal:
                        for part in jal.split(","):
                            part=part.strip()
                            if "-" in part:
                                a_,b_=part.split("-"); jar.extend(range(int(a_),int(b_)+1))
                            else: jar.append(int(part))
                        jar=sorted(set(jar))
                    nb=st.number_input(f"Périodes ({la})",min_value=1,value=1,key=f"{pj}_{la}_nb")
                    plt=0
                    for p in range(int(nb)):
                        ca,cb,cc=st.columns(3)
                        with ca: dd=st.date_input(f"Début {p+1}",dm,key=f"{pj}_{la}_dd{p}")
                        with cb: df_=st.date_input(f"Fin {p+1}",dm+pd.Timedelta(days=5),key=f"{pj}_{la}_df{p}")
                        with cc: cad=st.number_input(f"Cadence T/j {p+1}",min_value=0,value=1000,key=f"{pj}_{la}_cad{p}")
                        for d in pd.date_range(pd.Timestamp(dd),pd.Timestamp(df_),freq='D'):
                            if d.day not in jar: plt+=cad
                    prod_acp29_tot+=plt
                    st.info(f"Production totale {la} : **{plt:,.0f} T**")

            st.divider()
            st.markdown("### 📈 Résultats")
            c29=3.14*prod_acp29_tot
            sf=si_acs+dech+rade_acs+prod_acs_tot-c29-ce
            r1,r2,r3,r4=st.columns(4)
            r1.metric("Production ACS",f"{prod_acs_tot:,.0f} T")
            r2.metric("Production ACP29",f"{prod_acp29_tot:,.0f} T")
            r3.metric("Conso ACP29 (×3.14)",f"{c29:,.0f} T")
            r4.metric("Stock final estimé",f"{sf:,.0f} T",delta="✅ positif" if sf>0 else "❌ déficit")

            nb_j=len(cal_acs)
            pj_=prod_acs_tot/nb_j if nb_j>0 else 0
            cj_=(c29+ce)/nb_j if nb_j>0 else 0
            stock=si_acs; svacs=[]
            for i_d,d in enumerate(cal_acs):
                if i_d==0: stock+=rade_acs+dech
                stock+=pj_; stock-=cj_; svacs.append(stock)
            fig=go.Figure()
            fig.add_trace(go.Scatter(x=cal_acs,y=svacs,mode='lines+markers',name='Stock ACS',line=dict(color='#00843D',width=2)))
            fig.add_trace(go.Scatter(x=cal_acs,y=[0]*len(cal_acs),mode='lines',name='Zéro stock',line=dict(dash='dash',color='red',width=1.5)))
            fig.update_layout(title="📈 Évolution du stock ACS",xaxis_title='Date',yaxis_title='Stock (T)',
                plot_bgcolor='rgba(244,247,245,0.5)',paper_bgcolor='rgba(0,0,0,0)',height=420)
            st.plotly_chart(fig, use_container_width=True)

        # ── Soufre / NH3 / KCL ───────────────────────────────────────────────
        else:
            SEUILS={"Soufre":36000,"NH3":5000,"KCL":10000}
            seuil=SEUILS.get(matiere,36000)
            c1,c2=st.columns(2)
            with c1: si_j=st.number_input("Stock initial (T)",key=f"{pj}_stock",min_value=0,value=100000,step=1000)
            with c2: cj_j=st.number_input("Consommation journalière (T)",key=f"{pj}_cons",min_value=0,value=17500,step=100)

            ucr_j=st.checkbox("Consommations journalières réelles ?",key=f"{pj}_ucr")
            cr_j={}
            if ucr_j:
                st.markdown("#### 📅 Consommation réelle par jour")
                dm=pd.Timestamp.today().replace(day=1)
                jours=pd.date_range(dm,dm+pd.offsets.MonthEnd(1),freq='D')
                cols=st.columns(4)
                for i,j in enumerate(jours):
                    with cols[i%4]:
                        cr_j[j.date()]=st.number_input(j.strftime('%d/%m'),min_value=0,value=int(cj_j),step=100,key=f"{pj}_cr_{j.strftime('%Y%m%d')}")

            st.markdown(f"#### 🚢 Navires ({matiere})")
            nav_j,ret_j=[],{}
            n_nav_j=st.number_input(f"Nombre de navires ({matiere})",key=f"{pj}_n",min_value=0,value=3)
            for i in range(int(n_nav_j)):
                cd,cq,cr=st.columns(3)
                with cd: da=st.date_input(f"Date navire {i+1}",pd.Timestamp.today(),key=f"{pj}_d{i}")
                with cq: qty=st.number_input(f"Quantité {i+1} (T)",0,500000,30000,1000,key=f"{pj}_q{i}")
                with cr: ret=st.number_input(f"Retard (j) {i+1}",0,30,0,1,key=f"{pj}_r{i}")
                nav_j.append((pd.Timestamp(da),qty))
                if ret>0: ret_j[pd.Timestamp(da)]=ret

            if st.button(f"🚀 Lancer la simulation — Jorf ({matiere})",key=f"{pj}_btn",type="primary"):
                d,sv,na,nq=simulation_stock(si_j,cj_j,nav_j,ret_j,cr_j if ucr_j else None)
                afficher_graphique_sim(d,sv,na,nq,f"📈 Évolution du stock — Jorf ({matiere})",seuil=seuil)
