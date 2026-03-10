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

# ─── HELPERS ────────────────────────────────────────────────────────────────

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

def fmt_number(n):
    return f"{int(n):,}".replace(",", " ")

def copier_ligne_btn(df, total_col, label, key):
    vals = df[df["Date"] != "TOTAL GENERAL"][total_col].dropna().tolist()
    ligne_txt = "\t".join(str(int(v)) for v in vals)
    btn_id = f"btn_{key}"
    st.components.v1.html(f"""
        <style>
            #{btn_id} {{
                background: #00843D; color: white; border: none;
                padding: 7px 18px; border-radius: 7px; cursor: pointer;
                font-family: Barlow, sans-serif; font-size: 14px; font-weight: 600;
            }}
            #{btn_id}.copied {{ background: #1A6FA8; }}
        </style>
        <button id="{btn_id}" onclick="
            navigator.clipboard.writeText('{ligne_txt}').then(() => {{
                this.innerHTML = 'Copie effectuee';
                this.classList.add('copied');
                setTimeout(() => {{ this.innerHTML = 'Copier {label} en ligne'; this.classList.remove('copied'); }}, 2000);
            }});
        ">Copier {label} en ligne</button>
    """, height=45)

def extract_mois_label(date_str):
    try:
        parts = str(date_str).split("/")
        if len(parts) == 3:
            m = int(parts[1]); y = parts[2]
            noms = {1:"Jan",2:"Fev",3:"Mar",4:"Avr",5:"Mai",6:"Jun",
                    7:"Jul",8:"Aou",9:"Sep",10:"Oct",11:"Nov",12:"Dec"}
            return f"{noms.get(m,'?')} {y}"
    except:
        pass
    return "Inconnu"

def normalise_sheet_name(name):
    n = name.strip().lower()
    for k, v in {"e":"e","e":"e","e":"e","a":"a","a":"a","u":"u","o":"o","i":"i","c":"c"}.items():
        n = n.replace(k, v)
    return n

SKIP_KEYWORDS = ["total","recap","recapitulatif","annee","annuel","bilan","synthese","summary"]

def is_data_sheet(name):
    norm = name.strip().lower()
    return not any(kw in norm for kw in SKIP_KEYWORDS)

def read_excel_any(file):
    """Lit un fichier Excel peu importe le format (.xlsx, .xls, .xlsm)."""
    filename = getattr(file, 'name', '').lower()
    if filename.endswith('.xls') and not filename.endswith('.xlsx') and not filename.endswith('.xlsm'):
        # Ancien format binaire .xls — nécessite xlrd
        engine = 'xlrd'
    else:
        # .xlsx et .xlsm sont gérés par openpyxl
        engine = 'openpyxl'
    return engine

# ─── HEADER ──────────────────────────────────────────────────────────────────
col_logo, col_title = st.columns([1, 5])
with col_logo:
    if os.path.exists("logo_ocp.png"):
        st.image("logo_ocp.png", width=110)
    else:
        st.markdown("<div style='font-size:34px;font-weight:900;color:#00843D;font-family:Barlow Condensed,sans-serif;'>OCP</div>", unsafe_allow_html=True)
with col_title:
    st.title("Suivi chargement export")
    st.markdown("##### Reporting Consolide — Jorf Lasfar & Safi")

st.divider()

# ─── SIDEBAR ─────────────────────────────────────────────────────────────────
st.sidebar.header("Chargement des fichiers")
# Accepte .xlsx, .xls et .xlsm
EXCEL_TYPES = ["xlsx", "xls", "xlsm"]
file_jorf = st.sidebar.file_uploader("Fichier Jorf", type=EXCEL_TYPES, key="jorf")
file_safi = st.sidebar.file_uploader("Fichier Safi", type=EXCEL_TYPES, key="safi")

# ─── PARSE JORF ──────────────────────────────────────────────────────────────
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
            v1 = force_nombre(df_raw.iloc[coords["ENGRAIS"], j]) if coords["ENGRAIS"] is not None else 0.0
            v2 = force_nombre(df_raw.iloc[coords["CAMIONS"], j]) if coords["CAMIONS"] is not None else 0.0
            v3 = force_nombre(df_raw.iloc[coords["VL"], j])      if coords["VL"] is not None else 0.0
            rows.append({"Date": dl, "Export Engrais": v1, "Export Camions": v2,
                         "VL Camions": v3, "TOTAL Jorf": v1 + v2 + v3})
        jorf_df = pd.DataFrame(rows)
    except Exception as e:
        st.sidebar.error(f"Erreur Jorf : {e}")

# ─── PARSE RADE (Sit Navire) ─────────────────────────────────────────────────
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
            if hasattr(date_val, 'strftime'):
                date_label = date_val.strftime('%d/%m/%Y')
            else:
                date_label = s_date
            val_num = force_nombre(val)
            rows_rade.append({"Date": date_label, "Engrais en attente": val_num})
        rade_df = pd.DataFrame(rows_rade) if rows_rade else None
    except:
        pass

# ─── PARSE SAFI ──────────────────────────────────────────────────────────────
safi_df = None
if file_safi:
    try:
        engine = read_excel_any(file_safi)
        xl = pd.ExcelFile(file_safi, engine=engine)
        COL_JOUR = 1; COL_TSP_EXP = 31; COL_TSP_ML = 32; START_ROW = 6

        def parse_mois_annee(sheet_name):
            mois_map = {"jan":1,"fev":2,"fev":2,"mar":3,"avr":4,"mai":5,"jun":6,
                        "jui":6,"jul":7,"aou":8,"aou":8,"sep":9,"oct":10,"nov":11,"dec":12,"dec":12}
            parts = sheet_name.strip().split()
            mois_num = None; annee = None
            for p in parts:
                p_low = p.lower()[:3]
                if p_low in mois_map: mois_num = mois_map[p_low]
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
                tsp_exp = force_nombre(dfs.iloc[ri, tsp_exp_col]) if tsp_exp_col < dfs.shape[1] else 0.0
                tsp_ml  = force_nombre(dfs.iloc[ri, tsp_ml_col])  if tsp_ml_col  < dfs.shape[1] else 0.0
                rows.append({"Mois": sheet, "Jour": jour_num,
                             "Date": f"{jour_num:02d}/{mois_num:02d}/{annee}",
                             "TSP Export": tsp_exp, "TSP ML": tsp_ml,
                             "TOTAL Safi": tsp_exp + tsp_ml})
        safi_df = pd.DataFrame(rows) if rows else None
    except Exception as e:
        st.sidebar.error(f"Erreur Safi : {e}")

# ─── FILTRES SIDEBAR ─────────────────────────────────────────────────────────
st.sidebar.divider()
st.sidebar.header("Filtrage")

def filtre_dates_sidebar(df, label_prefix, key_prefix, date_col="Date"):
    mois_map = {}
    for d in df[date_col].unique():
        try:
            parts = str(d).split("/")
            noms = {1:"Jan",2:"Fev",3:"Mar",4:"Avr",5:"Mai",6:"Jun",
                    7:"Jul",8:"Aou",9:"Sep",10:"Oct",11:"Nov",12:"Dec"}
            m_label = f"{noms.get(int(parts[1]),'?')} {parts[2]}"
        except:
            m_label = "Autre"
        mois_map.setdefault(m_label, []).append(d)

    mode = st.sidebar.radio(f"Filtrer {label_prefix} par",
                            ["Tout", "Mois", "Dates"], horizontal=True, key=f"{key_prefix}_mode")
    if mode == "Tout":
        return []
    elif mode == "Mois":
        choix_mois = st.sidebar.multiselect(f"Mois {label_prefix}", sorted(mois_map.keys()), key=f"{key_prefix}_mois")
        if not choix_mois: return []
        return [d for m in choix_mois for d in mois_map[m]]
    else:
        all_dates = sorted(df[date_col].unique().tolist(),
                           key=lambda d: tuple(int(x) for x in str(d).split("/"))[::-1])
        return st.sidebar.multiselect(f"Dates {label_prefix}", all_dates, key=f"{key_prefix}_dates")

if jorf_df is not None:
    st.sidebar.markdown("**Jorf Lasfar**")
    sel_jorf = filtre_dates_sidebar(jorf_df, "Jorf", "jorf")
else:
    sel_jorf = []

if safi_df is not None:
    st.sidebar.markdown("**Safi**")
    sel_safi = filtre_dates_sidebar(safi_df, "Safi", "safi")
else:
    sel_safi = []

def appliquer_filtre(df, sel, col="Date"):
    if not sel: return df
    return df[df[col].isin(sel)]

# ─── CUMULS ──────────────────────────────────────────────────────────────────
cumul_jorf  = float(jorf_df["TOTAL Jorf"].sum()) if jorf_df is not None else 0.0
cumul_safi  = float(safi_df["TOTAL Safi"].sum()) if safi_df is not None else 0.0
cumul_total = cumul_jorf + cumul_safi

# ─── KPI CARDS ───────────────────────────────────────────────────────────────
st.markdown("### Cumul a Date — Toute la Periode")
c1, c2, c3 = st.columns(3)
with c1:
    sub1 = "Export Engrais + Camions + VL" if jorf_df is not None else "Fichier non charge"
    st.markdown(f"""<div class="kpi-card jorf">
        <div class="kpi-label">Total Jorf Lasfar</div>
        <div class="kpi-value">{fmt_number(cumul_jorf)}</div>
        <div class="kpi-sub">{sub1}</div></div>""", unsafe_allow_html=True)
with c2:
    sub2 = "TSP Export + TSP ML" if safi_df is not None else "Fichier non charge"
    st.markdown(f"""<div class="kpi-card safi">
        <div class="kpi-label">Total Safi</div>
        <div class="kpi-value">{fmt_number(cumul_safi)}</div>
        <div class="kpi-sub">{sub2}</div></div>""", unsafe_allow_html=True)
with c3:
    st.markdown(f"""<div class="kpi-card total">
        <div class="kpi-label">Total Jorf + Safi</div>
        <div class="kpi-value">{fmt_number(cumul_total)}</div>
        <div class="kpi-sub">Consolide toutes unites</div></div>""", unsafe_allow_html=True)

st.divider()

# ─── SECTION JORF ────────────────────────────────────────────────────────────
st.markdown('<div class="section-header jorf">Jorf Lasfar — Chargement Export</div>', unsafe_allow_html=True)

if jorf_df is not None:
    show_jorf = appliquer_filtre(jorf_df, sel_jorf)
    st.dataframe(show_jorf, use_container_width=True, hide_index=True,
        height=min(500, 45 + 35 * len(show_jorf)),
        column_config={
            "Date":           st.column_config.TextColumn("Date"),
            "Export Engrais": st.column_config.NumberColumn("Export Engrais", format="%d"),
            "Export Camions": st.column_config.NumberColumn("Export Camions", format="%d"),
            "VL Camions":     st.column_config.NumberColumn("VL Camions",     format="%d"),
            "TOTAL Jorf":     st.column_config.NumberColumn("TOTAL Jorf",     format="%d"),
        })
    copier_ligne_btn(show_jorf, "TOTAL Jorf", "Total Jorf", "copy_jorf")
    if len(show_jorf) > 1:
        st.line_chart(show_jorf.set_index("Date")["TOTAL Jorf"], color="#00843D")
else:
    st.info("Chargez le fichier Jorf dans la barre laterale.")

st.divider()

# ─── SECTION RADE ────────────────────────────────────────────────────────────
st.markdown('<div class="section-header rade">Rade Jorf Lasfar — Engrais en Attente d\'Accostage</div>', unsafe_allow_html=True)

if rade_df is not None:
    show_rade = appliquer_filtre(rade_df, sel_jorf)
    total_rade = pd.DataFrame([{
        "Date": "TOTAL GENERAL",
        "Engrais en attente": show_rade["Engrais en attente"].sum()
    }])
    display_rade = pd.concat([show_rade, total_rade], ignore_index=True)
    st.dataframe(display_rade, use_container_width=True, hide_index=True,
        height=min(500, 45 + 35 * len(display_rade)),
        column_config={
            "Date":               st.column_config.TextColumn("Date"),
            "Engrais en attente": st.column_config.NumberColumn("Engrais en Attente (Rade)", format="%d"),
        })
    copier_ligne_btn(show_rade, "Engrais en attente", "Rade", "copy_rade")
    if len(show_rade) > 1:
        st.line_chart(show_rade.set_index("Date")["Engrais en attente"], color="#6B3FA0")
elif file_jorf is not None:
    st.warning("Feuille 'Sit Navire' introuvable dans le fichier Jorf.")
else:
    st.info("Chargez le fichier Jorf pour voir les donnees Rade.")

st.divider()

# ─── SECTION SAFI ────────────────────────────────────────────────────────────
st.markdown('<div class="section-header safi">Safi — TSP Export & TSP ML</div>', unsafe_allow_html=True)

if safi_df is not None:
    show_safi = appliquer_filtre(safi_df, sel_safi).copy()
    display_safi = show_safi[["Date", "TSP Export", "TSP ML", "TOTAL Safi"]].copy()
    grand_total = pd.DataFrame([{"Date": "TOTAL GENERAL",
        "TSP Export": show_safi["TSP Export"].sum(),
        "TSP ML":     show_safi["TSP ML"].sum(),
        "TOTAL Safi": show_safi["TOTAL Safi"].sum()}])
    display_safi = pd.concat([display_safi, grand_total], ignore_index=True)
    st.dataframe(display_safi, use_container_width=True, hide_index=True,
        height=min(600, 45 + 35 * len(display_safi)),
        column_config={
            "Date":       st.column_config.TextColumn("Date"),
            "TSP Export": st.column_config.NumberColumn("TSP Export", format="%d"),
            "TSP ML":     st.column_config.NumberColumn("TSP ML",     format="%d"),
            "TOTAL Safi": st.column_config.NumberColumn("TOTAL Safi", format="%d"),
        })
    copier_ligne_btn(show_safi, "TOTAL Safi", "Total Safi", "copy_safi")
    if len(show_safi) > 1:
        st.line_chart(show_safi.set_index("Date")[["TSP Export", "TSP ML"]])
else:
    st.info("Chargez le fichier Safi dans la barre laterale.")

st.divider()

# ─── SECTION TOTAL ───────────────────────────────────────────────────────────
st.markdown('<div class="section-header total">Total Consolide — Jorf + Safi par Jour</div>', unsafe_allow_html=True)

if jorf_df is not None or safi_df is not None:
    jorf_filtered = appliquer_filtre(jorf_df, sel_jorf) if jorf_df is not None else None
    safi_filtered = appliquer_filtre(safi_df, sel_safi) if safi_df is not None else None

    j_day = jorf_filtered[["Date", "TOTAL Jorf"]].copy() if jorf_filtered is not None else pd.DataFrame(columns=["Date", "TOTAL Jorf"])
    s_day = safi_filtered[["Date", "TOTAL Safi"]].copy() if safi_filtered is not None else pd.DataFrame(columns=["Date", "TOTAL Safi"])

    if not j_day.empty and not s_day.empty:
        day_df = pd.merge(j_day, s_day, on="Date", how="outer").fillna(0)
    elif not j_day.empty:
        day_df = j_day.copy(); day_df["TOTAL Safi"] = 0.0
    else:
        day_df = s_day.copy(); day_df["TOTAL Jorf"] = 0.0

    day_df["TOTAL Jorf+Safi"] = day_df["TOTAL Jorf"] + day_df["TOTAL Safi"]

    def date_sort_key(d):
        try:
            parts = str(d).split("/")
            return (int(parts[2]), int(parts[1]), int(parts[0]))
        except:
            return (9999, 99, 99)

    day_df["_sort"] = day_df["Date"].apply(date_sort_key)
    day_df = day_df.sort_values("_sort").drop(columns=["_sort"]).reset_index(drop=True)

    total_row = pd.DataFrame([{"Date": "TOTAL GENERAL",
        "TOTAL Jorf":      day_df["TOTAL Jorf"].sum(),
        "TOTAL Safi":      day_df["TOTAL Safi"].sum(),
        "TOTAL Jorf+Safi": day_df["TOTAL Jorf+Safi"].sum()}])
    disp_day = pd.concat([day_df, total_row], ignore_index=True)

    st.dataframe(disp_day, use_container_width=True, hide_index=True,
        height=min(600, 45 + 35 * len(disp_day)),
        column_config={
            "Date":            st.column_config.TextColumn("Date"),
            "TOTAL Jorf":      st.column_config.NumberColumn("Total Jorf",      format="%d"),
            "TOTAL Safi":      st.column_config.NumberColumn("Total Safi",      format="%d"),
            "TOTAL Jorf+Safi": st.column_config.NumberColumn("Total Jorf+Safi", format="%d"),
        })
    copier_ligne_btn(disp_day, "TOTAL Jorf+Safi", "Total Jorf+Safi", "copy_total")

    st.markdown("#### Evolution mensuelle — Jorf vs Safi")
    chart_df = day_df.copy()
    chart_df["Mois"] = chart_df["Date"].apply(extract_mois_label)
    chart_df = chart_df[chart_df["Mois"] != "Inconnu"]
    mois_tot = chart_df.groupby("Mois")[["TOTAL Jorf", "TOTAL Safi"]].sum().reset_index()

    def mois_sort_key(m):
        noms = {"Jan":1,"Fev":2,"Mar":3,"Avr":4,"Mai":5,"Jun":6,
                "Jul":7,"Aou":8,"Sep":9,"Oct":10,"Nov":11,"Dec":12}
        try:
            parts = m.split()
            return (int(parts[1]), noms.get(parts[0], 99))
        except:
            return (9999, 99)

    mois_tot["_sort"] = mois_tot["Mois"].apply(mois_sort_key)
    mois_tot = mois_tot.sort_values("_sort").drop(columns=["_sort"]).reset_index(drop=True)
    mois_tot = mois_tot[(mois_tot["TOTAL Jorf"] > 0) | (mois_tot["TOTAL Safi"] > 0)]

    if len(mois_tot) > 0:
        st.bar_chart(mois_tot.set_index("Mois")[["TOTAL Jorf", "TOTAL Safi"]])
    else:
        st.info("Pas encore de donnees pour le graphique mensuel.")
else:
    st.info("Chargez au moins un fichier pour voir le total consolide.")


