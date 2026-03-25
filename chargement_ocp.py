import streamlit as st
import pandas as pd
import re, os, io, pickle, json
from datetime import datetime
import google.generativeai as genai

# ══════════════════════════════════════════════════════
# 1. CONFIGURATION & IA
# ══════════════════════════════════════════════════════
st.set_page_config(page_title="OCP Manufacturing", layout="wide", initial_sidebar_state="expanded")

if "page" not in st.session_state: st.session_state["page"] = "accueil"
if "ventes_df" not in st.session_state: st.session_state["ventes_df"] = None

try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model_ai = genai.GenerativeModel('gemini-1.5-flash')
except:
    st.error("⚠️ Clé API Gemini manquante dans les Secrets Streamlit.")

def get_smart_mapping(df_columns, target_columns):
    """L'IA travaille sur une liste de colonnes propre d'un seul onglet."""
    prompt = f"""
    En tant qu'expert OCP, analyse ces colonnes Excel : {df_columns}
    Trouve les correspondances pour : {target_columns}
    Note : 'Month' est la colonne temporelle, 'Status Planif' contient les codes 0, 1 ou 2.
    Réponds UNIQUEMENT avec ce JSON : {{"nom_excel": "nom_cible"}}
    """
    try:
        response = model_ai.generate_content(prompt)
        clean_json = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(clean_json)
    except: return {}

# ══════════════════════════════════════════════════════
# 2. DESIGN & UTILS (VOTRE STYLE)
# ══════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow:wght@400;600;700&display=swap');
:root { --green: #00843D; --blue: #1565C0; --orange: #C05A00; --purple: #6B3FA0; --bg: #F2F4F7; }
html,body,[class*="css"] { font-family:'Barlow',sans-serif !important; }
.stApp { background:var(--bg) !important; }
.topbar { background:white; border-bottom:1px solid #E0E4EA; padding:12px 1.8rem; margin:0 -1.8rem 20px -1.8rem; display:flex; justify-content:space-between; box-shadow:0 1px 3px rgba(0,0,0,0.07); }
.decade-wrap { background:white; border-radius:10px; padding:18px 20px; box-shadow:0 1px 3px rgba(0,0,0,0.07); margin-bottom:10px; border-top:3px solid var(--green); }
.decade-grid { display:flex; gap:8px; margin-top:10px; }
.decade-block { flex:1; background:var(--bg); border-radius:8px; padding:10px; text-align:center; }
.decade-block-val { font-size:20px; font-weight:700; color:var(--green); }
.stitle { font-weight:700; text-transform:uppercase; color:#4A5568; margin:20px 0 10px 0; display:flex; align-items:center; gap:8px; }
.stitle::before { content:''; width:3px; height:14px; background:var(--green); border-radius:2px; }
</style>
""", unsafe_allow_html=True)

def fmt(n): return f"{n:,.1f}".replace(",", " ")
def force_n(v):
    if pd.isna(v): return 0.
    try: return float(str(v).replace(" ", "").replace("\xa0", "").replace(",", "."))
    except: return 0.

# ══════════════════════════════════════════════════════
# 3. NAVIGATION
# ══════════════════════════════════════════════════════
with st.sidebar:
    st.markdown('<div style="padding:20px; font-weight:800; font-size:20px; color:#00843D;">OCP DASHBOARD</div>', unsafe_allow_html=True)
    if st.button("🏠 Accueil", use_container_width=True): st.session_state.page = "accueil"; st.rerun()
    if st.button("💰 Pipeline Ventes", use_container_width=True): st.session_state.page = "ventes"; st.rerun()

# ══════════════════════════════════════════════════════
# PAGE : ACCUEIL
# ══════════════════════════════════════════════════════
if st.session_state.page == "accueil":
    st.markdown('<div class="topbar"><div>Dashboard Global</div></div>', unsafe_allow_html=True)
    dfv = st.session_state.get("ventes_df")
    val_v = dfv[["D1","D2","D3"]].sum().sum() if dfv is not None and "D1" in dfv.columns else 0
    st.metric("Total Pipeline Ventes", f"{fmt(val_v)} KT")

# ══════════════════════════════════════════════════════
# PAGE : PIPELINE VENTES (AIDE À L'IA)
# ══════════════════════════════════════════════════════
elif st.session_state.page == "ventes":
    st.markdown('<div class="topbar"><div>Pipeline des Ventes — Chargement Intelligent</div></div>', unsafe_allow_html=True)
    
    uc1, uc2 = st.columns([1, 1])
    with uc1:
        st.markdown('<div class="upload-zone">', unsafe_allow_html=True)
        f_v = st.file_uploader("Fichier Pipeline Ventes", type=["xlsx", "xlsb"])
        if f_v:
            # ÉTAPE 1 : On aide l'IA en listant les onglets
            xl = pd.ExcelFile(f_v)
            onglet_sel = st.selectbox("🎯 Étape 1 : Choisir l'onglet de données", xl.sheet_names, index=1 if "January" in xl.sheet_names else 0)
            
            # ÉTAPE 2 : On charge uniquement cet onglet
            df_raw = pd.read_excel(f_v, sheet_name=onglet_sel)
            targets = ["Month", "Status Planif", "D1", "D2", "D3"]
            
            # ÉTAPE 3 : L'IA travaille sur des colonnes propres
            with st.expander("🤖 Étape 2 : L'IA mappe les colonnes", expanded=True):
                mapping = get_smart_mapping(list(df_raw.columns), targets)
                final_map = st.data_editor(mapping, use_container_width=True)
                
                if st.button("🚀 Valider et Afficher"):
                    df_v = df_raw.rename(columns=final_map)
                    for d in ["D1", "D2", "D3"]: 
                        if d in df_v.columns: df_v[d] = df_v[d].apply(force_n)
                    st.session_state["ventes_df"] = df_v
                    st.success(f"Données de l'onglet '{onglet_sel}' chargées !")
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # AFFICHAGE DES CARTES
    if st.session_state.get("ventes_df") is not None:
        df_all = st.session_state["ventes_df"]
        
        # Filtre interne par la colonne Month
        if "Month" in df_all.columns:
            liste_m = df_all["Month"].dropna().unique()
            m_sel = st.selectbox("📅 Sélectionner le Mois dans la table", liste_m)
            df_m = df_all[df_all["Month"] == m_sel]
        else:
            df_m = df_all
            m_sel = "Toutes périodes"

        st.markdown(f'<div class="stitle orange">Situation — {m_sel}</div>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        confs = [(c1, "⚓ En Rade", "#6B3FA0", "2."), (c2, "🚢 En cours", "#00843D", "1."), (c3, "📦 Chargé", "#1565C0", "0.")]
        
        for col, title, color, code in confs:
            if "Status Planif" in df_m.columns:
                sub = df_m[df_m["Status Planif"].astype(str).str.contains(code, na=False)]
                d1, d2, d3 = sub["D1"].sum(), sub["D2"].sum(), sub["D3"].sum()
                with col:
                    st.markdown(f"""
                    <div class="decade-wrap" style="border-top-color:{color}">
                        <div style="font-weight:700; color:{color};">{title}</div>
                        <div class="decade-grid">
                            <div class="decade-block"><div style="font-size:9px">D1</div><div class="decade-block-val">{fmt(d1)}</div></div>
                            <div class="decade-block"><div style="font-size:9px">D2</div><div class="decade-block-val">{fmt(d2)}</div></div>
                            <div class="decade-block"><div style="font-size:9px">D3</div><div class="decade-block-val">{fmt(d3)}</div></div>
                        </div>
                        <div style="text-align:right; font-weight:800; margin-top:10px;">{fmt(d1+d2+d3)} KT</div>
                    </div>""", unsafe_allow_html=True)

        st.markdown('<div class="stitle">Table de détail</div>', unsafe_allow_html=True)
        st.dataframe(df_m[["Month", "Status Planif", "D1", "D2", "D3"]], use_container_width=True, hide_index=True)
