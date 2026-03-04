import streamlit as st
import pandas as pd
import re
import time
import os
import io
from docx import Document

# 1. Configuration de la page
st.set_page_config(page_title="OCP - Le Chargement", layout="wide", page_icon="🚢")

# --- DESIGN OCP (VERT ET BLANC) ---
st.markdown("""
    <style>
        :root { --ocp-green: #00843D; }
        .stApp { background-color: #FFFFFF; }
        h1, h2, h3 { color: var(--ocp-green) !important; }
        .stButton>button { background-color: var(--ocp-green); color: white; border-radius: 8px; width: 100%; }
        .stTable { border: 1px solid var(--ocp-green); }
        [data-testid="stSidebar"] { border-right: 3px solid var(--ocp-green); }
    </style>
""", unsafe_allow_html=True)

def force_nombre(valeur):
    """Logique de calcul validée avec protection contre les nombres géants"""
    if pd.isna(valeur): return 0.0
    if isinstance(valeur, (int, float)): 
        # Protection contre la notation scientifique invisible (ex: 1e-17)
        if abs(valeur) < 1e-6: return 0.0
        return float(valeur)
    s = str(valeur).strip()
    if s in ("-", "", "nan"): return 0.0
    # Nettoyage : on garde uniquement les chiffres
    nettoye = re.sub(r'[^\d]', '', s.replace("\xa0", "").replace(" ", ""))
    # Si le nombre est absurdement long, c'est une erreur de lecture
    if len(nettoye) > 12: return 0.0
    try:
        return float(nettoye)
    except ValueError:
        return 0.0

def generate_word(df_result, date_selection):
    """Génère un fichier Word avec les valeurs copiables"""
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
            # Formatage propre pour le copier-coller
            row_cells[i].text = f"{val:,.0f}".replace(',', ' ') if isinstance(val, (int, float)) else str(val)
    
    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()

# --- HEADER ---
col_logo, col_title = st.columns([1, 4])
with col_logo:
    if os.path.exists("logo_ocp.png"):
        st.image("logo_ocp.png", width=120)
    elif os.path.exists("logo_ocp"):
        st.image("logo_ocp", width=120)
    else:
        st.write("🟢 **OCP GROUP**")

with col_title:
    st.title("Système de Suivi du Chargement")
    st.markdown("##### Analyse de l'Atterrissage • Reporting JPH 2026")

st.divider()

file = st.file_uploader("📂 Charger le fichier Reporting-JPH 2026", type=["xlsx"])

if file:
    with st.status("🚀 Traitement des flux OCP en cours...", expanded=False) as status:
        try:
            # Chargement de l'onglet EXPORT
            df = pd.read_excel(file, sheet_name='EXPORT', header=None)
            
            # SCANNER DE LIGNES (On cherche dans les premières colonnes)
            coords = {"ENGRAIS": None, "CAMIONS": None, "VL": None}
            for r in range(len(df)):
                # On concatène les 3 premières colonnes pour chercher le texte
                ligne_label = " ".join(df.iloc[r, 0:3].astype(str)).upper()
                if "EXPORT ENGRAIS" in ligne_label: coords["ENGRAIS"] = r
                if "EXPORT CAMIONS" in ligne_label: coords["CAMIONS"] = r
                if "VL CAMIONS" in ligne_label:     coords["VL"] = r
            
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
                    "Export Engrais": v1, "Export Camions": v2,
                    "VL Camions": v3, "TOTAL": v1 + v2 + v3
                })

            status.update(label="✅ Analyse terminée !", state="complete")

            if final_list:
                res_df = pd.DataFrame(final_list)
                st.sidebar.header("🔍 Filtrage")
                choix = st.sidebar.selectbox("Période", ["Toutes"] + list(res_df["Date"]))
                show_df = res_df if choix == "Toutes" else res_df[res_df["Date"] == choix]

                st.subheader(f"📊 Résultats : {choix}")
                st.table(show_df.style.format(precision=0, thousands=" "))
                
                # --- NOUVELLE FONCTION : COPIER / EXPORTER ---
                st.divider()
                st.markdown("### 📥 Récupérer les valeurs (Copier/Coller)")
                c1, c2 = st.columns(2)
                with c1:
                    # Bouton Excel/CSV
                    st.download_button(
                        label="Excel (CSV)",
                        data=show_df.to_csv(index=False).encode('utf-8'),
                        file_name=f"Donnees_OCP_{choix}.csv",
                        mime="text/csv"
                    )
                with c2:
                    # Bouton Word
                    st.download_button(
                        label="Fichier WORD",
                        data=generate_word(show_df, choix),
                        file_name=f"Rapport_OCP_{choix}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )

                if choix == "Toutes" and len(res_df) > 1:
                    st.line_chart(res_df.set_index("Date")["TOTAL"], color="#00843D")
            else:
                st.error("Structure du fichier non reconnue.")

        except Exception as e:
            st.error(f"Erreur technique : {e}")
else:
    st.info("Veuillez importer le fichier Excel.")


