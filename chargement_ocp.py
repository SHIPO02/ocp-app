import streamlit as st
import pandas as pd
import json
import google.generativeai as genai

# --- CONFIGURATION ---
st.set_page_config(page_title="OCP Pipeline", layout="wide")

if "ventes_df" not in st.session_state:
    st.session_state["ventes_df"] = None

# Configuration IA (Remplace par ta clé si nécessaire)
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model_ai = genai.GenerativeModel('gemini-1.5-flash')
except:
    st.error("Clé API non trouvée.")

# --- UTILS ---
def fmt(n): return f"{n:,.1f}".replace(",", " ")
def force_n(v):
    if pd.isna(v): return 0.
    try: return float(str(v).replace(" ", "").replace(",", "."))
    except: return 0.

def get_smart_mapping(df_columns, target_columns):
    prompt = f"Mappe ces colonnes Excel : {df_columns} vers ces cibles : {target_columns}. Réponds UNIQUEMENT en JSON."
    try:
        response = model_ai.generate_content(prompt)
        txt = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(txt)
    except: return {}

# --- PAGE PIPELINE VENTES ---
st.header("💰 Pipeline des Ventes")

f = st.file_uploader("Charger le fichier Excel", type=["xlsx", "xlsb"])
if f:
    xl = pd.ExcelFile(f)
    onglet = st.selectbox("Choisir l'onglet", xl.sheet_names)
    df_raw = xl.parse(onglet)
    
    # On demande à l'IA de trouver ces 5 colonnes précises
    targets = ["Physical Month", "Status Planif", "D1", "D2", "D3"]
    
    with st.expander("🤖 IA : Mapping automatique", expanded=True):
        mapping = get_smart_mapping(list(df_raw.columns), targets)
        final_map = st.data_editor(mapping, use_container_width=True)
        
        if st.button("Valider et Générer les Cartes"):
            df_v = df_raw.rename(columns=final_map)
            # Nettoyage des nombres
            for d in ["D1", "D2", "D3"]:
                if d in df_v.columns: df_v[d] = df_v[d].apply(force_n)
            st.session_state["ventes_df"] = df_v
            st.rerun()

# --- AFFICHAGE DES RÉSULTATS ---
if st.session_state.ventes_df is not None:
    df = st.session_state.ventes_df
    
    # 1. Filtre Mois
    if "Physical Month" in df.columns:
        mois_sel = st.selectbox("Mois", df["Physical Month"].dropna().unique())
        df_m = df[df["Physical Month"] == mois_sel]
    else:
        df_m = df
        mois_sel = "Toutes périodes"

    # 2. GÉNÉRATION DES CARDS (Design OCP)
    st.subheader(f"Situation — {mois_sel}")
    c1, c2, c3 = st.columns(3)
    
    # On définit les règles pour les 3 statuts (1=En cours, 2=Rade, 0/3=Nommé)
    confs = [
        (c1, "🚢 En cours", "#00843D", "1."),
        (c2, "⚓ En Rade", "#6B3FA0", "2."),
        (c3, "📦 Nommé", "#1565C0", "0.|3.|nomme")
    ]

    for col, title, color, pattern in confs:
        if "Status Planif" in df_m.columns:
            # Filtrage intelligent sur le texte du statut
            mask = df_m["Status Planif"].astype(str).str.lower().str.contains(pattern, na=False)
            sub = df_m[mask]
            
            # Sommes D1, D2, D3
            d1, d2, d3 = sub["D1"].sum(), sub["D2"].sum(), sub["D3"].sum()
            total = d1 + d2 + d3
            
            with col:
                st.markdown(f"""
                <div style="background:white; border-radius:10px; padding:15px; border-top:5px solid {color}; box-shadow:0 2px 4px rgba(0,0,0,0.05)">
                    <div style="font-weight:700; color:{color};">{title}</div>
                    <div style="display:flex; justify-content:space-between; margin-top:10px; border-bottom:1px solid #EEE; padding-bottom:8px;">
                        <div style="text-align:center;"><div style="font-size:10px;color:gray;">D1</div><b>{fmt(d1)}</b></div>
                        <div style="text-align:center;"><div style="font-size:10px;color:gray;">D2</div><b>{fmt(d2)}</b></div>
                        <div style="text-align:center;"><div style="font-size:10px;color:gray;">D3</div><b>{fmt(d3)}</b></div>
                    </div>
                    <div style="text-align:right; font-weight:800; color:{color}; margin-top:8px; font-size:18px;">
                        {fmt(total)} <span style="font-size:10px;">KT</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # 3. TABLE DE DÉTAIL (Avec la colonne Statut ajoutée)
    st.markdown("### 📋 TABLE DE DÉTAIL")
    cols_a_afficher = [c for c in ["Physical Month", "D1", "D2", "D3", "Status Planif"] if c in df_m.columns]
    st.dataframe(df_m[cols_a_afficher], use_container_width=True, hide_index=True)
