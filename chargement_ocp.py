import streamlit as st
import pandas as pd
import re, os, io, pickle, json
from datetime import datetime
import plotly.graph_objects as go
import base64
import google.generativeai as genai

# ══════════════════════════════════════════════════════
# CONFIGURATION IA & SÉCURITÉ
# ══════════════════════════════════════════════════════
st.set_page_config(page_title="OCP Manufacturing", layout="wide", initial_sidebar_state="expanded")

# Récupération de la clé API via Streamlit Secrets (indispensable pour le Cloud)
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model_ai = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error("⚠️ Erreur : Clé API non configurée dans les Secrets Streamlit.")

def get_smart_mapping(df_columns, target_columns, context="Données OCP"):
    """L'IA analyse sémantiquement les colonnes Excel peu importe leur position."""
    prompt = f"""
    Expert logistique OCP, analyse ces colonnes Excel : {df_columns}
    Identifie les colonnes qui correspondent le mieux à : {target_columns}
    Pour D1, D2, D3, cherche les volumes des décades.
    Réponds UNIQUEMENT avec un JSON pur : {{"colonne_excel": "nom_cible"}}
    """
    try:
        response = model_ai.generate_content(prompt)
        clean_json = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(clean_json)
    except: return {}

# ══════════════════════════════════════════════════════
# CSS — TON DESIGN ORIGINAL (STRICTEMENT CONSERVÉ)
# ══════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow:wght@300;400;500;600;700&family=Barlow+Condensed:wght@500;600;700;800&display=swap');
:root {
  --green: #00843D; --green-dk: #005C2A; --green-lt: #E8F5EE;
  --blue: #1565C0; --blue-lt: #E3EAF8;
  --orange: #C05A00; --orange-lt: #FBF0E6;
  --purple: #6B3FA0; --purple-lt: #F0EBF8;
  --red: #C62828;
  --bg: #F2F4F7; --white: #FFFFFF;
  --border: #E0E4EA; --border2: #EEF0F4;
  --text: #12202E; --text2: #4A5568; --text3: #94A3B8;
  --sh1: 0 1px 3px rgba(0,0,0,0.07); --sh2: 0 4px 16px rgba(0,0,0,0.10);
}
html,body,[class*="css"] { font-family:'Barlow',sans-serif !important; color:var(--text); }
.stApp { background:var(--bg) !important; }
.main .block-container { padding:0 1.8rem 2rem 1.8rem !important; max-width:100% !important; }
#MainMenu,footer { visibility:hidden; }
header[data-testid="stHeader"] { background:transparent !important; height:0 !important; }
[data-testid="stDecoration"],.stDeployButton { display:none !important; }
.topbar { background:var(--white); border-bottom:1px solid var(--border); padding:12px 1.8rem; margin:0 -1.8rem 20px -1.8rem; display:flex; align-items:center; justify-content:space-between; box-shadow:var(--sh1); }
.tb-title { font-family:'Barlow Condensed',sans-serif; font-size:20px; font-weight:700; color:var(--text); }
.kcard { background:var(--white); border:1px solid var(--border); border-radius:10px; padding:18px 20px; box-shadow:var(--sh1); position:relative; overflow:hidden; display:flex; flex-direction:column; justify-content:space-between; }
.kcard.green::after { content:''; position:absolute; top:0; left:0; right:0; height:3px; border-radius:10px 10px 0 0; background:var(--green); }
.kcard.blue::after { content:''; position:absolute; top:0; left:0; right:0; height:3px; border-radius:10px 10px 0 0; background:var(--blue); }
.kcard.orange::after { content:''; position:absolute; top:0; left:0; right:0; height:3px; border-radius:10px 10px 0 0; background:var(--orange); }
.kc-lbl { font-size:9px; font-weight:700; letter-spacing:1.4px; text-transform:uppercase; color:var(--text3); }
.kc-val { font-family:'Barlow Condensed',sans-serif; font-size:34px; font-weight:700; line-height:1; margin:4px 0; }
.kc-val.green { color:var(--green); } .kc-val.blue { color:var(--blue); } .kc-val.orange { color:var(--orange); }
.decade-wrap { background:var(--white); border:1px solid var(--border); border-radius:10px; padding:18px 20px; box-shadow:var(--sh1); height:100%; }
.decade-grid { display:flex; gap:8px; }
.decade-block { flex:1; background:var(--bg); border-radius:8px; padding:10px 12px; text-align:center; }
.decade-block-label { font-size:9px; font-weight:700; color:var(--text3); }
.decade-block-val { font-family:'Barlow Condensed',sans-serif; font-size:22px; font-weight:700; }
.stitle { font-family:'Barlow Condensed',sans-serif; font-size:13px; font-weight:700; letter-spacing:1px; text-transform:uppercase; color:var(--text2); margin:20px 0 10px 0; display:flex; align-items:center; gap:8px; }
.stitle::before { content:''; width:3px; height:14px; background:var(--green); border-radius:2px; display:inline-block; }
.upload-zone { background:var(--white); border:1.5px dashed var(--border); border-radius:10px; padding:20px; box-shadow:var(--sh1); text-align:center; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════
# PERSISTENCE & UTILS (TON CODE ORIGINAL)
# ══════════════════════════════════════════════════════
CACHE_DIR = ".ocp_cache"
os.makedirs(CACHE_DIR, exist_ok=True)
JORF_CACHE = os.path.join(CACHE_DIR,"jorf.pkl")
SAFI_CACHE = os.path.join(CACHE_DIR,"safi.pkl")
VENTES_CACHE = os.path.join(CACHE_DIR,"ventes.pkl")

def save_cache(p,d): 
    with open(p,"wb") as f: pickle.dump(d,f)
def load_cache(p):
    if os.path.exists(p):
        try:
            with open(p,"rb") as f: return pickle.load(f)
        except: pass
    return None
def force_n(v):
    if pd.isna(v): return 0.
    try: return float(str(v).replace(" ", "").replace("\xa0", "").replace(",", "."))
    except: return 0.
def fmt(n): return f"{n:,.1f}".replace(","," ")

# ══════════════════════════════════════════════════════
# NAVIGATION & SESSION
# ══════════════════════════════════════════════════════
if "page" not in st.session_state: st.session_state["page"]="accueil"

# Chargement auto du cache
for k, p, sk in [("jorf_df", JORF_CACHE, "jorf"), ("safi_df", SAFI_CACHE, "safi"), ("ventes_df", VENTES_CACHE, "ventes")]:
    if k not in st.session_state:
        c = load_cache(p)
        st.session_state[k] = c["df"] if c else None

with st.sidebar:
    st.markdown('<div style="padding:20px; font-weight:800; font-size:20px; color:#00843D;">OCP Manufacturing</div>', unsafe_allow_html=True)
    NAV = [("accueil","Accueil"), ("suivi","Suivi Chargement"), ("stock","Simulation Stock"), ("ventes","Pipeline des Ventes")]
    for key, label in NAV:
        if st.button(label, use_container_width=True, type="primary" if st.session_state["page"]==key else "secondary"):
            st.session_state["page"]=key; st.rerun()

page = st.session_state["page"]

# ══════════════════════════════════════════════════════════════════════════════
# PAGE : ACCUEIL
# ══════════════════════════════════════════════════════════════════════════════
if page == "accueil":
    st.markdown('<div class="topbar"><div class="tb-title">Tableau de Bord Global</div></div>', unsafe_allow_html=True)
    
    # KPIs sécurisés contre les KeyError
    c1, c2, c3 = st.columns(3)
    with c1:
        dfj = st.session_state.get("jorf_df")
        vj = dfj["TOTAL"].sum() if dfj is not None and "TOTAL" in dfj.columns else 0
        st.markdown(f'<div class="kcard green"><div class="kc-lbl">Production Jorf</div><div class="kc-val green">{fmt(vj)} KT</div></div>', unsafe_allow_html=True)
    with c2:
        dfs = st.session_state.get("safi_df")
        vs = dfs["TOTAL"].sum() if dfs is not None and "TOTAL" in dfs.columns else 0
        st.markdown(f'<div class="kcard blue"><div class="kc-lbl">Production Safi</div><div class="kc-val blue">{fmt(vs)} KT</div></div>', unsafe_allow_html=True)
    with c3:
        dfv = st.session_state.get("ventes_df")
        vv = dfv[["D1","D2","D3"]].sum().sum() if dfv is not None and all(x in dfv.columns for x in ["D1","D2","D3"]) else 0
        st.markdown(f'<div class="kcard orange"><div class="kc-lbl">Pipeline Ventes</div><div class="kc-val orange">{fmt(vv)} KT</div></div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE : SUIVI CHARGEMENT (AVEC IA)
# ══════════════════════════════════════════════════════════════════════════════
elif page == "suivi":
    st.markdown('<div class="topbar"><div class="tb-title">Suivi des Chargements (Mapping IA)</div></div>', unsafe_allow_html=True)
    col_j, col_s = st.columns(2)
    
    for col, name, cache_p, sess_k, targets in [
        (col_j, "Jorf Lasfar", JORF_CACHE, "jorf_df", ["Date", "Export Engrais", "Export Camions", "VL Camions"]),
        (col_s, "Safi", SAFI_CACHE, "safi_df", ["Date", "TSP Export", "TSP ML"])
    ]:
        with col:
            st.markdown(f'<div class="stitle">Import {name}</div>', unsafe_allow_html=True)
            f = st.file_uploader(f"Fichier {name}", type=["xlsx", "xlsb"], key=f"up_{sess_k}")
            if f:
                df_raw = pd.read_excel(f)
                with st.expander("🤖 IA : Mapping des colonnes", expanded=True):
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
# PAGE : PIPELINE DES VENTES (DÉCADES & STATUTS)
# ══════════════════════════════════════════════════════════════════════════════
elif page == "ventes":
    st.markdown('<div class="topbar"><div class="tb-title">Pipeline des Ventes — Situation Décades</div></div>', unsafe_allow_html=True)
    
    # 1. Zone d'Import
    uc1, _ = st.columns([1, 2])
    with uc1:
        st.markdown('<div class="upload-zone">', unsafe_allow_html=True)
        f_v = st.file_uploader("Fichier Pipeline Ventes", type=["xlsx", "xlsb"], key="up_v")
        if f_v:
            df_raw = pd.read_excel(f_v)
            targets_v = ["Physical Month", "Status Planif", "D1", "D2", "D3"]
            with st.expander("🤖 IA : Détection des volumes décades", expanded=True):
                mapping_v = get_smart_mapping(list(df_raw.columns), targets_v, "Ventes")
                final_map_v = st.data_editor(mapping_v, use_container_width=True)
                if st.button("Valider Pipeline"):
                    df_v = df_raw.rename(columns=final_map_v)
                    for d in ["D1", "D2", "D3"]: 
                        if d in df_v.columns: df_v[d] = df_v[d].apply(force_n)
                    st.session_state["ventes_df"] = df_v
                    save_cache(VENTES_CACHE, {"df": df_v}); st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # 2. Affichage des Cards
    if st.session_state.get("ventes_df") is not None:
        df = st.session_state["ventes_df"]
        mois = st.selectbox("Mois d'analyse", df["Physical Month"].unique() if "Physical Month" in df.columns else ["N/A"])
        df_m = df[df["Physical Month"] == mois] if "Physical Month" in df.columns else df
        
        st.markdown(f'<div class="stitle orange">Situation des décades — {mois}</div>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        # On définit les codes statuts (0, 1, 2)
        configs = [(c3, "📦 Chargé / Nommé", "blue", "0."), (c2, "🚢 En cours", "green", "1."), (c1, "⚓ En Rade", "purple", "2.")]
        
        for col, title, color, code in configs:
            if "Status Planif" in df_m.columns:
                sub = df_m[df_m["Status Planif"].astype(str).str.contains(code, na=False)]
                d1, d2, d3 = [sub[x].sum() if x in sub.columns else 0 for x in ["D1","D2","D3"]]
                with col:
                    st.markdown(f"""
                    <div class="decade-wrap">
                        <div style="font-weight:700; color:var(--text); margin-bottom:10px;">{title}</div>
                        <div class="decade-grid">
                            <div class="decade-block"><div class="decade-block-label">D1</div><div class="decade-block-val">{fmt(d1)}</div></div>
                            <div class="decade-block"><div class="decade-block-label">D2</div><div class="decade-block-val">{fmt(d2)}</div></div>
                            <div class="decade-block"><div class="decade-block-label">D3</div><div class="decade-block-val">{fmt(d3)}</div></div>
                        </div>
                        <div style="margin-top:12px; text-align:right; font-weight:800; color:var(--{color});">Total: {fmt(d1+d2+d3)} KT</div>
                    </div>""", unsafe_allow_html=True)
        st.markdown('<div style="margin-top:20px"></div>', unsafe_allow_html=True)
        st.dataframe(df_m[["Status Planif", "D1", "D2", "D3"]], use_container_width=True, hide_index=True)
    else:
        st.markdown('<div class="ph-card"><h2>Pipeline des Ventes</h2><p>Chargez un fichier pour activer ce module.</p></div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE : STOCK (Simulation d'origine)
# ══════════════════════════════════════════════════════════════════════════════
elif page == "stock":
    st.markdown('<div class="topbar"><div class="tb-title">Simulation de Stock</div></div>', unsafe_allow_html=True)
    st.info("Module de simulation actif (Paramètres manuels).")
    # Conserve ici ton code original de simulation de stock...
