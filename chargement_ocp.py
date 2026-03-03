import streamlit as st
import pandas as pd
import re
import time
import os
import segno
from io import BytesIO

# --- CONFIGURATION ---
st.set_page_config(page_title="OCP - Le Chargement", layout="wide", page_icon="🚢")

st.markdown("""
    <style>
        :root { --ocp-green: #00843D; }
        .stApp { background-color: #FFFFFF; }
        h1, h2, h3 { color: var(--ocp-green) !important; }
        .stButton>button { background-color: var(--ocp-green); color: white; border-radius: 8px; }
    </style>
""", unsafe_allow_html=True)

def force_nombre(valeur):
    if pd.isna(valeur): return 0.0
    if isinstance(valeur, (int, float)):
        if abs(valeur) < 1e-6: return 0.0
        return float(valeur)
    s = str(valeur).strip()
    if s in ("-", "", "nan"): return 0.0
    nettoye = re.sub(r'[^\d]', '', s)
    if len(nettoye) > 10: return 0.0
    return float(nettoye) if nettoye else 0.0

# --- HEADER ---
col_logo, col_title = st.columns([1, 4])
with col_logo:
    if os.path.exists("logo_ocp.png"):
        st.image("logo_ocp.png", width=120)
    else:
        st.write("🟢 **OCP GROUP**")

with col_title:
    st.title("Système de Suivi du Chargement")
    st.markdown("##### Analyse de l'Atterrissage • Reporting JPH 2026")

st.divider()

file = st.file_uploader("📂 Charger le fichier Reporting-JPH 2026", type=["xlsx"])

if file:
    with st.status("🚀 Analyse OCP en cours...", expanded=False) as status:
        try:
            df = pd.read_excel(file, sheet_name='EXPORT', header=None)
            coords = {"ENGRAIS": None, "CAMIONS": None, "VL": None}
            for r in range(len(df)):
                libelle = str(df.iloc[r, 1]).upper().strip()
                if "EXPORT ENGRAIS" == libelle: coords["ENGRAIS"] = r
                elif "EXPORT CAMIONS" == libelle: coords["CAMIONS"] = r
                elif "VL CAMIONS" == libelle: coords["VL"] = r
            
            ligne_dates = df.iloc[2, :]
            cols_data = [j for j in range(3, len(ligne_dates)) if pd.notna(ligne_dates[j])]

            final_list = []
            for j in cols_data:
                dt = ligne_dates[j]
                date_label = dt.strftime('%d/%m/%Y') if hasattr(dt, 'strftime') else str(dt).split(" ")[0]
                v1 = force_nombre(df.iloc[coords["ENGRAIS"], j]) if coords["ENGRAIS"] is not None else 0.0
                v2 = force_nombre(df.iloc[coords["CAMIONS"], j]) if coords["CAMIONS"] is not None else 0.0
                v3 = force_nombre(df.iloc[coords["VL"], j])      if coords["VL"] is not None else 0.0
                final_list.append({"Date": date_label, "Export Engrais": v1, "Export Camions": v2, "VL Camions": v3, "TOTAL": v1+v2+v3})

            if final_list:
                res_df = pd.DataFrame(final_list)
                st.subheader("📊 Résultats")
                st.table(res_df.style.format(precision=0, thousands=" "))
                
                # --- SECTION CODE QR ---
                st.divider()
                st.markdown("### 📱 Scanner pour accéder à l'App")
                
                # Génération du QR Code pointant vers votre URL
                url_app = "https://chargement.streamlit.app"
                qr = segno.make_qr(url_app)
                
                # Sauvegarde en mémoire avec couleur OCP
                buffer = BytesIO()
                qr.save(buffer, kind='png', scale=5, dark="#00843D")
                
                col_qr, col_text = st.columns([1, 3])
                with col_qr:
                    st.image(buffer.getvalue())
                with col_text:
                    st.write(f"Partagez ce code avec vos collègues pour qu'ils puissent utiliser l'outil directement sur mobile.")
                    st.code(url_app)

        except Exception as e:
            st.error(f"Erreur : {e}")
