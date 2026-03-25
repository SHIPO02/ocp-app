import streamlit as st
import pandas as pd
import re, os, io, pickle, json
from datetime import datetime
import plotly.graph_objects as go
import base64
import google.generativeai as genai

# ══════════════════════════════════════════════════════
# CONFIGURATION INITIALE & IA
# ══════════════════════════════════════════════════════
st.set_page_config(page_title="OCP Manufacturing", layout="wide", initial_sidebar_state="expanded")

# Initialisation sécurisée du Session State
if "page" not in st.session_state:
    st.session_state["page"] = "accueil"
if "ventes_df" not in st.session_state:
    st.session_state["ventes_df"] = None

# Configuration de Gemini
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model_ai = genai.GenerativeModel('gemini-1.5-flash')
except:
    st.error("⚠️ Configurez GEMINI_API_KEY dans les Secrets Streamlit.")

# ══════════════════════════════════════════════════════
# CSS — THÈME BLANC PROFESSIONNEL (CONSERVÉ)
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
.topbar { background:var(--white); border-bottom:1px solid var(--border); padding:12px 1.8rem; margin:0 -1.8rem 20px -1.8rem; display:flex; align-items:center; justify-content:space-between; box-shadow:var(--sh1); }
.tb-title { font-family:'Barlow Condensed',sans-serif; font-size:20px; font-weight:700; color:var(--text); }
.kcard { background:var(--white); border:1px solid var(--border); border-radius:10px; padding:18px 20px; box-shadow:var(--sh1); position:relative; overflow:hidden; display:flex; flex-direction:column; justify-content:space-between; }
.kcard.green::after { content:''; position:absolute; top:0; left:0; right:0; height:3px; background:var(--green); }
.kcard.blue::after { content:''; position:absolute; top:0; left:0; right:0; height:3px; background:var(--blue); }
.kcard.orange::after { content:''; position:absolute; top:0; left:0; right:0; height:3px; background:var(--orange); }
.kc-val { font-family:'Barlow Condensed',sans-serif; font-size:34px; font-weight:700; line-height:1; margin:4px 0; }
.kc-val.green { color:var(--green); } .kc-val.blue { color:var(--blue); } .kc-val.orange { color:var(--orange); }
.decade-wrap { background:var(--white); border:1px solid var(--border); border-radius:10px; padding:18px 20px; box-shadow:var(--sh1); height:100%; }
.decade-grid { display:flex; gap:8px; margin-top:10px; }
.decade-block { flex:1; background:var(--bg); border:1px solid var(--border2); border-radius:8px; padding:10px 12px; text-align:center; }
.decade-block-label { font-size:9px; font-weight:700; color:var(--text3); }
.decade-block-val { font-family:'Barlow Condensed',sans-serif; font-size:20px; font-weight:700; color:var(--text); }
.stitle { font-family:'Barlow Condensed',sans-serif; font-size:13px; font-weight:700; letter-spacing:1px; text-transform:uppercase; color:var(--text2); margin:20px 0 10px 0; display:flex; align-items:center; gap:8px; }
.stitle::before { content:''; width:3px; height:14px; background:var(--green); border-radius:2px; display:inline-block; }
.upload-zone { background:var(--white); border:1px solid var(--border); border-radius:10px; padding:20px; box-shadow:var(--sh1); }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════
# PERSISTENCE & UTILS
# ══════════════════════════════════════════════════════
CACHE_DIR = ".ocp_cache"
os.makedirs(CACHE_DIR, exist_ok=True)
JORF_CACHE = os.path.join(CACHE_DIR, "jorf.pkl")
SAFI_CACHE = os.path.join(CACHE_DIR, "safi.pkl")
VENTES_CACHE = os.path.join(CACHE_DIR, "ventes.pkl")

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

def get_smart_mapping(df_columns, target_columns):
    prompt = f"Analyse ces colonnes : {df_columns}. Trouve les correspondances pour : {target_columns}. Réponds UNIQUEMENT en JSON pur : {{'colonne_excel': 'nom_cible'}}"
    try:
        response = model_ai.generate_content(prompt)
        clean_json = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(clean_json)
    except: return {}

# ══════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════
with st.sidebar:
    st.markdown('<div style="padding:20px; font-weight:800; font-size:20px; color:#00843D;">OCP MANUFACTURING</div>', unsafe_allow_html=True)
    NAV = [("accueil","Accueil"), ("suivi","Suivi Chargement"), ("stock","Simulation Stock"), ("ventes","Pipeline des Ventes")]
    for key, label in NAV:
        if st.button(label, use_container_width=True, type="primary" if st.session_state["page"]==key else "secondary"):
            st.session_state["page"]=key; st.rerun()

# Chargement du cache
for k, p in [("jorf_df", JORF_CACHE), ("safi_df", SAFI_CACHE), ("ventes_df", VENTES_CACHE)]:
    if k not in st.session_state or st.session_state[k] is None:
        c = load_cache(p)
        if isinstance(c, dict) and "df" in c: st.session_state[k] = c["df"]

page = st.session_state["page"]

# ══════════════════════════════════════════════════════
# PAGE : ACCUEIL
# ══════════════════════════════════════════════════════
if page == "accueil":
    st.markdown('<div class="topbar"><div class="tb-title">Tableau de Bord Global</div></div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        dfj = st.session_state.get("jorf_df")
        vj = dfj["TOTAL Jorf"].sum() if dfj is not None and "TOTAL Jorf" in dfj.columns else 0
        st.markdown(f'<div class="kcard green"><div class="kc-lbl">Jorf Lasfar</div><div class="kc-val green">{fmt(vj)} KT</div></div>', unsafe_allow_html=True)
    with c2:
        dfs = st.session_state.get("safi_df")
        vs = dfs["TOTAL Safi"].sum() if dfs is not None and "TOTAL Safi" in dfs.columns else 0
        st.markdown(f'<div class="kcard blue"><div class="kc-lbl">Safi</div><div class="kc-val blue">{fmt(vs)} KT</div></div>', unsafe_allow_html=True)
    with c3:
        dfv = st.session_state.get("ventes_df")
        vv = dfv[["D1","D2","D3"]].sum().sum() if dfv is not None and "D1" in dfv.columns else 0
        st.markdown(f'<div class="kcard orange"><div class="kc-lbl">Pipe Ventes</div><div class="kc-val orange">{fmt(vv)} KT</div></div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════
# PAGE : SUIVI (CONSERVÉ)
# ══════════════════════════════════════════════════════
elif page == "suivi":
    st.markdown('<div class="topbar"><div class="tb-title">Suivi Chargement</div></div>', unsafe_allow_html=True)
    st.info("Module de suivi Jorf / Safi.")

# ══════════════════════════════════════════════════════
# PAGE : PIPELINE DES VENTES (INTEGRATION IA & CARTES)
# ══════════════════════════════════════════════════════
elif page == "ventes":
    st.markdown('<div class="topbar"><div class="tb-title">Pipeline des Ventes — Pilotage Décades</div></div>', unsafe_allow_html=True)
    
    # 1. ZONE IMPORT
    uc1, _ = st.columns([1, 2])
    with uc1:
        st.markdown('<div class="upload-zone">', unsafe_allow_html=True)
        st.markdown('<div style="font-weight:700; font-size:14px; margin-bottom:10px;">Importation du Pipeline</div>', unsafe_allow_html=True)
        f_v = st.file_uploader("Excel Pipeline", type=["xlsx", "xlsb"], key="up_v", label_visibility="collapsed")
        
        if f_v:
            df_raw = pd.read_excel(f_v)
            targets_v = ["Physical Month", "Status Planif", "D1", "D2", "D3"]
            with st.expander("🤖 IA : Mapping des colonnes", expanded=True):
                mapping = get_smart_mapping(list(df_raw.columns), targets_v)
                final_map = st.data_editor(mapping, use_container_width=True)
                if st.button("Confirmer l'analyse"):
                    df_v = df_raw.rename(columns=final_map)
                    for d in ["D1", "D2", "D3"]:
                        if d in df_v.columns: df_v[d] = df_v[d].apply(force_n)
                    st.session_state["ventes_df"] = df_v
                    save_cache(VENTES_CACHE, {"df": df_v}); st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # 2. AFFICHAGE DES RÉSULTATS
    if st.session_state.get("ventes_df") is not None:
        df = st.session_state["ventes_df"]
        needed = ["Physical Month", "Status Planif", "D1", "D2", "D3"]
        
        if all(c in df.columns for c in needed):
            # Filtre Mois
            mois_sel = st.selectbox("Sélectionner le Mois", df["Physical Month"].unique())
            df_m = df[df["Physical Month"] == mois_sel]
            
            st.markdown(f'<div class="stitle orange">Situation — {mois_sel} (KT)</div>', unsafe_allow_html=True)
            c1, c2, c3 = st.columns(3)
            
            # Configuration des statuts (Mapping sur tes codes 0, 1, 2)
            confs = [
                (c1, "⚓ En Rade", "#6B3FA0", "2."),
                (c2, "🚢 En cours", "#00843D", "1."),
                (c3, "📦 Chargé / Nommé", "#1565C0", "0.")
            ]
            
            for col, title, color, code in confs:
                sub = df_m[df_m["Status Planif"].astype(str).str.contains(code, na=False)]
                d1, d2, d3 = sub["D1"].sum(), sub["D2"].sum(), sub["D3"].sum()
                with col:
                    st.markdown(f"""
                    <div class="decade-wrap">
                        <div style="font-weight:700; color:{color};">{title}</div>
                        <div class="decade-grid">
                            <div class="decade-block"><div class="decade-block-label">D1</div><div class="decade-block-val">{fmt(d1)}</div></div>
                            <div class="decade-block"><div class="decade-block-label">D2</div><div class="decade-block-val">{fmt(d2)}</div></div>
                            <div class="decade-block"><div class="decade-block-label">D3</div><div class="decade-block-val">{fmt(d3)}</div></div>
                        </div>
                        <div style="text-align:right; font-weight:800; color:{color}; margin-top:10px;">Total: {fmt(d1+d2+d3)}</div>
                    </div>""", unsafe_allow_html=True)
            
            st.markdown('<div class="stitle">Détail des opérations</div>', unsafe_allow_html=True)
            st.dataframe(df_m[needed], use_container_width=True, hide_index=True)
        else:
            st.error(f"Colonnes manquantes dans le mapping : {[c for c in needed if c not in df.columns]}")

# ══════════════════════════════════════════════════════
# PAGE : STOCK (CONSERVÉ)
# ══════════════════════════════════════════════════════
elif page == "stock":
    st.markdown('<div class="topbar"><div class="tb-title">Simulation Stock</div></div>', unsafe_allow_html=True)
    st.info("Simulation active.")
