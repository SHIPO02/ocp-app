import streamlit as st
import pandas as pd
import re
import time
import os
import io
from docx import Document

# --- CONFIGURATION ET DESIGN ---
st.set_page_config(page_title="OCP - Le Chargement", layout="wide", page_icon="🚢")

st.markdown("""
    <style>
        :root { --ocp-green: #00843D; }
        .stApp { background-color: #FFFFFF; }
        h1, h2, h3 { color: var(--ocp-green) !important; }
        .stButton>button { background-color: var(--ocp-green); color: white; border-radius: 8px; width: 100%; }
        .stTable { border: 1px solid var(--ocp-green); }
    </style>
""", unsafe_allow_html=True)

def force_nombre(valeur):
    if pd.isna(valeur): return 0.0
    if isinstance(valeur, (int, float)):
        if abs(valeur) < 1e-6: return 0.0
        return float(valeur)
    s = str(valeur).strip()
    if s in ("-", "", "nan"): return 0.0
    # Nettoyage pour garder uniquement les chiffres (ex: 12,104. -> 12104)
    nettoye = re.sub(r'[^\d]', '', s)
    if len(nettoye) > 12: return 0.0
    return float(nettoye) if nettoye else 0.0

def generate_word(df_result, date_selection):
    doc = Document()
    doc.add_heading(f"Rapport de Chargement OCP", 0)
    doc.add_paragraph(f"Période : {date_selection}")
    table = doc.add_table(rows=1, cols=len(df_result.columns))
    table.style = 'Table Grid'
    hdr_cells = table.rows[0].cells
    for i, col in enumerate(df_result.columns):
        hdr_cells[i].text = col
    for _, row in df_result.iterrows():
        row_cells = table.add_row().cells
        for i, val in enumerate(row):
            row_cells[i].text = f"{val:,.0f}".replace(',', ' ') if isinstance(val, (int, float)) else str(val)
    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()

# --- HEADER ---
col_logo, col_title = st.columns([1, 4])
with col_logo:
    # Test plusieurs extensions pour le logo
    logo_found = False
    for ext in [".png", ".jpg", ".jpeg", ""]:
        if os.path.exists(f"logo_ocp{ext}"):
            st.image(f"logo_ocp{ext}", width=120)
            logo_found = True
            break
    if not logo_found: st.write("🟢 **OCP GROUP**")

with col_title:
    st.title("Système de Suivi du Chargement")
    st.markdown("##### Analyse Automatisée • Reporting JPH 2026")

st.divider()

file = st.file_uploader("📂 Charger le fichier Reporting-JPH (Excel)", type=["xlsx"])

if file:
    with st.status("🚀 Analyse des données...", expanded=False) as status:
        try:
            # On lit tout l'onglet 'EXPORT'
            df = pd.read_excel(file, sheet_name='EXPORT', header=None)
            
            # --- SCANNER DE LIGNES AMÉLIORÉ ---
            # On cherche partout dans le fichier pour trouver les lignes
            coords = {"ENGRAIS": None, "CAMIONS": None, "VL": None}
            for r in range(len(df)):
                # On scanne les premières colonnes (A, B, C) pour trouver les mots-clés
                row_values = " ".join(df.iloc[r, 0:5].astype(str).upper())
                if "EXPORT ENGRAIS" in row_values: coords["ENGRAIS"] = r
                if "EXPORT CAMIONS" in row_values: coords["CAMIONS"] = r
                if "VL CAMIONS" in row_values: coords["VL"] = r
            
            # --- DETECTION DES DATES (Ligne 3) ---
            ligne_dates = df.iloc[2, :]
            # Les données commencent généralement à la colonne 4 (Index 3)
            cols_data = [j for j in range(3, len(ligne_dates)) if pd.notna(ligne_dates[j])]

            final_list = []
            if coords["ENGRAIS"] is not None:
                for j in cols_data:
                    dt = ligne_dates[j]
                    date_label = dt.strftime('%d/%m/%Y') if hasattr(dt, 'strftime') else str(dt).split(" ")[0]
                    
                    v1 = force_nombre(df.iloc[coords["ENGRAIS"], j])
                    v2 = force_nombre(df.iloc[coords["CAMIONS"], j]) if coords["CAMIONS"] is not None else 0.0
                    v3 = force_nombre(df.iloc[coords["VL"], j]) if coords["VL"] is not None else 0.0
                    
                    # On n'ajoute que si au moins une valeur est > 0 pour éviter les lignes vides
                    if v1 > 0 or v2 > 0 or v3 > 0:
                        final_list.append({
                            "Date": date_label, 
                            "Export Engrais": v1, 
                            "Export Camions": v2, 
                            "VL Camions": v3, 
                            "TOTAL": v1+v2+v3
                        })

            if final_list:
                res_df = pd.DataFrame(final_list)
                st.sidebar.header("🔍 Options")
                choix = st.sidebar.selectbox("Filtrer par Date", ["Toutes"] + list(res_df["Date"]))
                show_df = res_df if choix == "Toutes" else res_df[res_df["Date"] == choix]

                st.subheader(f"📊 Résultats : {choix}")
                st.table(show_df.style.format(precision=0, thousands=" "))

                st.divider()
                st.markdown("### 📥 Transférer les résultats")
                c1, c2 = st.columns(2)
                with c1:
                    st.download_button(label="Excel / CSV", data=show

