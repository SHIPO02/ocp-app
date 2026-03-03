import streamlit as st
import pandas as pd
import re
import time
import os

# 1. Configuration de la page
st.set_page_config(page_title="OCP - Le Chargement", layout="wide", page_icon="🚢")

# --- DESIGN OCP (VERT ET BLANC) ---
st.markdown("""
    <style>
        :root { --ocp-green: #00843D; }
        .stApp { background-color: #FFFFFF; }
        h1, h2, h3 { color: var(--ocp-green) !important; }
        .stButton>button { background-color: var(--ocp-green); color: white; border-radius: 8px; }
        .stTable { border: 1px solid var(--ocp-green); }
        /* Style pour le bandeau latéral */
        [data-testid="stSidebar"] { border-right: 3px solid var(--ocp-green); }
    </style>
""", unsafe_allow_html=True)

def force_nombre(valeur):
    """Logique de calcul validée"""
    if pd.isna(valeur): return 0.0
    if isinstance(valeur, (int, float)): return float(valeur)
    s = str(valeur).strip()
    if s in ("-", "", "nan"): return 0.0
    s = s.replace("\xa0", "").replace(" ", "")
    if "," in s: s = s.replace(",", "").rstrip(".")
    try:
        return float(s)
    except ValueError:
        return 0.0

# --- HEADER AVEC LOGO LOCAL ---
col_logo, col_title = st.columns([1, 4])
with col_logo:
    # On cherche le fichier 'logo_ocp' avec ses extensions possibles
    logo_path = "logo_ocp.png" # ou .jpg, .jpeg selon votre fichier
    if os.path.exists("logo_ocp.png"):
        st.image("logo_ocp.png", width=120)
    elif os.path.exists("logo_ocp"):
        st.image("logo_ocp", width=120)
    else:
        # Fallback si le fichier n'est pas trouvé
        st.warning("Logo non trouvé")

with col_title:
    st.title("Système de Suivi du Chargement")
    st.markdown("##### Analyse de l'Atterrissage • Reporting JPH 2026")

st.divider()

# --- INTERFACE DE CHARGEMENT ---
file = st.file_uploader("📂 Charger le fichier Reporting-JPH 2026", type=["xlsx"])

if file:
    # Motif de chargement (Animation OCP)
    with st.status("🚀 Traitement des flux OCP en cours...", expanded=True) as status:
        st.write("Lecture de l'onglet EXPORT...")
        time.sleep(0.5)
        
        try:
            df = pd.read_excel(file, sheet_name='EXPORT', header=None)
            
            st.write("Identification des lignes (Engrais, Camions, VL)...")
            coords = {"ENGRAIS": None, "CAMIONS": None, "VL": None}
            for r in range(len(df)):
                for c in range(len(df.columns)):
                    cell = str(df.iloc[r, c]).upper().strip()
                    if "EXPORT ENGRAIS" in cell: coords["ENGRAIS"] = r
                    if "EXPORT CAMIONS" in cell: coords["CAMIONS"] = r
                    if "VL CAMIONS" in cell:     coords["VL"] = r
            
            st.write("Extraction des données chronologiques...")
            ligne_dates = df.iloc[2, :]
            cols_data = [j for j in range(3, len(ligne_dates)) if pd.notna(ligne_dates[j])]

            final_list = []
            for j in cols_data:
                dt = ligne_dates[j]
                date_label = dt.strftime('%d/%m/%Y') if hasattr(dt, 'strftime') else str(dt).split(" ")[0]

                v1 = force_nombre(df.iloc[coords["ENGRAIS"], j]) if coords["ENGRAIS"] is not None else 0.0
                v2 = force_nombre(df.iloc[coords["CAMIONS"], j]) if coords["CAMIONS"] is not None else 0.0
                v3 = force_nombre(df.iloc[coords["VL"], j])      if coords["VL"] is not None else 0.0

                final_list.append({
                    "Date": date_label,
                    "Export Engrais": v1,
                    "Export Camions": v2,
                    "VL Camions": v3,
                    "TOTAL": v1 + v2 + v3
                })

            status.update(label="✅ Chargement OCP terminé !", state="complete", expanded=False)

            if final_list:
                res_df = pd.DataFrame(final_list)
                
                # --- AFFICHAGE ---
                st.sidebar.header("🔍 Filtrage")
                choix = st.sidebar.selectbox("Période", ["Toutes"] + list(res_df["Date"]))

                show_df = res_df if choix == "Toutes" else res_df[res_df["Date"] == choix]

                st.subheader(f"📊 Résultats : {choix}")
                
                # Tableau formaté style OCP
                st.table(show_df.style.format(precision=0, thousands=" "))
                
                # Graphique en vert OCP
                if choix == "Toutes" and len(res_df) > 1:
                    st.line_chart(res_df.set_index("Date")["TOTAL"], color="#00843D")
            else:
                st.error("Aucune donnée trouvée.")

        except Exception as e:
            st.error(f"Erreur : {e}")
else:
    st.info("Veuillez importer le fichier Excel pour débuter l'analyse.")
