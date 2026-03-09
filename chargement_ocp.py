import streamlit as st
import pandas as pd
import re
import os
import io
from docx import Document

st.set_page_config(page_title="OCP - Suivi Production MFS", layout="wide", page_icon="🚢")

st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Barlow:wght@400;600;700&family=Barlow+Condensed:wght@600;700&display=swap');

        :root {
            --ocp-green: #00843D;
            --ocp-dark:  #005C2A;
            --ocp-light: #E8F5EE;
            --jerf-color: #00843D;
            --safi-color: #1A6FA8;
            --total-color: #C05A00;
        }

        html, body, [class*="css"] { font-family: 'Barlow', sans-serif; }
        .stApp { background-color: #F4F7F5; }
        h1, h2, h3 { color: var(--ocp-dark) !important; font-family: 'Barlow Condensed', sans-serif !important; }

        /* KPI Cards */
        .kpi-card {
            border-radius: 12px;
            padding: 20px 24px;
            color: white;
            box-shadow: 0 4px 16px rgba(0,0,0,0.12);
            position: relative;
            overflow: hidden;
        }
        .kpi-card::before {
            content: '';
            position: absolute;
            top: -20px; right: -20px;
            width: 100px; height: 100px;
            border-radius: 50%;
            background: rgba(255,255,255,0.1);
        }
        .kpi-card.jerf  { background: linear-gradient(135deg, #00843D, #005C2A); }
        .kpi-card.safi  { background: linear-gradient(135deg, #1A6FA8, #0D4A73); }
        .kpi-card.total { background: linear-gradient(135deg, #C05A00, #8A3F00); }
        .kpi-label { font-size: 12px; font-weight: 600; opacity: 0.85; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 6px; }
        .kpi-value { font-family: 'Barlow Condensed', sans-serif; font-size: 38px; font-weight: 700; line-height: 1; }
        .kpi-sub   { font-size: 11px; opacity: 0.7; margin-top: 4px; }

        /* Section headers */
        .section-header {
            display: flex; align-items: center; gap: 10px;
            padding: 10px 16px; border-radius: 8px;
            margin: 20px 0 10px 0;
            font-family: 'Barlow Condensed', sans-serif;
            font-size: 20px; font-weight: 700; color: white;
        }
        .section-header.jerf  { background: var(--jerf-color); }
        .section-header.safi  { background: var(--safi-color); }
        .section-header.total { background: var(--total-color); }

        /* Buttons */
        .stDownloadButton>button {
            background-color: var(--ocp-green) !important;
            color: white !important;
            border-radius: 8px !important;
            border: none !important;
            font-family: 'Barlow', sans-serif !important;
            font-weight: 600 !important;
        }
        [data-testid="stSidebar"] {
            border-right: 3px solid var(--ocp-green);
            background: #FAFFF9;
        }
        hr { border-color: #D0E8D9 !important; }
    </style>
""", unsafe_allow_html=True)

# ─── HELPERS ────────────────────────────────────────────────────────────────

def force_nombre(valeur):
    if pd.isna(valeur): return 0.0
    if isinstance(valeur, (int, float)):
        if abs(valeur) < 1e-6: return 0.0
        return float(valeur)
    s = str(valeur).strip()
    if s in ("-", "", "nan"): return 0.0
    nettoye = re.sub(r'[^\d]', '', s.replace("\xa0", "").replace(" ", ""))
    if len(nettoye) > 12: return 0.0
    try:
        return float(nettoye)
    except ValueError:
        return 0.0

def fmt_number(n):
    return f"{int(n):,}".replace(",", " ")

def generate_word(df_result, titre, periode):
    doc = Document()
    doc.add_heading(titre, 0)
    doc.add_paragraph(f"Période : {periode}")
    table = doc.add_table(rows=1, cols=len(df_result.columns))
    table.style = 'Table Grid'
    for i, col in enumerate(df_result.columns):
        table.rows[0].cells[i].text = col
    for _, row in df_result.iterrows():
        cells = table.add_row().cells
        for i, val in enumerate(row):
            cells[i].text = fmt_number(val) if isinstance(val, (int, float)) else str(val)
    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()

def export_buttons(df, prefix, titre, periode):
    c1, c2 = st.columns(2)
    with c1:
        st.download_button(
            f"⬇️ CSV — {prefix}",
            df.to_csv(index=False).encode('utf-8'),
            file_name=f"{prefix}_{periode}.csv",
            mime="text/csv"
        )
    with c2:
        st.download_button(
            f"⬇️ Word — {prefix}",
            generate_word(df, titre, periode),
            file_name=f"{prefix}_{periode}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

def extract_mois(date_str):
    try:
        parts = str(date_str).split("/")
        if len(parts) == 3:
            m = int(parts[1]); y = parts[2]
            noms = {1:"Jan",2:"Fév",3:"Mar",4:"Avr",5:"Mai",6:"Jun",
                    7:"Jul",8:"Aoû",9:"Sep",10:"Oct",11:"Nov",12:"Déc"}
            return f"{noms.get(m,'?')} {y}"
    except:
        pass
    return "Inconnu"

# ─── HEADER ──────────────────────────────────────────────────────────────────
col_logo, col_title = st.columns([1, 5])
with col_logo:
    if os.path.exists("logo_ocp.png"):
        st.image("logo_ocp.png", width=110)
    else:
        st.markdown("<div style='font-size:34px;font-weight:900;color:#00843D;font-family:Barlow Condensed,sans-serif;'>OCP</div>", unsafe_allow_html=True)
with col_title:
    st.title("Suivi de la Production MFS")
    st.markdown("##### Reporting Consolidé — Jerf Lasfar & Safi • JPH 2026")

st.divider()

# ─── SIDEBAR ─────────────────────────────────────────────────────────────────
st.sidebar.header("📂 Chargement des fichiers")
file_jerf = st.sidebar.file_uploader("🏭 Fichier Jerf (Reporting-JPH 2026)", type=["xlsx"], key="jerf")
file_safi = st.sidebar.file_uploader("🏗️ Fichier Safi (Suivi Production MFS)", type=["xlsx"], key="safi")

# ─── PARSE JERF ──────────────────────────────────────────────────────────────
jerf_df = None
if file_jerf:
    try:
        df_raw = pd.read_excel(file_jerf, sheet_name='EXPORT', header=None)
        coords = {"ENGRAIS": None, "CAMIONS": None, "VL": None}
        for r in range(len(df_raw)):
            lbl = " ".join(df_raw.iloc[r, 0:3].astype(str)).upper()
            if "EXPORT ENGRAIS" in lbl: coords["ENGRAIS"] = r
            if "EXPORT CAMIONS" in lbl: coords["CAMIONS"] = r
            if "VL CAMIONS"     in lbl: coords["VL"] = r

        ligne_dates = df_raw.iloc[2, :]
        cols_data = [j for j in range(3, len(ligne_dates)) if pd.notna(ligne_dates[j])]
        rows = []
        for j in cols_data:
            dt = ligne_dates[j]
            dl = dt.strftime('%d/%m/%Y') if hasattr(dt, 'strftime') else str(dt).split(" ")[0]
            v1 = force_nombre(df_raw.iloc[coords["ENGRAIS"], j]) if coords["ENGRAIS"] is not None else 0.0
            v2 = force_nombre(df_raw.iloc[coords["CAMIONS"], j]) if coords["CAMIONS"] is not None else 0.0
            v3 = force_nombre(df_raw.iloc[coords["VL"], j])      if coords["VL"] is not None else 0.0
            rows.append({"Date": dl, "Export Engrais": v1, "Export Camions": v2,
                         "VL Camions": v3, "TOTAL Jerf": v1 + v2 + v3})
        jerf_df = pd.DataFrame(rows)
    except Exception as e:
        st.sidebar.error(f"Erreur Jerf : {e}")

# ─── PARSE SAFI ──────────────────────────────────────────────────────────────
safi_df = None
if file_safi:
    try:
        xl = pd.ExcelFile(file_safi)
        COL_TSP_EXP, COL_TSP_ML, START_ROW = 31, 32, 6
        rows = []
        for sheet in xl.sheet_names:
            dfs = pd.read_excel(file_safi, sheet_name=sheet, header=None)
            if dfs.shape[1] <= COL_TSP_ML:
                continue
            for ri in range(START_ROW, len(dfs)):
                jour_val = dfs.iloc[ri, 0]
                if pd.isna(jour_val) or str(jour_val).strip() in ("", "nan", "Total", "TOTAL"):
                    continue
                try:
                    jour_num = int(float(str(jour_val).strip()))
                except ValueError:
                    continue
                tsp_exp = force_nombre(dfs.iloc[ri, COL_TSP_EXP])
                tsp_ml  = force_nombre(dfs.iloc[ri, COL_TSP_ML])
                rows.append({"Mois": sheet, "Jour": jour_num,
                             "TSP Export": tsp_exp, "TSP ML": tsp_ml,
                             "TOTAL Safi": tsp_exp + tsp_ml})
        safi_df = pd.DataFrame(rows) if rows else None
    except Exception as e:
        st.sidebar.error(f"Erreur Safi : {e}")

# ─── FILTRES SIDEBAR ─────────────────────────────────────────────────────────
st.sidebar.divider()
st.sidebar.header("🔍 Filtrage")

if jerf_df is not None:
    dates_jerf = ["Toutes"] + list(jerf_df["Date"].unique())
    choix_jerf = st.sidebar.selectbox("📅 Période Jerf", dates_jerf)
else:
    choix_jerf = "Toutes"

if safi_df is not None:
    mois_safi  = ["Tous"] + list(safi_df["Mois"].unique())
    choix_safi = st.sidebar.selectbox("📅 Mois Safi", mois_safi)
else:
    choix_safi = "Tous"

# ─── CUMULS ──────────────────────────────────────────────────────────────────
cumul_jerf  = float(jerf_df["TOTAL Jerf"].sum()) if jerf_df is not None else 0.0
cumul_safi  = float(safi_df["TOTAL Safi"].sum()) if safi_df is not None else 0.0
cumul_total = cumul_jerf + cumul_safi

# ─── KPI CARDS ───────────────────────────────────────────────────────────────
st.markdown("### 📌 Cumul à Date — Toute la Période")

c1, c2, c3 = st.columns(3)
with c1:
    sub1 = "Export Engrais + Camions + VL" if jerf_df is not None else "⚠️ Fichier non chargé"
    st.markdown(f"""
        <div class="kpi-card jerf">
            <div class="kpi-label">🏭 Total Jerf Lasfar</div>
            <div class="kpi-value">{fmt_number(cumul_jerf)}</div>
            <div class="kpi-sub">{sub1}</div>
        </div>""", unsafe_allow_html=True)
with c2:
    sub2 = "TSP Export + TSP ML" if safi_df is not None else "⚠️ Fichier non chargé"
    st.markdown(f"""
        <div class="kpi-card safi">
            <div class="kpi-label">🏗️ Total Safi</div>
            <div class="kpi-value">{fmt_number(cumul_safi)}</div>
            <div class="kpi-sub">{sub2}</div>
        </div>""", unsafe_allow_html=True)
with c3:
    st.markdown(f"""
        <div class="kpi-card total">
            <div class="kpi-label">📊 Total Jerf + Safi</div>
            <div class="kpi-value">{fmt_number(cumul_total)}</div>
            <div class="kpi-sub">Consolidé toutes unités</div>
        </div>""", unsafe_allow_html=True)

st.divider()

# ─── SECTION JERF ────────────────────────────────────────────────────────────
st.markdown('<div class="section-header jerf">🏭 Jerf Lasfar — Chargement Export</div>', unsafe_allow_html=True)

if jerf_df is not None:
    show_jerf = jerf_df if choix_jerf == "Toutes" else jerf_df[jerf_df["Date"] == choix_jerf]
    st.dataframe(
        show_jerf, use_container_width=True, hide_index=True,
        height=min(500, 45 + 35 * len(show_jerf)),
        column_config={
            "Date":           st.column_config.TextColumn("Date"),
            "Export Engrais": st.column_config.NumberColumn("Export Engrais", format="%d"),
            "Export Camions": st.column_config.NumberColumn("Export Camions", format="%d"),
            "VL Camions":     st.column_config.NumberColumn("VL Camions",     format="%d"),
            "TOTAL Jerf":     st.column_config.NumberColumn("TOTAL Jerf ✅",  format="%d"),
        }
    )
    export_buttons(show_jerf, "Jerf", "Rapport Jerf Lasfar", choix_jerf)
    if choix_jerf == "Toutes" and len(jerf_df) > 1:
        st.line_chart(jerf_df.set_index("Date")["TOTAL Jerf"], color="#00843D")
else:
    st.info("⬅️ Chargez le fichier **Reporting-JPH 2026** dans la barre latérale pour voir les données Jerf.")

st.divider()

# ─── SECTION SAFI ────────────────────────────────────────────────────────────
st.markdown('<div class="section-header safi">🏗️ Safi — TSP Export & TSP ML</div>', unsafe_allow_html=True)

if safi_df is not None:
    show_safi = safi_df if choix_safi == "Tous" else safi_df[safi_df["Mois"] == choix_safi]
    st.dataframe(
        show_safi, use_container_width=True, hide_index=True,
        height=min(500, 45 + 35 * len(show_safi)),
        column_config={
            "Mois":       st.column_config.TextColumn("Mois"),
            "Jour":       st.column_config.NumberColumn("Jour",       format="%d"),
            "TSP Export": st.column_config.NumberColumn("TSP Export", format="%d"),
            "TSP ML":     st.column_config.NumberColumn("TSP ML",     format="%d"),
            "TOTAL Safi": st.column_config.NumberColumn("TOTAL Safi ✅", format="%d"),
        }
    )
    export_buttons(show_safi, "Safi", "Rapport Safi TSP", choix_safi)
    if len(show_safi) > 1:
        chart_df = show_safi.copy()
        chart_df["Label"] = chart_df["Mois"].astype(str) + "-J" + chart_df["Jour"].astype(str)
        st.line_chart(chart_df.set_index("Label")[["TSP Export", "TSP ML"]])
else:
    st.info("⬅️ Chargez le fichier **SUIVI DE LA PRODUCTION MFS** dans la barre latérale pour voir les données Safi.")

st.divider()

# ─── SECTION TOTAL ───────────────────────────────────────────────────────────
st.markdown('<div class="section-header total">📊 Total Consolidé — Jerf + Safi par Mois</div>', unsafe_allow_html=True)

if jerf_df is not None or safi_df is not None:
    if jerf_df is not None:
        jdf = jerf_df.copy()
        jdf["Mois"] = jdf["Date"].apply(extract_mois)
        j_mois = jdf.groupby("Mois")["TOTAL Jerf"].sum().reset_index()
        j_mois.columns = ["Mois", "TOTAL Jerf"]
    else:
        j_mois = pd.DataFrame(columns=["Mois", "TOTAL Jerf"])

    if safi_df is not None:
        s_mois = safi_df.groupby("Mois")["TOTAL Safi"].sum().reset_index()
        s_mois.columns = ["Mois", "TOTAL Safi"]
    else:
        s_mois = pd.DataFrame(columns=["Mois", "TOTAL Safi"])

    if jerf_df is not None and safi_df is not None:
        tot = pd.merge(j_mois, s_mois, on="Mois", how="outer").fillna(0)
    elif jerf_df is not None:
        tot = j_mois.copy(); tot["TOTAL Safi"] = 0.0
    else:
        tot = s_mois.copy(); tot["TOTAL Jerf"] = 0.0

    tot["TOTAL Jerf+Safi"] = tot["TOTAL Jerf"] + tot["TOTAL Safi"]

    total_row = pd.DataFrame([{
        "Mois": "🔢 TOTAL GÉNÉRAL",
        "TOTAL Jerf":      tot["TOTAL Jerf"].sum(),
        "TOTAL Safi":      tot["TOTAL Safi"].sum(),
        "TOTAL Jerf+Safi": tot["TOTAL Jerf+Safi"].sum()
    }])
    disp = pd.concat([tot, total_row], ignore_index=True)

    st.dataframe(
        disp, use_container_width=True, hide_index=True,
        column_config={
            "Mois":            st.column_config.TextColumn("Mois"),
            "TOTAL Jerf":      st.column_config.NumberColumn("Total Jerf",      format="%d"),
            "TOTAL Safi":      st.column_config.NumberColumn("Total Safi",      format="%d"),
            "TOTAL Jerf+Safi": st.column_config.NumberColumn("Total Jerf+Safi", format="%d"),
        }
    )
    export_buttons(disp, "Total_Consolide", "Rapport Total Jerf + Safi", "Consolidé")
    if len(tot) > 1:
        st.bar_chart(tot.set_index("Mois")[["TOTAL Jerf", "TOTAL Safi"]])
else:
    st.info("⬅️ Chargez au moins un fichier pour voir le total consolidé.")




