import streamlit as st
import pandas as pd
import re, os, io, pickle, json
from datetime import datetime
import google.generativeai as genai

# ══════════════════════════════════════════════════════
# 1. CONFIGURATION IA (GEMINI)
# ══════════════════════════════════════════════════════
st.set_page_config(page_title="OCP Manufacturing", layout="wide", initial_sidebar_state="expanded")

# Récupération de la clé depuis les Secrets (votre image 1)
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model_ai = genai.GenerativeModel('gemini-1.5-flash')
except:
    st.error("⚠️ Clé GEMINI_API_KEY manquante dans les Secrets Streamlit.")

def get_smart_mapping(df_columns, target_columns):
    """L'IA analyse les noms des colonnes et trouve les correspondances."""
    prompt = f"""
    Tu es un expert en données logistiques. Voici les colonnes d'un fichier Excel : {df_columns}
    Je veux que tu trouves les colonnes qui correspondent à ces 5 concepts : {target_columns}
    
    Règles :
    - 'Physical Month' : Colonne contenant les mois (ex: Mars, Février).
    - 'Status Planif' : Colonne avec les codes (0. Chargé, 1. En cours, 2. En rade).
    - 'D1', 'D2', 'D3' : Colonnes de volumes par décades.
    
    Réponds UNIQUEMENT avec un JSON pur : {{"colonne_excel": "nom_cible"}}
    """
    try:
        response = model_ai.generate_content(prompt)
        clean_json = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(clean_json)
    except: return {}

# ══════════════════════════════════════════════════════
# 2. FONCTIONS DE NETTOYAGE & DESIGN
# ══════════════════════════════════════════════════════
def force_n(v):
    if pd.isna(v): return 0.
    try: return float(str(v).replace(" ", "").replace("\xa0", "").replace(",", "."))
    except: return 0.

def fmt(n): return f"{n:,.1f}".replace(",", " ")

st.markdown("""
<style>
    .kcard { background:white; border-radius:10px; padding:20px; box-shadow:0 1px 3px rgba(0,0,0,0.1); border-top:3px solid #00843D; }
    .decade-wrap { background:white; border-radius:10px; padding:15px; border:1px solid #EEE; margin-bottom:10px; }
    .decade-grid { display:flex; gap:8px; margin-top:10px; }
    .decade-block { flex:1; background:#F8F9FA; border-radius:8px; padding:10px; text-align:center; }
    .stitle { font-weight:700; color:#4A5568; text-transform:uppercase; margin:20px 0 10px 0; display:flex; align-items:center; gap:8px; }
    .stitle::before { content:''; width:3px; height:14px; background:#00843D; border-radius:2px; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════
# 3. NAVIGATION & SESSION
# ══════════════════════════════════════════════════════
if "page" not in st.session_state: st.session_state["page"] = "accueil"
if "ventes_df" not in st.session_state: st.session_state["ventes_df"] = None

with st.sidebar:
    st.title("OCP Dashboard")
    if st.button("🏠 Accueil", use_container_width=True): st.session_state.page = "accueil"; st.rerun()
    if st.button("💰 Pipeline Ventes", use_container_width=True): st.session_state.page = "ventes"; st.rerun()

# ══════════════════════════════════════════════════════
# PAGE ACCUEIL (CORRECTION ERREUR IMAGE 2)
# ══════════════════════════════════════════════════════
if st.session_state.page == "accueil":
    st.header("Dashboard Global")
    c1, c2 = st.columns(2)
    with c1:
        dfv = st.session_state.get("ventes_df")
        # Protection contre KeyError : on vérifie si les colonnes existent avant le calcul
        if dfv is not None and all(c in dfv.columns for c in ["D1", "D2", "D3"]):
            total_v = dfv[["D1", "D2", "D3"]].sum().sum()
            st.metric("Total Pipeline Ventes", f"{fmt(total_v)} KT")
        else:
            st.info("En attente de données Pipeline...")

# ══════════════════════════════════════════════════════
# PAGE PIPELINE VENTES (GESTION IMAGE 3)
# ══════════════════════════════════════════════════════
elif st.session_state.page == "ventes":
    st.header("Pipeline des Ventes")
    
    f = st.file_uploader("Uploader le fichier Excel", type=["xlsx", "xlsb"])
    if f:
        # On lit tous les onglets pour laisser l'IA ou l'utilisateur choisir
        xl = pd.ExcelFile(f)
        onglet = st.selectbox("Sélectionner l'onglet (ex: January)", xl.sheet_names)
        df_raw = xl.parse(onglet)
        
        # Les 5 colonnes qui vous intéressent (votre demande)
        targets = ["Physical Month", "Status Planif", "D1", "D2", "D3"]
        
        with st.expander("🤖 Analyse intelligente des colonnes", expanded=True):
            # L'IA fait le mapping
            mapping = get_smart_mapping(list(df_raw.columns), targets)
            final_map = st.data_editor(mapping, use_container_width=True)
            
            if st.button("Valider et Afficher les Décades"):
                df_v = df_raw.rename(columns=final_map)
                # On ne garde que vos 5 colonnes
                cols_ok = [c for c in targets if c in df_v.columns]
                df_v = df_v[cols_ok]
                
                # Conversion numérique des décades
                for d in ["D1", "D2", "D3"]:
                    if d in df_v.columns: df_v[d] = df_v[d].apply(force_n)
                
                st.session_state["ventes_df"] = df_v
                st.rerun()

    # Affichage des cartes si données prêtes
    if st.session_state.ventes_df is not None:
        df = st.session_state.ventes_df
        if "Physical Month" in df.columns:
            mois = st.selectbox("Filtrer par mois", df["Physical Month"].unique())
            df_m = df[df["Physical Month"] == mois]
            
            st.markdown(f'<div class="stitle">Situation — {mois}</div>', unsafe_allow_html=True)
            c1, c2, c3 = st.columns(3)
            confs = [(c1, "⚓ En Rade", "purple", "2."), (c2, "🚢 En cours", "green", "1."), (c3, "📦 Chargé", "blue", "0.")]
            
            for col, title, color, code in confs:
                if "Status Planif" in df_m.columns:
                    sub = df_m[df_m["Status Planif"].astype(str).str.contains(code, na=False)]
                    d1, d2, d3 = [sub[x].sum() if x in sub.columns else 0 for x in ["D1", "D2", "D3"]]
                    with col:
                        st.markdown(f"""
                        <div class="decade-wrap" style="border-top: 3px solid {color}">
                            <div style="font-weight:700;">{title}</div>
                            <div class="decade-grid">
                                <div class="decade-block"><div style="font-size:9px">D1</div><div style="font-weight:700">{fmt(d1)}</div></div>
                                <div class="decade-block"><div style="font-size:9px">D2</div><div style="font-weight:700">{fmt(d2)}</div></div>
                                <div class="decade-block"><div style="font-size:9px">D3</div><div style="font-weight:700">{fmt(d3)}</div></div>
                            </div>
                        </div>""", unsafe_allow_html=True)
            
            st.markdown('<div class="stitle">Table de détail</div>', unsafe_allow_html=True)
            st.dataframe(df_m, use_container_width=True, hide_index=True)
