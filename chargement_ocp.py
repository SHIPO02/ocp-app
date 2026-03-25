import streamlit as st
import pandas as pd
import json
import google.generativeai as genai
import os

# 1. CONFIGURATION (TOUJOURS EN PREMIER)
st.set_page_config(page_title="OCP Pipeline", layout="wide")

# Initialisation des variables de session
if "ventes_df" not in st.session_state:
    st.session_state["ventes_df"] = None
if "page" not in st.session_state:
    st.session_state["page"] = "ventes"

# Configuration IA
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model_ai = genai.GenerativeModel('gemini-1.5-flash')
except:
    st.error("Clé API non trouvée dans les Secrets.")

# 2. FONCTIONS SUPPORTS
def fmt(n): 
    return f"{n:,.1f}".replace(",", " ")

def force_n(v):
    if pd.isna(v): return 0.
    try: return float(str(v).replace(" ", "").replace(",", "."))
    except: return 0.

def get_smart_mapping(df_columns, target_columns):
    prompt = f"Mappe ces colonnes Excel : {df_columns} vers {target_columns}. Réponds UNIQUEMENT en JSON."
    try:
        response = model_ai.generate_content(prompt)
        txt = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(txt)
    except: return {}

# 3. INTERFACE D'IMPORTATION
st.header("💰 Pipeline des Ventes")

f = st.file_uploader("Charger le fichier Excel", type=["xlsx", "xlsb"])
if f:
    xl = pd.ExcelFile(f)
    onglet = st.selectbox("Choisir l'onglet", xl.sheet_names)
    df_raw = xl.parse(onglet)
    
    targets = ["Physical Month", "Status Planif", "D1", "D2", "D3"]
    
    with st.expander("🤖 IA : Mapping automatique", expanded=True):
        mapping = get_smart_mapping(list(df_raw.columns), targets)
        final_map = st.data_editor(mapping, use_container_width=True)
        
        if st.button("Valider et Générer les Cartes"):
            df_v = df_raw.rename(columns=final_map)
            # Nettoyage des colonnes numériques
            for d in ["D1", "D2", "D3"]:
                if d in df_v.columns: 
                    df_v[d] = df_v[d].apply(force_n)
            st.session_state["ventes_df"] = df_v
            st.rerun()

# 4. AFFICHAGE DES RÉSULTATS (PROTECTION CONTRE L'ERREUR)
if st.session_state["ventes_df"] is not None:
    df = st.session_state["ventes_df"]
    
    # Filtre Mois
    if "Physical Month" in df.columns:
        mois_sel = st.selectbox("Sélectionner le Mois", df["Physical Month"].dropna().unique())
        df_m = df[df["Physical Month"] == mois_sel]
    else:
        df_m = df
        mois_sel = "Tout"

    # --- SECTION DES CARTES (CARDS) ---
    st.markdown(f"### 📊 Situation — {mois_sel}")
    c1, c2, c3 = st.columns(3)
    
    # Configuration des statuts (1=En cours, 2=Rade, 0/3=Nommé)
    confs = [
        (c1, "🚢 En cours", "#00843D", "1.|en cours"),
        (c2, "⚓ En Rade", "#6B3FA0", "2.|rade"),
        (c3, "📦 Nommé", "#1565C0", "0.|3.|nomme|charge")
    ]

    for col, title, color, pattern in confs:
        if "Status Planif" in df_m.columns:
            mask = df_m["Status Planif"].astype(str).str.lower().str.contains(pattern, na=False)
            sub = df_m[mask]
            
            d1_sum = sub["D1"].sum() if "D1" in sub.columns else 0
            d2_sum = sub["D2"].sum() if "D2" in sub.columns else 0
            d3_sum = sub["D3"].sum() if "D3" in sub.columns else 0
            total = d1_sum + d2_sum + d3_sum
            
            with col:
                st.markdown(f"""
                <div style="background:white; border-radius:10px; padding:15px; border-top:5px solid {color}; box-shadow:0 2px 4px rgba(0,0,0,0.05); margin-bottom:20px;">
                    <div style="font-weight:700; color:{color}; font-size:14px;">{title}</div>
                    <div style="display:flex; justify-content:space-between; margin-top:10px; border-bottom:1px solid #EEE; padding-bottom:8px;">
                        <div style="text-align:center;"><div style="font-size:10px;color:gray;">D1</div><b style="font-size:14px;">{fmt(d1_sum)}</b></div>
                        <div style="text-align:center;"><div style="font-size:10px;color:gray;">D2</div><b style="font-size:14px;">{fmt(d2_sum)}</b></div>
                        <div style="text-align:center;"><div style="font-size:10px;color:gray;">D3</div><b style="font-size:14px;">{fmt(d3_sum)}</b></div>
                    </div>
                    <div style="text-align:right; font-weight:800; color:{color}; margin-top:8px; font-size:18px;">
                        {fmt(total)} <span style="font-size:10px;">KT</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # --- TABLE DE DÉTAIL ---
    st.markdown("### 📋 TABLE DE DÉTAIL")
    # Liste des colonnes à afficher (incluant Status Planif)
    cols_disp = [c for c in ["Physical Month", "D1", "D2", "D3", "Status Planif"] if c in df_m.columns]
    st.dataframe(df_m[cols_disp], use_container_width=True, hide_index=True)
