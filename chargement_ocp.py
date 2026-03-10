import streamlit as st
import pandas as pd
import re
import os

st.set_page_config(page_title="OCP - Suivi chargement Export", layout="wide")

st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Barlow:wght@400;600;700&family=Barlow+Condensed:wght@600;700&display=swap');
        :root { --ocp-green: #00843D; --ocp-dark: #005C2A; --jorf-color: #00843D; --safi-color: #1A6FA8; --total-color: #C05A00; --rade-color: #6B3FA0; }
        html, body, [class*="css"] { font-family: 'Barlow', sans-serif; }
        .stApp { background-color: #F4F7F5; }
        h1, h2, h3 { color: var(--ocp-dark) !important; font-family: 'Barlow Condensed', sans-serif !important; }
        .kpi-card { border-radius: 12px; padding: 20px 24px; color: white; box-shadow: 0 4px 16px rgba(0,0,0,0.12); position: relative; overflow: hidden; }
        .kpi-card::before { content: ''; position: absolute; top: -20px; right: -20px; width: 100px; height: 100px; border-radius: 50%; background: rgba(255,255,255,0.1); }
        .kpi-card.jorf  { background: linear-gradient(135deg, #00843D, #005C2A); }
        .kpi-card.safi  { background: linear-gradient(135deg, #1A6FA8, #0D4A73); }
        .kpi-card.total { background: linear-gradient(135deg, #C05A00, #8A3F00); }
        .kpi-card.rade  { background: linear-gradient(135deg, #6B3FA0, #4A2A73); }
        .kpi-label { font-size: 12px; font-weight: 600; opacity: 0.85; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 6px; }
        .kpi-value { font-family: 'Barlow Condensed', sans-serif; font-size: 38px; font-weight: 700; line-height: 1; }
        .kpi-sub   { font-size: 11px; opacity: 0.7; margin-top: 4px; }
        .section-header { display: flex; align-items: center; gap: 10px; padding: 10px 16px; border-radius: 8px; margin: 20px 0 10px 0; font-family: 'Barlow Condensed', sans-serif; font-size: 20px; font-weight: 700; color: white; }
        .section-header.jorf  { background: var(--jorf-color); }
        .section-header.safi  { background: var(--safi-color); }
        .section-header.total { background: var(--total-color); }
        .section-header.rade  { background: var(--rade-color); }
        [data-testid="stSidebar"] { border-right: 3px solid var(--ocp-green); background: #FAFFF9; }
        hr { border-color: #D0E8D9 !important; }
    </style>
""", unsafe_allow_html=True)

# Dictionnaire mois
NOMS_MOIS = {1:"Jan",2:"Fev",3:"Mar",4:"Avr",5:"Mai",6:"Jun",
             7:"Jul",8:"Aou",9:"Sep",10:"Oct",11:"Nov",12:"Dec"}
ORDRE_MOIS = {v:k for k,v in NOMS_MOIS.items()}

def force_nombre(valeur):
    if pd.isna(valeur): return 0.0
    if isinstance(valeur, (int, float)):
        return 0.0 if abs(valeur) < 1e-6 else float(valeur)
    s = str(valeur).strip()
    if s in ("-", "", "nan"): return 0.0
    nettoye = re.sub(r'[^\d]', '', s.replace("\xa0", "").replace(" ", ""))
    if len(nettoye) > 12: return 0.0
    try:
        return float(nettoye)
    except ValueError:
        return 0.0

def en_milliers(v):
    return round(v / 1000, 1)

def fmt_number(n):
    return f"{n:,.1f}".replace(",", " ")

def copier_ligne_btn(df, total_col, label, key):
    vals = df[df["Date"] != "TOTAL GENERAL"][total_col].dropna().tolist()
    ligne_txt = "\t".join(str(round(v, 1)) for v in vals)
    btn_id = f"btn_{key}"
    st.components.v1.html(f"""
        <style>
            #{btn_id} {{ background: #00843D; color: white; border: none; padding: 7px 18px; border-radius: 7px; cursor: pointer; font-family: Barlow, sans-serif; font-size: 14px; font-weight: 600; }}
            #{btn_id}.copied {{ background: #1A6FA8; }}
        </style>
        <button id="{btn_id}" onclick="navigator.clipboard.writeText('{ligne_txt}').then(() => {{ this.innerHTML = 'Copie effectuee'; this.classList.add('copied'); setTimeout(() => {{ this.innerHTML = 'Copier {label} en ligne'; this.classList.remove('copied'); }}, 2000); }});">Copier {label} en ligne</button>
    """, height=45)

def extract_mois_label(date_str):
    try:
        parts = str(date_str).split("/")
        if len(parts) == 3:
            return f"{NOMS_MOIS.get(int(parts[1]),'?')} {parts[2]}"
    except:
        pass
    return "Inconnu"

def mois_sort_key(m):
    try:
        parts = m.split()
        return (int(parts[1]), ORDRE_MOIS.get(parts[0], 99))
    except:
        return (9999, 99)

SKIP_KEYWORDS = ["total","recap","recapitulatif","annee","annuel","bilan","synthese","summary"]

def is_data_sheet(name):
    return not any(kw in name.strip().lower() for kw in SKIP_KEYWORDS)

def read_excel_any(file):
    filename = getattr(file, 'name', '').lower()
    if filename.endswith('.xls') and not filename.endswith('.xlsx') and not filename.endswith('.xlsm'):
        return 'xlrd'
    return 'openpyxl'

# HEADER
col_logo, col_title = st.columns([1, 5])
with col_logo:
    if os.path.exists("logo_ocp.png"):
        st.image("logo_ocp.png", width=110)
    else:
        st.markdown("<div style='font-size:34px;font-weight:900;color:#00843D;font-family:Barlow Condensed,sans-serif;'>OCP</div>", unsafe_allow_html=True)
with col_title:
    st.title("Suivi chargement export")
    st.markdown("##### Reporting Consolide — Jorf Lasfar & Safi &nbsp;|&nbsp; Valeurs en milliers de tonnes")

st.divider()

# SIDEBAR
st.sidebar.header("Chargement des fichiers")
EXCEL_TYPES = ["xlsx", "xls", "xlsm"]
file_jorf = st.sidebar.file_uploader("Fichier Jorf", type=EXCEL_TYPES, key="jorf")
file_safi = st.sidebar.file_uploader("Fichier Safi", type=EXCEL_TYPES, key="safi")

# PARSE JORF
jorf_df = None
if file_jorf:
    try:
        engine = read_excel_any(file_jorf)
        df_raw = pd.read_excel(file_jorf, sheet_name='EXPORT', header=None, engine=engine)
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
            v1 = en_milliers(force_nombre(df_raw.iloc[coords["ENGRAIS"], j])) if coords["ENGRAIS"] is not None else 0.0
            v2 = en_milliers(force_nombre(df_raw.iloc[coords["CAMIONS"], j])) if coords["CAMIONS"] is not None else 0.0
            v3 = en_milliers(force_nombre(df_raw.iloc[coords["VL"], j]))      if coords["VL"] is not None else 0.0
            rows.append({"Date": dl, "Export Engrais": v1, "Export Camions": v2,
                         "VL Camions": v3, "TOTAL Jorf": round(v1 + v2 + v3, 1)})
        jorf_df = pd.DataFrame(rows)
    except Exception as e:
        st.sidebar.error(f"Erreur Jorf : {e}")

# PARSE RADE
rade_df = None
if file_jorf:
    try:
        engine = read_excel_any(file_jorf)
        df_rade = pd.read_excel(file_jorf, sheet_name='Sit Navire', header=None, engine=engine)
        rows_rade = []
        for r in range(len(df_rade)):
            date_val = df_rade.iloc[r, 1]
            val      = df_rade.iloc[r, 3]
            if pd.isna(date_val) or pd.isna(val): continue
            s_date = str(date_val).strip()
            if s_date in ("", "nan", "Date"): continue
            date_label = date_val.strftime('%d/%m/%Y') if hasattr(date_val, 'strftime') else s_date
            rows_rade.append({"Date": date_label, "Engrais en attente": en_milliers(force_nombre(val))})
        rade_df = pd.DataFrame(rows_rade) if rows_rade else None
    except:
        pass

# PARSE SAFI
safi_df = None
if file_safi:
    try:
        engine = read_excel_any(file_safi)
        xl = pd.ExcelFile(file_safi, engine=engine)
        COL_JOUR = 1; COL_TSP_EXP = 31; COL_TSP_ML = 32; START_ROW = 6

        def normaliser(s):
            """Supprime les accents et met en minuscule."""
            accents = {"é":"e","è":"e","ê":"e","ë":"e","à":"a","â":"a","ù":"u",
                       "û":"u","ô":"o","î":"i","ï":"i","ç":"c","ü":"u","ö":"o"}
            s = s.lower()
            for a, b in accents.items():
                s = s.replace(a, b)
            return s

        def parse_mois_annee(sheet_name):
            mois_map = {
                "jan":1, "fev":2, "fev":2, "mar":3, "avr":4, "mai":5,
                "jun":6, "jui":6, "jul":7, "aou":8, "sep":9,
                "oct":10, "nov":11, "dec":12
            }
            # Variantes longues (ex: "Février 2026", "février", "fevrier")
            mois_long = {
                "janvier":1, "fevrier":2, "mars":3, "avril":4, "mai":5,
                "juin":6, "juillet":7, "aout":8, "septembre":9,
                "octobre":10, "novembre":11, "decembre":12
            }
            parts = sheet_name.strip().split()
            mois_num = None; annee = None
            for p in parts:
                p_norm = normaliser(p)
                # Essai correspondance courte (3 lettres)
                if p_norm[:3] in mois_map:
                    mois_num = mois_map[p_norm[:3]]
                # Essai correspondance longue
                if p_norm in mois_long:
                    mois_num = mois_long[p_norm]
                try:
                    y = int(p)
                    if 2000 <= y <= 2100: annee = y
                except: pass
            return mois_num, annee

        rows = []
        for sheet in xl.sheet_names:
            if not is_data_sheet(sheet): continue
            mois_num, annee = parse_mois_annee(sheet)
            if mois_num is None or annee is None: continue
            dfs = pd.read_excel(file_safi, sheet_name=sheet, header=None, engine=engine)
            tsp_exp_col = COL_TSP_EXP; tsp_ml_col = COL_TSP_ML
            if dfs.shape[1] <= COL_TSP_ML:
                found_exp = False
                for hrow in range(min(8, len(dfs))):
                    row_vals = [str(v).strip().upper() for v in dfs.iloc[hrow]]
                    for ci, v in enumerate(row_vals):
                        if "TSP" in v and "EXPORT" in v: tsp_exp_col = ci; found_exp = True
                        if "TSP" in v and "ML" in v: tsp_ml_col = ci
                if not found_exp: continue
            for ri in range(START_ROW, len(dfs)):
                jour_val = dfs.iloc[ri, COL_JOUR]
                if pd.isna(jour_val): continue
                s = str(jour_val).strip()
                if s in ("", "nan") or any(k in s.upper() for k in ["TOTAL","CUMUL","MOYENNE","MOY"]): continue
                try: jour_num = int(float(s))
                except ValueError: continue
                if jour_num < 1 or jour_num > 31: continue
                tsp_exp = en_milliers(force_nombre(dfs.iloc[ri, tsp_exp_col])) if tsp_exp_col < dfs.shape[1] else 0.0
                tsp_ml  = en_milliers(force_nombre(dfs.iloc[ri, tsp_ml_col]))  if tsp_ml_col  < dfs.shape[1] else 0.0
                rows.append({"Mois": sheet, "Jour": jour_num,
                             "Date": f"{jour_num:02d}/{mois_num:02d}/{annee}",
                             "TSP Export": tsp_exp, "TSP ML": tsp_ml,
                             "TOTAL Safi": round(tsp_exp + tsp_ml, 1)})
        safi_df = pd.DataFrame(rows) if rows else None
    except Exception as e:
        st.sidebar.error(f"Erreur Safi : {e}")

# FILTRES
st.sidebar.divider()
st.sidebar.header("Filtrage")

def filtre_dates_sidebar(df, label_prefix, key_prefix, date_col="Date"):
    # Mois présents dans les données
    mois_map = {}
    annees_presentes = set()
    for d in df[date_col].unique():
        try:
            parts = str(d).split("/")
            annees_presentes.add(int(parts[2]))
            m_label = f"{NOMS_MOIS.get(int(parts[1]),'?')} {parts[2]}"
        except:
            m_label = "Autre"
        mois_map.setdefault(m_label, []).append(d)

    # Ajouter les 12 mois pour chaque année présente (même sans données)
    for annee in annees_presentes:
        for num, nom in NOMS_MOIS.items():
            m_label = f"{nom} {annee}"
            if m_label not in mois_map:
                mois_map[m_label] = []  # liste vide = pas de données

    # Tri chronologique
    mois_tries = sorted(mois_map.keys(), key=mois_sort_key)
    # Options : mois avec données normaux, mois sans données avec indication
    options_finales = []
    for m in mois_tries:
        if mois_map[m]:
            options_finales.append(m)
        else:
            options_finales.append(f"{m} —")  # marqueur "pas de données"

    mode = st.sidebar.radio(f"Filtrer {label_prefix} par",
                            ["Tout", "Mois", "Dates"], horizontal=True, key=f"{key_prefix}_mode")
    if mode == "Tout":
        return [], "Toute la periode"
    elif mode == "Mois":
        choix_mois = st.sidebar.multiselect(
            f"Mois {label_prefix} (— = aucune donnee)",
            options=options_finales,
            default=[],
            key=f"{key_prefix}_mois"
        )
        if not choix_mois: return [], "Toute la periode"
        # Récupérer les vraies clés (sans le marqueur "—")
        dates_sel = []
        labels_sel = []
        for m in choix_mois:
            cle = m.rstrip(" —")
            dates_sel += mois_map.get(cle, [])
            labels_sel.append(cle)
        return dates_sel, ", ".join(labels_sel)
    else:
        all_dates = sorted(df[date_col].unique().tolist(),
                           key=lambda d: tuple(int(x) for x in str(d).split("/"))[::-1])
        choix_dates = st.sidebar.multiselect(f"Dates {label_prefix}", all_dates, key=f"{key_prefix}_dates")
        if not choix_dates: return [], "Toute la periode"
        return choix_dates, f"{len(choix_dates)} date(s)"

if jorf_df is not None:
    st.sidebar.markdown("**Jorf Lasfar**")
    sel_jorf, label_jorf = filtre_dates_sidebar(jorf_df, "Jorf", "jorf")
else:
    sel_jorf, label_jorf = [], "Toute la periode"

if safi_df is not None:
    st.sidebar.markdown("**Safi**")
    sel_safi, label_safi = filtre_dates_sidebar(safi_df, "Safi", "safi")
else:
    sel_safi, label_safi = [], "Toute la periode"

def appliquer_filtre(df, sel, col="Date"):
    if not sel: return df
    return df[df[col].isin(sel)]

# ─── CUMULS reactifs au filtre ───────────────────────────────────────────────
jorf_kpi = appliquer_filtre(jorf_df, sel_jorf) if jorf_df is not None else None
safi_kpi = appliquer_filtre(safi_df, sel_safi) if safi_df is not None else None
rade_kpi = appliquer_filtre(rade_df, sel_jorf) if rade_df is not None else None

cumul_jorf  = round(float(jorf_kpi["TOTAL Jorf"].sum()), 1)              if jorf_kpi is not None else 0.0
cumul_safi  = round(float(safi_kpi["TOTAL Safi"].sum()), 1)              if safi_kpi is not None else 0.0
cumul_rade  = round(float(rade_kpi["Engrais en attente"].sum()), 1)      if rade_kpi is not None else 0.0
# Rade Safi : on prend TSP ML comme proxy rade safi (à adapter si source différente)
cumul_rade_safi = round(float(safi_kpi["TSP ML"].sum()), 1)              if safi_kpi is not None else 0.0
cumul_total = round(cumul_jorf + cumul_safi, 1)

periode_label = f"Filtre : {label_jorf} / {label_safi}" if (sel_jorf or sel_safi) else "Toute la Periode"

# ─── KPI CARDS — 1 seule ligne ───────────────────────────────────────────────
st.markdown(f"### Cumul a Date — {periode_label}")
k1, k2, k3, k4, k5 = st.columns(5)
with k1:
    sub1 = "Export Engrais + Camions + VL" if jorf_df is not None else "Fichier non charge"
    st.markdown(f"""<div class="kpi-card jorf"><div class="kpi-label">Total Jorf</div><div class="kpi-value">{fmt_number(cumul_jorf)}</div><div class="kpi-sub">{sub1}</div></div>""", unsafe_allow_html=True)
with k2:
    sub_rade = "Engrais en attente Rade" if rade_df is not None else "Fichier non charge"
    st.markdown(f"""<div class="kpi-card rade"><div class="kpi-label">Rade Jorf</div><div class="kpi-value">{fmt_number(cumul_rade)}</div><div class="kpi-sub">{sub_rade}</div></div>""", unsafe_allow_html=True)
with k3:
    sub2 = "Export Engrais + VL Camions" if safi_df is not None else "Fichier non charge"
    st.markdown(f"""<div class="kpi-card safi"><div class="kpi-label">Total Safi</div><div class="kpi-value">{fmt_number(cumul_safi)}</div><div class="kpi-sub">{sub2}</div></div>""", unsafe_allow_html=True)
with k4:
    sub_rs = "VL Camions Safi" if safi_df is not None else "Fichier non charge"
    st.markdown(f"""<div class="kpi-card rade"><div class="kpi-label">Rade Safi</div><div class="kpi-value">{fmt_number(cumul_rade_safi)}</div><div class="kpi-sub">{sub_rs}</div></div>""", unsafe_allow_html=True)
with k5:
    st.markdown(f"""<div class="kpi-card total"><div class="kpi-label">Total Jorf + Safi</div><div class="kpi-value">{fmt_number(cumul_total)}</div><div class="kpi-sub">Consolide toutes unites</div></div>""", unsafe_allow_html=True)

st.divider()

# ─── TABLE UNIFIEE ────────────────────────────────────────────────────────────
# Colonnes renommées : TSP Export → Export Engrais Safi, TSP ML → ML Safi
st.markdown('<div class="section-header total">Tableau Consolide — Toutes Donnees par Jour (KT)</div>', unsafe_allow_html=True)

# En-tête groupé HTML
st.markdown("""
<style>
.grp-header { display: flex; width: 100%; margin-bottom: 4px; font-family: 'Barlow Condensed', sans-serif; font-weight: 700; font-size: 13px; }
.grp-jorf  { background:#00843D; color:white; padding:4px 10px; border-radius:4px; margin-right:4px; flex:4; text-align:center; }
.grp-safi  { background:#1A6FA8; color:white; padding:4px 10px; border-radius:4px; margin-right:4px; flex:3; text-align:center; }
.grp-rade  { background:#6B3FA0; color:white; padding:4px 10px; border-radius:4px; margin-right:4px; flex:1; text-align:center; }
.grp-total { background:#C05A00; color:white; padding:4px 10px; border-radius:4px; flex:1; text-align:center; }
</style>
<div class="grp-header">
  <div style="min-width:90px;flex:0"></div>
  <div class="grp-jorf">JORF LASFAR</div>
  <div class="grp-safi">SAFI</div>
  <div class="grp-rade">RADE</div>
  <div class="grp-total">TOTAL</div>
</div>
""", unsafe_allow_html=True)

any_data = jorf_df is not None or safi_df is not None or rade_df is not None

if any_data:
    def date_sort_key(d):
        try:
            parts = str(d).split("/")
            return (int(parts[2]), int(parts[1]), int(parts[0]))
        except:
            return (9999, 99, 99)

    jorf_f = appliquer_filtre(jorf_df, sel_jorf) if jorf_df is not None else None
    rade_f = appliquer_filtre(rade_df, sel_jorf) if rade_df is not None else None
    safi_f = appliquer_filtre(safi_df, sel_safi) if safi_df is not None else None

    all_dates = set()
    if jorf_f is not None: all_dates |= set(jorf_f["Date"].unique())
    if rade_f is not None: all_dates |= set(rade_f["Date"].unique())
    if safi_f is not None: all_dates |= set(safi_f["Date"].unique())
    all_dates = sorted(all_dates, key=date_sort_key)

    unified_rows = []
    for d in all_dates:
        row = {"Date": d}
        # ── JORF détail ──
        if jorf_f is not None:
            r = jorf_f[jorf_f["Date"] == d]
            row["J_Engrais"] = round(r["Export Engrais"].sum(), 1) if not r.empty else 0.0
            row["J_Camions"] = round(r["Export Camions"].sum(), 1) if not r.empty else 0.0
            row["J_VL"]      = round(r["VL Camions"].sum(), 1)     if not r.empty else 0.0
        # ── SAFI détail ──
        if safi_f is not None:
            r = safi_f[safi_f["Date"] == d]
            row["S_Engrais"] = round(r["TSP Export"].sum(), 1) if not r.empty else 0.0
            row["S_VL"]      = round(r["TSP ML"].sum(), 1)     if not r.empty else 0.0
        # ── TOTAUX ──
        j_tot = round(
            row.get("J_Engrais",0.0)+row.get("J_Camions",0.0)+row.get("J_VL",0.0), 1
        ) if jorf_f is not None else 0.0
        s_tot = round(
            row.get("S_Engrais",0.0)+row.get("S_VL",0.0), 1
        ) if safi_f is not None else 0.0
        if jorf_f is not None: row["J_TOTAL"] = j_tot
        if safi_f is not None: row["S_TOTAL"] = s_tot
        row["TOTAL"] = round(j_tot + s_tot, 1)
        # ── RADE JORF ──
        if rade_f is not None:
            r = rade_f[rade_f["Date"] == d]
            row["RADE_J"] = round(r["Engrais en attente"].sum(), 1) if not r.empty else 0.0
        # ── RADE SAFI (TSP ML = mise a la mer / attente) ──
        if safi_f is not None:
            r = safi_f[safi_f["Date"] == d]
            row["RADE_S"] = round(r["TSP ML"].sum(), 1) if not r.empty else 0.0
        unified_rows.append(row)

    unified_df = pd.DataFrame(unified_rows)

    # Ordre explicite des colonnes
    col_order = ["Date"]
    if jorf_f is not None: col_order += ["J_Engrais", "J_Camions", "J_VL"]
    if safi_f is not None: col_order += ["S_Engrais", "S_VL"]
    if jorf_f is not None: col_order += ["J_TOTAL"]
    if safi_f is not None: col_order += ["S_TOTAL"]
    col_order += ["TOTAL"]
    if rade_f is not None: col_order += ["RADE_J"]
    if safi_f is not None: col_order += ["RADE_S"]
    col_order = [c for c in col_order if c in unified_df.columns]
    unified_df = unified_df[col_order]

    # Ligne TOTAL GENERAL
    total_row = {"Date": "TOTAL GENERAL"}
    for col in unified_df.columns:
        if col != "Date":
            total_row[col] = round(unified_df[col].sum(), 1)
    disp_unified = pd.concat([unified_df, pd.DataFrame([total_row])], ignore_index=True)

    # Config colonnes
    col_cfg = {"Date": st.column_config.TextColumn("Date")}
    if jorf_f is not None:
        col_cfg["J_Engrais"] = st.column_config.NumberColumn("Export Engrais", format="%.1f")
        col_cfg["J_Camions"] = st.column_config.NumberColumn("Export Camions", format="%.1f")
        col_cfg["J_VL"]      = st.column_config.NumberColumn("VL Camions",     format="%.1f")
    if safi_f is not None:
        col_cfg["S_Engrais"] = st.column_config.NumberColumn("Export Engrais", format="%.1f")
        col_cfg["S_VL"]      = st.column_config.NumberColumn("VL Camions",     format="%.1f")
    if jorf_f is not None:
        col_cfg["J_TOTAL"]   = st.column_config.NumberColumn("Total Jorf",     format="%.1f")
    if safi_f is not None:
        col_cfg["S_TOTAL"]   = st.column_config.NumberColumn("Total Safi",     format="%.1f")
    col_cfg["TOTAL"]  = st.column_config.NumberColumn("Total Jorf+Safi", format="%.1f")
    if rade_f is not None:
        col_cfg["RADE_J"] = st.column_config.NumberColumn("Rade Jorf",  format="%.1f")
    if safi_f is not None:
        col_cfg["RADE_S"] = st.column_config.NumberColumn("Rade Safi",  format="%.1f")

    st.dataframe(disp_unified, use_container_width=True, hide_index=True,
        height=min(700, 45 + 35 * len(disp_unified)),
        column_config=col_cfg)

    col_copy1, col_copy2, col_copy3 = st.columns(3)
    with col_copy1:
        if jorf_f is not None: copier_ligne_btn(unified_df, "J_TOTAL", "Total Jorf", "copy_jorf")
    with col_copy2:
        if safi_f is not None: copier_ligne_btn(unified_df, "S_TOTAL", "Total Safi", "copy_safi")
    with col_copy3:
        copier_ligne_btn(unified_df, "TOTAL", "Total Jorf+Safi", "copy_total")

    st.divider()

    # ─── 2 GRAPHIQUES COTE A COTE ────────────────────────────────────────────
    g_left, g_right = st.columns(2)

    # GRAPHIQUE GAUCHE — Rade (barres violettes)
    with g_left:
        st.markdown('<div class="section-header rade">Rade Jorf — Engrais en Attente</div>', unsafe_allow_html=True)
        if rade_f is not None and "RADE_J" in unified_df.columns and len(unified_df) > 1:
            rade_chart = unified_df[unified_df["RADE_J"] > 0].copy()
            if len(rade_chart) > 0:
                st.bar_chart(
                    rade_chart.set_index("Date")[["RADE_J"]].rename(columns={"RADE_J": "Rade Jorf"}),
                    color="#6B3FA0"
                )
            else:
                st.info("Pas de donnees Rade disponibles.")
        else:
            st.info("Chargez le fichier Jorf pour voir la Rade.")

    # GRAPHIQUE DROIT — Jorf + Safi par mois (barres groupées)
    with g_right:
        st.markdown('<div class="section-header total">Jorf + Safi — Evolution Mensuelle</div>', unsafe_allow_html=True)
        chart_df = unified_df.copy()
        chart_df["Mois"] = chart_df["Date"].apply(extract_mois_label)
        chart_df = chart_df[chart_df["Mois"] != "Inconnu"]
        cols_mois = [c for c in ["J_TOTAL", "S_TOTAL"] if c in chart_df.columns]
        if cols_mois and len(chart_df) > 0:
            mois_tot = chart_df.groupby("Mois")[cols_mois].sum().reset_index()
            mois_tot["_sort"] = mois_tot["Mois"].apply(mois_sort_key)
            mois_tot = mois_tot.sort_values("_sort").drop(columns=["_sort"]).reset_index(drop=True)
            mois_tot = mois_tot[mois_tot[cols_mois].sum(axis=1) > 0]
            if len(mois_tot) > 0:
                mois_tot = mois_tot.rename(columns={"J_TOTAL": "Total Jorf", "S_TOTAL": "Total Safi"})
                st.bar_chart(mois_tot.set_index("Mois")[["Total Jorf", "Total Safi"]], color=["#00843D", "#1A6FA8"])
            else:
                st.info("Pas encore de donnees pour le graphique mensuel.")
        else:
            st.info("Chargez les fichiers pour voir le graphique.")
else:
    st.info("Chargez au moins un fichier pour voir le tableau consolide.")
