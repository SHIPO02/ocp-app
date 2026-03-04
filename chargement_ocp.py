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
    """Nettoyage des données pour éviter les nombres géants."""
    if pd.isna(valeur): return 0.0
    if isinstance(valeur, (int, float)):
        if abs(valeur) < 1e-6: return 0.0
        return float(valeur)
    s = str(valeur).strip()
    if s in ("-", "", "nan"): return 0.0
    nettoye = re.sub(r'[^\d]', '', s)
    if len(nettoye) > 10: return 0.0
    return float(nettoye) if nettoye else 0.0

def generate_word(df_result, date_selection):
    """Génère un fichier Word propre pour l'encadrant."""
    doc = Document()
    doc.add_heading(f"Rapport de Chargement OCP", 0)
    doc.add_paragraph(f"Période : {date_selection}")
    doc.add_paragraph(f"Généré le : {time.strftime('%d/%m/%Y à %H:%M')}")
    
    table = doc.add_table(rows=1, cols=len(df_result.columns))
    table.style = 'Table Grid'
    hdr_cells = table.rows[0].cells
    for i, col in enumerate(df_result.columns):
        hdr_cells[i].text = col

    for _, row in df_result.iterrows():
        row_cells = table.add_row().cells
        for i, val in enumerate(row):
            row_cells[i].text = str(int(val)) if isinstance(val, float) else str(val)
    
    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()

# --- HEADER ---
col_logo, col_title = st.columns([1, 4])
with col_logo:
    if os.path.exists("logo_ocp.png"):
        st.image("logo_ocp.png", width=120)
    else:
        st.write("🟢 **OCP GROUP**")

with col_title:
    st.title("Système de Suivi du Chargement")
    st.markdown("##### Reporting JPH 2026 - Atterrissage Automatisé")

st.divider()

file = st.file_uploader("📂 Charger le fichier Reporting-JPH (Excel)", type=["xlsx"])

if file:
    with st.status("🚀 Analyse des données...", expanded=False) as status:
        try:
            df = pd.read_excel(file, sheet_name='EXPORT', header=None)
            coords = {"ENGRAIS": None, "CAMIONS": None, "VL": None}
            for r in range(len(df)):
                lib = str(df.iloc[r, 1]).upper().strip()
                if "EXPORT ENGRAIS" == lib: coords["ENGRAIS"] = r
                elif "EXPORT CAMIONS" == lib: coords["CAMIONS"] = r
                elif "VL CAMIONS" == lib: coords["VL"] = r
            
            ligne_dates = df.iloc[2, :]
            cols_data = [j for j in range(3, len(ligne_dates)) if pd.notna(ligne_dates[j])]

            final_list = []
            for j in cols_data:
                dt = ligne_dates[j]
                date_label = dt.strftime('%d/%m/%Y') if hasattr(dt, 'strftime') else str(dt).split(" ")[0]
                v1 = force_nombre(df.iloc[coords["ENGRAIS"], j]) if coords["ENGRAIS"] is not None else 0.0
                v2 = force_nombre(df.iloc[coords["CAMIONS"], j]) if coords["CAMIONS"] is not None else 0.0
                v3 = force_nombre(df.iloc[coords["VL"], j]) if coords["VL"] is not None else 0.0
                final_list.append({"Date": date_label, "Export Engrais": v1, "Export Camions": v2, "VL Camions": v3, "TOTAL": v1+v2+v3})

            if final_list:
                res_df = pd.DataFrame(final_list)
                st.sidebar.header("🔍 Options")
                choix = st.sidebar.selectbox("Filtrer par Date", ["Toutes"] + list(res_df["Date"]))
                show_df = res_df if choix == "Toutes" else res_df[res_df["Date"] == choix]

                st.subheader(f"📊 Résultats : {choix}")
                st.table(show_df.style.format(precision=0, thousands=" "))

                # --- ZONE D'EXPORTATION ---
                st.divider()
                st.markdown("### 📥 Transférer les résultats")
                c1, c2 = st.columns(2)
                
                with c1:
                    st.download_button(
                        label="Excel / CSV",
                        data=show_df.to_csv(index=False).encode('utf-8'),
                        file_name=f"OCP_Export_{choix}.csv",
                        mime="text/csv"
                    )
                with c2:
                    st.download_button(
                        label="Fichier WORD",
                        data=generate_word(show_df, choix),
                        file_name=f"Rapport_OCP_{choix}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
                
                status.update(label="✅ Traitement terminé", state="complete")
        except Exception as e:
            st.error(f"Erreur : {e}")
