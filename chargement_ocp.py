import streamlit as st
import pandas as pd
import re, os, io, pickle, json
from datetime import datetime
import plotly.graph_objects as go
import base64
import google.generativeai as genai

# ══════════════════════════════════════════════════════
# CONFIGURATION INITIALE & SÉCURITÉ IA
# ══════════════════════════════════════════════════════
st.set_page_config(page_title="OCP Manufacturing", layout="wide", initial_sidebar_state="expanded")

# Configuration sécurisée via Streamlit Secrets
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model_ai = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error("⚠️ Clé API non configurée. Ajoutez GEMINI_API_KEY dans les Secrets Streamlit.")

def get_smart_mapping(df_columns, target_columns, context="Données OCP"):
    """L'IA analyse sémantiquement les colonnes Excel."""
    prompt = f"""
    Expert logistique OCP, analyse ces colonnes Excel : {df_columns}
    Identifie les correspondances pour : {target_columns}
    Réponds UNIQUEMENT avec un JSON pur : {{"colonne_excel": "nom_cible"}}
    """
    try:
        response = model_ai.generate_content(prompt)
        clean_json = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(clean_json)
    except:
        return {}

# ══════════════════════════════════════════════════════
# CSS — THÈME PROFESSIONNEL OCP
# ══════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow:wght@300;400;500;600;700&family=Barlow+Condensed:wght@500;600;700;800&display=swap');
:root {
  --green: #00843D; --green-dk: #005C2A; --green-lt: #E8F5EE;
  --blue: #1565C0; --blue-lt: #E3EAF8;
  --orange: #C05A00; --orange-lt: #FBF0E6;
  --purple: #6B3FA0; --purple-lt: #F0EBF8;
  --bg: #F2F4F7; --white: #FFFFFF;
  --border: #E0E4EA; --text: #12202E; --text2: #4A5568;
  --sh1: 0 1px 3px rgba(0,0,0,0.07); --sh2: 0 4px 16px rgba(0,0,0,0.10);
}
html,body,[class*="css"] { font-family:'Barlow',sans-serif !important; color:var(--text); }
.stApp { background:var(--bg) !important; }
.topbar { background:var(--white); border-bottom:1px solid var(--border); padding:12px 1.8rem; margin:0 -1.8rem 20px -1.8rem; display:flex; align-items:center; justify-content:space-between; box-shadow:var(--sh1); }
.kcard { background:var(--white); border:1px solid var(--border); border-radius:10px; padding:18px 20px; box-shadow:var(--sh1); position:relative; overflow:hidden; display:flex; flex-direction:column; justify-content:space-between; height:100%; }
.kcard.green::after { content:''; position:absolute; top:0; left:0; right:0; height:3px; background:var(--green); }
.kcard.blue::after { content:''; position:absolute; top:0; left:0; right:0; height:3px; background:var(--blue); }
.kcard.orange::after { content:''; position:absolute; top:0; left:0; right:0; height:3px; background:var(--orange); }
.kc-lbl { font-size:9px; font-weight:700; text-transform:uppercase; color:var(--text2); letter-spacing:1px; }
.kc-val { font-family:'Barlow Condensed',sans-serif; font-size:32px; font-weight:700; margin:4px 0; }
.kc-val.orange { color:var(--orange); } .kc-val.green { color:var(--green); } .kc-val.blue { color:var(--blue); }
.decade-wrap { background:var(--white); border:1px solid var(--border); border-radius:10px; padding:15px; box-shadow:var(--sh1); height:100%; }
.decade-grid { display:flex; gap:5px; margin-top:10px; }
.decade-block { flex:1; background:var(--bg); border-radius:6px; padding:8px; text-align:center; }
.decade-block-label { font-size:9px; font-weight:700; color:var(--text2); }
.decade-block-val { font-family:'Barlow Condensed',sans-serif; font-size:18px; font-weight:700; }
.stitle { font-family:'Barlow Condensed',sans-serif; font-size:14px; font-weight:700; text-transform:uppercase; color:var(--text2); margin:20px 0 10px 0; display:flex; align-items:center; gap:8px; }
.stitle::before { content:''; width:4px; height:15px; background:var(--green); border-radius:2px; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════
# CACHE & UTILS
# ══════════════════════════════════════════════════════
CACHE_DIR = ".ocp_cache"
os.makedirs(CACHE_DIR, exist_ok=True)
FILES = ["jorf", "safi", "ventes"]
CACHES = {x: os.path.join(CACHE_DIR, f"{x}.pkl") for x in FILES}

def save_cache(p, d): 
    with open(p, "wb") as f: pickle.dump(d, f)
def load_cache(p):
    if os.path.exists(p):
        try:
            with open(p, "rb") as f: return pickle.load(f)
        except: pass
    return None
def force_n(v):
    if pd.isna(v): return 0.
    try: return float(str(v).replace(" ", "").replace("\xa0", "").replace(",", "."))
    except: return 0.
def fmt(n): return f"{n:,.1f}".replace(",", " ")

# ══════════════════════════════════════════════════════
# NAVIGATION & SESSION
# ══════════════════════════════════════════════════════
if "page" not in st.session_state: st.session_state["page"] = "accueil"

for key in ["jorf_df", "safi_df", "ventes_df"]:
    if key not in st.session_state:
        c = load_cache(CACHES[key.split('_')[0]])
        st.session_state[key] = c["df"] if c else None

with st.sidebar:
    st.markdown('<div style="padding:10px 0 20px 0; font-weight:800; font-size:22px; color:#00843D; text-align:center;">OCP MANUFACTURING</div>', unsafe_allow_html=True)
    NAV = [("accueil", "🏠 Accueil"), ("suivi", "📊 Suivi Chargement"), ("ventes", "💰 Pipeline Ventes")]
    for k, l in NAV:
        if st.button(l, use_container_width=True, type="primary" if st.session_state["page"]==k else "secondary"):
            st.session_state["page"] = k; st.rerun()

page = st.session_state["page"]

# ══════════════════════════════════════════════════════════════════════════════
# PAGE : ACCUEIL (VERSION SÉCURISÉE SANS KEYERROR)
# ══════════════════════════════════════════════════════════════════════════════
if page == "accueil":
    st.markdown('<div class="topbar"><div style="font-size:18px; font-weight:700;">Dashboard Global</div></div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    
    with c1: 
        df_j = st.session_state.get("jorf_df")
        v_j = df_j["TOTAL"].sum() if df_j is not None and "TOTAL" in df_j.columns else 0
        st.markdown(f'<div class="kcard green"><div class="kc-lbl">Jorf Lasfar</div><div class="kc-val green">{fmt(v_j)} KT</div></div>', unsafe_allow_html=True)
    with c2:
        df_s = st.session_state.get("safi_df")
        v_s = df_s["TOTAL"].sum() if df_s is not None and "TOTAL" in df_s.columns else 0
        st.markdown(f'<div class="kcard blue"><div class="kc-lbl">Safi</div><div class="kc-val blue">{fmt(v_s)} KT</div></div>', unsafe_allow_html=True)
    with c3:
        df_v = st.session_state.get("ventes_df")
        v_v = df_v[["D1","D2","D3"]].sum().sum() if df_v is not None and all(x in df_v.columns for x in ["D1","D2","D3"]) else 0
        st.markdown(f'<div class="kcard orange"><div class="kc-lbl">Pipe Ventes</div><div class="kc-val orange">{fmt(v_v)} KT</div></div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE : SUIVI CHARGEMENT (IA MAPPING)
# ══════════════════════════════════════════════════════════════════════════════
elif page == "suivi":
    st.markdown('<div class="topbar"><div style="font-size:18px; font-weight:700;">Suivi Journalier (Jorf / Safi)</div></div>', unsafe_allow_html=True)
    col_j, col_s = st.columns(2)
    
    for col, name, cache_p, sess_k, targets in [
        (col_j, "Jorf Lasfar", CACHES["jorf"], "jorf_df", ["Date", "Export Engrais", "Export Camions", "VL Camions"]),
        (col_s, "Safi", CACHES["safi"], "safi_df", ["Date", "TSP Export", "TSP ML"])
    ]:
        with col:
            st.markdown(f'<div class="stitle">Import {name}</div>', unsafe_allow_html=True)
            f = st.file_uploader(f"Déposer Excel {name}", type=["xlsx", "xlsb"], key=f"up_{sess_k}")
            if f:
                df_raw = pd.read_excel(f)
                with st.expander("🤖 IA : Mapping automatique", expanded=True):
                    mapping = get_smart_mapping(list(df_raw.columns), targets, name)
                    final_map = st.data_editor(mapping, key=f"edit_{sess_k}", use_container_width=True)
                    if st.button(f"Confirmer {name}"):
                        df = df_raw.rename(columns=final_map)
                        df = df[[c for c in targets if c in df.columns]].dropna(subset=["Date"])
                        for c in df.columns: 
                            if c != "Date": df[c] = df[c].apply(force_n)
                        df["TOTAL"] = df.drop(columns=["Date"]).sum(axis=1)
                        st.session_state[sess_k] = df
                        save_cache(cache_p, {"df": df}); st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# PAGE : PIPELINE VENTES (IA DÉCADES)
# ══════════════════════════════════════════════════════════════════════════════
elif page == "ventes":
    st.markdown('<div class="topbar"><div style="font-size:18px; font-weight:700;">Analyse Pipeline Ventes</div></div>', unsafe_allow_html=True)
    
    f_v = st.file_uploader("Fichier Pipeline Ventes", type=["xlsx", "xlsb"], key="up_v")
    if f_v:
        df_raw = pd.read_excel(f_v)
        targets_v = ["Physical Month", "Status Planif", "D1", "D2", "D3"]
        with st.expander("🤖 IA : Détection des colonnes", expanded=True):
            mapping_v = get_smart_mapping(list(df_raw.columns), targets_v, "Pipeline Ventes")
            final_map_v = st.data_editor(mapping_v, use_container_width=True)
            if st.button("Valider Pipeline"):
                df_v = df_raw.rename(columns=final_map_v)
                for d in ["D1", "D2", "D3"]: 
                    if d in df_v.columns: df_v[d] = df_v[d].apply(force_n)
                st.session_state["ventes_df"] = df_v
                save_cache(CACHES["ventes"], {"df": df_v}); st.rerun()

    if st.session_state.get("ventes_df") is not None:
        df = st.session_state["ventes_df"]
        mois = st.selectbox("Mois", df["Physical Month"].unique() if "Physical Month" in df.columns else ["N/A"])
        df_m = df[df["Physical Month"] == mois] if "Physical Month" in df.columns else df
        
        st.markdown('<div class="stitle orange">Situation des décades (KT)</div>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        conf = [(c1, "⚓ En Rade", "purple", "2."), (c2, "🚢 En cours", "green", "1."), (c3, "📦 Chargé", "blue", "0.")]
        
        for col, title, color, code in conf:
            if "Status Planif" in df_m.columns:
                sub = df_m[df_m["Status Planif"].astype(str).str.contains(code, na=False)]
                d1, d2, d3 = [sub[x].sum() if x in sub.columns else 0 for x in ["D1","D2","D3"]]
                with col:
                    st.markdown(f"""<div class="decade-wrap"><div style="font-weight:700;">{title}</div><div class="decade-grid">
                        <div class="decade-block"><div class="decade-block-label">D1</div><div class="decade-block-val">{fmt(d1)}</div></div>
                        <div class="decade-block"><div class="decade-block-label">D2</div><div class="decade-block-val">{fmt(d2)}</div></div>
                        <div class="decade-block"><div class="decade-block-label">D3</div><div class="decade-block-val">{fmt(d3)}</div></div>
                    </div><div style="margin-top:10px;text-align:right;font-weight:800;color:var(--{color});">Total: {fmt(d1+d2+d3)} KT</div></div>""", unsafe_allow_html=True)
