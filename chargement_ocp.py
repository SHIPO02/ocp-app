import streamlit as st
import pandas as pd
import re
import os
import io
import pickle
import json
from datetime import datetime

st.set_page_config(page_title="OCP - Suivi chargement Manufacturing", layout="wide")

st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Barlow:wght@400;600;700&family=Barlow+Condensed:wght@600;700&display=swap');
        :root { --ocp-green: #00843D; --ocp-dark: #005C2A; --jorf-color: #00843D; --safi-color: #1A6FA8; --total-color: #C05A00; --rade-color: #6B3FA0; }
        html, body, [class*="css"] { font-family: 'Barlow', sans-serif; }
        .stApp { background-color: #F4F7F5; }
        h1, h2, h3 { color: var(--ocp-dark) !important; font-family: 'Barlow Condensed', sans-serif !important; }
        .kpi-card { border-radius: 12px; padding: 16px 18px; color: white; box-shadow: 0 4px 16px rgba(0,0,0,0.12); position: relative; overflow: hidden; min-height: 160px; height: 160px; display: flex; flex-direction: column; justify-content: space-between; box-sizing: border-box; }
        .kpi-card::before { content: ''; position: absolute; top: -20px; right: -20px; width: 80px; height: 80px; border-radius: 50%; background: rgba(255,255,255,0.1); }
        .kpi-card.jorf  { background: linear-gradient(135deg, #00843D, #005C2A); }
        .kpi-card.safi  { background: linear-gradient(135deg, #1A6FA8, #0D4A73); }
        .kpi-card.total { background: linear-gradient(135deg, #C05A00, #8A3F00); }
        .kpi-card.rade  { background: linear-gradient(135deg, #6B3FA0, #4A2A73); }
        .kpi-label { font-size: 11px; font-weight: 700; opacity: 0.9; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 4px; }
        .kpi-value { font-family: 'Barlow Condensed', sans-serif; font-size: 32px; font-weight: 700; line-height: 1.1; margin: 4px 0; word-break: break-word; }
        .kpi-sub   { font-size: 10px; opacity: 0.75; margin-top: 2px; line-height: 1.3; }
        .kpi-date  { font-size: 10px; opacity: 0.9; margin-top: 4px; font-weight: 600; letter-spacing: 0.3px; }
        .section-header { display: flex; align-items: center; gap: 10px; padding: 10px 16px; border-radius: 8px; margin: 20px 0 10px 0; font-family: 'Barlow Condensed', sans-serif; font-size: 20px; font-weight: 700; color: white; }
        .section-header.jorf  { background: var(--jorf-color); }
        .section-header.safi  { background: var(--safi-color); }
        .section-header.total { background: var(--total-color); }
        .section-header.rade  { background: var(--rade-color); }
        [data-testid="stSidebar"] { border-right: 3px solid var(--ocp-green); background: #FAFFF9; }
        hr { border-color: #D0E8D9 !important; }
        .saved-badge { display:inline-block; background:#00843D; color:white; border-radius:6px; padding:2px 10px; font-size:12px; font-weight:600; margin-left:8px; }
        .hist-item { background: white; border-left: 4px solid #00843D; border-radius: 6px; padding: 8px 12px; margin-bottom: 6px; font-size: 13px; }
        .hist-item.safi { border-left-color: #1A6FA8; }
    </style>
""", unsafe_allow_html=True)

# ─── PERSISTENCE ─────────────────────────────────────────────────────────────
CACHE_DIR    = ".ocp_cache"
JORF_CACHE   = os.path.join(CACHE_DIR, "jorf.pkl")
SAFI_CACHE   = os.path.join(CACHE_DIR, "safi.pkl")
HIST_JORF    = os.path.join(CACHE_DIR, "hist_jorf.json")
HIST_SAFI    = os.path.join(CACHE_DIR, "hist_safi.json")
HIST_FILES   = os.path.join(CACHE_DIR, "hist_files")
os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(HIST_FILES, exist_ok=True)

def save_cache(path, data: dict):
    with open(path, "wb") as f:
        pickle.dump(data, f)

def load_cache(path):
    if os.path.exists(path):
        try:
            with open(path, "rb") as f:
                return pickle.load(f)
        except Exception:
            pass
    return None

def clear_cache(path):
    if os.path.exists(path):
        os.remove(path)

# ─── HISTORIQUE ──────────────────────────────────────────────────────────────

def load_historique(hist_path):
    if os.path.exists(hist_path):
        try:
            with open(hist_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return []

def save_historique(hist_path, hist_list):
    with open(hist_path, "w", encoding="utf-8") as f:
        json.dump(hist_list, f, ensure_ascii=False, indent=2)

def add_to_historique(hist_path, filename, file_bytes, file_type):
    """Ajoute un fichier à l'historique et sauvegarde ses bytes sur disque."""
    hist = load_historique(hist_path)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = filename.replace(" ", "_")
    phys_path = os.path.join(HIST_FILES, f"{file_type}_{ts}_{safe_name}")
    with open(phys_path, "wb") as f:
        f.write(file_bytes)
    entry = {
        "filename": filename,
        "date_upload": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "path": phys_path,
        "type": file_type,
    }
    hist = [h for h in hist if not (h["filename"] == filename and h["date_upload"][:10] == entry["date_upload"][:10])]
    hist.insert(0, entry)
    hist = hist[:20]
    save_historique(hist_path, hist)
    return phys_path

def load_from_hist_entry(entry):
    """Charge les bytes d'un fichier depuis l'historique."""
    path = entry.get("path", "")
    if os.path.exists(path):
        with open(path, "rb") as f:
            return f.read()
    return None

# ─── DICTIONNAIRE MOIS ────────────────────────────────────────────────────────
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

def date_sort_key(d):
    try:
        parts = str(d).split("/")
        return (int(parts[2]), int(parts[1]), int(parts[0]))
    except:
        return (9999, 99, 99)

SKIP_KEYWORDS = ["total","recap","recapitulatif","annee","annuel","bilan","synthese","summary"]

def is_data_sheet(name):
    return not any(kw in name.strip().lower() for kw in SKIP_KEYWORDS)

def detect_engine(raw_bytes):
    for eng in ['openpyxl', 'pyxlsb', 'calamine']:
        try:
            pd.ExcelFile(io.BytesIO(raw_bytes), engine=eng)
            return eng
        except Exception:
            continue
    raise ValueError("Aucun engine ne peut lire ce fichier.")

def read_file_bytes(file):
    file.seek(0)
    raw = file.read()
    filename = getattr(file, 'name', '').lower().strip()
    if filename.endswith('.xlsb'):
        return raw, 'pyxlsb'
    if filename.endswith('.xlsm') or filename.endswith('.xlsx'):
        try:
            pd.ExcelFile(io.BytesIO(raw), engine='openpyxl')
            return raw, 'openpyxl'
        except Exception:
            pass
    if filename.endswith('.xls'):
        try:
            pd.ExcelFile(io.BytesIO(raw), engine='calamine')
            return raw, 'calamine'
        except Exception:
            pass
    return raw, detect_engine(raw)

def get_derniere_valeur(df, col_valeur, col_date="Date"):
    if df is None or df.empty:
        return 0.0, None
    tmp = df[df[col_valeur] > 0].copy()
    if tmp.empty:
        return 0.0, None
    tmp["_sort"] = tmp[col_date].apply(date_sort_key)
    tmp = tmp.sort_values("_sort")
    last = tmp.iloc[-1]
    return round(float(last[col_valeur]), 1), last[col_date]

# ─── PARSE FUNCTIONS ─────────────────────────────────────────────────────────

def parse_jorf(raw_bytes, engine):
    df_raw = pd.read_excel(io.BytesIO(raw_bytes), sheet_name='EXPORT', header=None, engine=engine)
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
    return pd.DataFrame(rows)

def parse_rade(raw_bytes, engine):
    df_rade = pd.read_excel(io.BytesIO(raw_bytes), sheet_name='Sit Navire', header=None, engine=engine)
    rows_rade = []
    for r in range(len(df_rade)):
        date_val = df_rade.iloc[r, 1]
        val      = df_rade.iloc[r, 3]
        if pd.isna(date_val) or pd.isna(val): continue
        s_date = str(date_val).strip()
        if s_date in ("", "nan", "Date"): continue
        date_label = date_val.strftime('%d/%m/%Y') if hasattr(date_val, 'strftime') else s_date
        rows_rade.append({"Date": date_label, "Engrais en attente": en_milliers(force_nombre(val))})
    return pd.DataFrame(rows_rade) if rows_rade else None

def parse_safi(raw_bytes, engine):
    xl = pd.ExcelFile(io.BytesIO(raw_bytes), engine=engine)
    COL_JOUR = 1; COL_TSP_EXP = 31; COL_TSP_ML = 32; START_ROW = 6

    def normaliser(s):
        accents = {"é":"e","è":"e","ê":"e","ë":"e","à":"a","â":"a","ù":"u",
                   "û":"u","ô":"o","î":"i","ï":"i","ç":"c","ü":"u","ö":"o"}
        s = s.lower()
        for a, b in accents.items():
            s = s.replace(a, b)
        return s

    def parse_mois_annee(sheet_name):
        mois_map  = {"jan":1,"fev":2,"mar":3,"avr":4,"mai":5,"jun":6,"jui":6,"jul":7,"aou":8,"sep":9,"oct":10,"nov":11,"dec":12}
        mois_long = {"janvier":1,"fevrier":2,"mars":3,"avril":4,"mai":5,"juin":6,"juillet":7,"aout":8,"septembre":9,"octobre":10,"novembre":11,"decembre":12}
        parts = sheet_name.strip().split()
        mois_num = None; annee = None
        for p in parts:
            p_norm = normaliser(p)
            if p_norm[:3] in mois_map: mois_num = mois_map[p_norm[:3]]
            if p_norm in mois_long:    mois_num = mois_long[p_norm]
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
        dfs = pd.read_excel(io.BytesIO(raw_bytes), sheet_name=sheet, header=None, engine=engine)
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
    return pd.DataFrame(rows) if rows else None

# ─── FONCTION CHARGEMENT DEPUIS BYTES ────────────────────────────────────────

def charger_jorf_depuis_bytes(raw_bytes, filename):
    """Parse et sauvegarde un fichier Jorf depuis ses bytes bruts."""
    fake_file = io.BytesIO(raw_bytes)
    fake_file.name = filename
    raw, engine = read_file_bytes(fake_file)
    jorf_df_new = parse_jorf(raw, engine)
    rade_df_new = None
    try:
        rade_df_new = parse_rade(raw, engine)
    except:
        pass
    st.session_state["jorf_df"]   = jorf_df_new
    st.session_state["rade_df"]   = rade_df_new
    st.session_state["jorf_name"] = filename
    save_cache(JORF_CACHE, {"jorf_df": jorf_df_new, "rade_df": rade_df_new, "filename": filename})
    return jorf_df_new

def charger_safi_depuis_bytes(raw_bytes, filename):
    """Parse et sauvegarde un fichier Safi depuis ses bytes bruts."""
    fake_file = io.BytesIO(raw_bytes)
    fake_file.name = filename
    raw, engine = read_file_bytes(fake_file)
    safi_df_new = parse_safi(raw, engine)
    st.session_state["safi_df"]   = safi_df_new
    st.session_state["safi_name"] = filename
    save_cache(SAFI_CACHE, {"safi_df": safi_df_new, "filename": filename})
    return safi_df_new

# ─── HEADER ──────────────────────────────────────────────────────────────────
col_logo, col_title = st.columns([1, 5])
with col_logo:
    if os.path.exists("logo_ocp.png"):
        st.image("logo_ocp.png", width=110)
    else:
        st.markdown("<div style='font-size:34px;font-weight:900;color:#00843D;font-family:Barlow Condensed,sans-serif;'>OCP</div>", unsafe_allow_html=True)
with col_title:
    st.title("Suivi chargement Manufacturing")
    st.markdown("##### Jorf Lasfar & Safi")

st.divider()

# ─── SIDEBAR ─────────────────────────────────────────────────────────────────
st.sidebar.header("Chargement des fichiers")
EXCEL_TYPES = ["xlsx", "xls", "xlsm", "xlsb"]

# Load cached data into session_state on first run
if "jorf_loaded" not in st.session_state:
    cached = load_cache(JORF_CACHE)
    if cached:
        st.session_state["jorf_df"]   = cached.get("jorf_df")
        st.session_state["rade_df"]   = cached.get("rade_df")
        st.session_state["jorf_name"] = cached.get("filename", "")
    st.session_state["jorf_loaded"] = True

if "safi_loaded" not in st.session_state:
    cached = load_cache(SAFI_CACHE)
    if cached:
        st.session_state["safi_df"]   = cached.get("safi_df")
        st.session_state["safi_name"] = cached.get("filename", "")
    st.session_state["safi_loaded"] = True

# ── File uploaders ─────────────────────────────────────────────────────────
file_jorf = st.sidebar.file_uploader("📂 Fichier Jorf", type=EXCEL_TYPES, key="jorf_uploader")
file_safi = st.sidebar.file_uploader("📂 Fichier Safi", type=EXCEL_TYPES, key="safi_uploader")

jorf_name_saved = st.session_state.get("jorf_name", "")
safi_name_saved = st.session_state.get("safi_name", "")

if not file_jorf and jorf_name_saved:
    st.sidebar.success(f"✅ Jorf actif : **{jorf_name_saved}**")

if not file_safi and safi_name_saved:
    st.sidebar.success(f"✅ Safi actif : **{safi_name_saved}**")

# ─── PARSE & SAVE JORF  (auto-remplace l'ancien) ─────────────────────────────
if file_jorf:
    try:
        jorf_bytes, engine = read_file_bytes(file_jorf)
        jorf_df_new  = parse_jorf(jorf_bytes, engine)
        rade_df_new  = None
        try:
            rade_df_new = parse_rade(jorf_bytes, engine)
        except:
            pass
        clear_cache(JORF_CACHE)
        st.session_state["jorf_df"]   = jorf_df_new
        st.session_state["rade_df"]   = rade_df_new
        st.session_state["jorf_name"] = file_jorf.name
        save_cache(JORF_CACHE, {"jorf_df": jorf_df_new, "rade_df": rade_df_new, "filename": file_jorf.name})
        file_jorf.seek(0)
        add_to_historique(HIST_JORF, file_jorf.name, file_jorf.read(), "jorf")
        st.sidebar.success(f"✅ Jorf chargé et sauvegardé !")
    except Exception as e:
        st.sidebar.error(f"Erreur Jorf : {e}")

# ─── PARSE & SAVE SAFI  (auto-remplace l'ancien) ─────────────────────────────
if file_safi:
    try:
        safi_bytes, engine = read_file_bytes(file_safi)
        safi_df_new = parse_safi(safi_bytes, engine)
        clear_cache(SAFI_CACHE)
        st.session_state["safi_df"]   = safi_df_new
        st.session_state["safi_name"] = file_safi.name
        save_cache(SAFI_CACHE, {"safi_df": safi_df_new, "filename": file_safi.name})
        file_safi.seek(0)
        add_to_historique(HIST_SAFI, file_safi.name, file_safi.read(), "safi")
        if safi_df_new is None:
            st.sidebar.warning("Safi : aucune feuille mensuelle détectée.")
        else:
            st.sidebar.success(f"✅ Safi chargé et sauvegardé !")
    except Exception as e:
        st.sidebar.error(f"Erreur Safi : {e}")

# ─── HISTORIQUE SIDEBAR ───────────────────────────────────────────────────────
st.sidebar.divider()
st.sidebar.markdown("### 🕓 Historique des fichiers")

hist_jorf = load_historique(HIST_JORF)
hist_safi = load_historique(HIST_SAFI)

if hist_jorf:
    with st.sidebar.expander(f"📋 Jorf ({len(hist_jorf)} fichier(s))", expanded=False):
        for i, entry in enumerate(hist_jorf):
            is_active = entry["filename"] == st.session_state.get("jorf_name", "")
            col_h1, col_h2 = st.columns([3, 1])
            with col_h1:
                st.markdown(f"{'🟢 ' if is_active else '⬜ '}{entry['filename']}  \n`{entry['date_upload']}`")
            with col_h2:
                if not is_active:
                    if st.button("↩️", key=f"reload_jorf_{i}", help=f"Recharger {entry['filename']}"):
                        raw = load_from_hist_entry(entry)
                        if raw:
                            try:
                                charger_jorf_depuis_bytes(raw, entry["filename"])
                                st.success(f"✅ {entry['filename']} rechargé !")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erreur : {e}")
                        else:
                            st.error("Fichier introuvable dans l'historique.")
                else:
                    st.markdown("✅")
else:
    st.sidebar.caption("Aucun fichier Jorf dans l'historique.")

if hist_safi:
    with st.sidebar.expander(f"📋 Safi ({len(hist_safi)} fichier(s))", expanded=False):
        for i, entry in enumerate(hist_safi):
            is_active = entry["filename"] == st.session_state.get("safi_name", "")
            col_h1, col_h2 = st.columns([3, 1])
            with col_h1:
                st.markdown(f"{'🟢 ' if is_active else '⬜ '}{entry['filename']}  \n`{entry['date_upload']}`")
            with col_h2:
                if not is_active:
                    if st.button("↩️", key=f"reload_safi_{i}", help=f"Recharger {entry['filename']}"):
                        raw = load_from_hist_entry(entry)
                        if raw:
                            try:
                                charger_safi_depuis_bytes(raw, entry["filename"])
                                st.success(f"✅ {entry['filename']} rechargé !")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erreur : {e}")
                        else:
                            st.error("Fichier introuvable dans l'historique.")
                else:
                    st.markdown("✅")
else:
    st.sidebar.caption("Aucun fichier Safi dans l'historique.")

# ─── Retrieve from session_state ─────────────────────────────────────────────
jorf_df = st.session_state.get("jorf_df", None)
rade_df = st.session_state.get("rade_df", None)
safi_df = st.session_state.get("safi_df", None)

# ─── FILTRES ─────────────────────────────────────────────────────────────────
st.sidebar.divider()
st.sidebar.header("Filtrage")

def filtre_dates_sidebar(df, label_prefix, key_prefix, date_col="Date"):
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
    for annee in annees_presentes:
        for num, nom in NOMS_MOIS.items():
            m_label = f"{nom} {annee}"
            if m_label not in mois_map:
                mois_map[m_label] = []
    mois_tries = sorted(mois_map.keys(), key=mois_sort_key)
    options_finales = []
    for m in mois_tries:
        if mois_map[m]: options_finales.append(m)
        else:           options_finales.append(f"{m} —")
    mode = st.sidebar.radio(f"Filtrer {label_prefix} par",
                            ["Tout", "Mois", "Dates"], horizontal=True, key=f"{key_prefix}_mode")
    if mode == "Tout":
        return [], "Toute la periode"
    elif mode == "Mois":
        choix_mois = st.sidebar.multiselect(
            f"Mois {label_prefix} (— = aucune donnee)",
            options=options_finales, default=[], key=f"{key_prefix}_mois")
        if not choix_mois: return [], "Toute la periode"
        dates_sel = []; labels_sel = []
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

# ─── CUMULS ──────────────────────────────────────────────────────────────────
jorf_kpi = appliquer_filtre(jorf_df, sel_jorf) if jorf_df is not None else None
safi_kpi = appliquer_filtre(safi_df, sel_safi) if safi_df is not None else None
rade_kpi = appliquer_filtre(rade_df, sel_jorf) if rade_df is not None else None

cumul_jorf  = round(float(jorf_kpi["TOTAL Jorf"].sum()), 1) if jorf_kpi is not None else 0.0
cumul_safi  = round(float(safi_kpi["TOTAL Safi"].sum()), 1) if safi_kpi is not None else 0.0
cumul_total = round(cumul_jorf + cumul_safi, 1)

rade_j_val, rade_j_date = get_derniere_valeur(rade_kpi, "Engrais en attente") if rade_kpi is not None else (0.0, None)
rade_s_val, rade_s_date = get_derniere_valeur(safi_kpi, "TSP ML") if safi_kpi is not None else (0.0, None)

periode_label = f"Filtre : {label_jorf} / {label_safi}" if (sel_jorf or sel_safi) else "Toute la Periode"

# ─── KPI CARDS ───────────────────────────────────────────────────────────────
st.markdown(f"### Cumul a Date — {periode_label}")
k1, k2, k3, k4 = st.columns(4)
with k1:
    sub1 = "Export Engrais + Camions + VL" if jorf_df is not None else "Fichier non charge"
    st.markdown(f"""<div class="kpi-card jorf"><div class="kpi-label">Total Jorf</div><div class="kpi-value">{fmt_number(cumul_jorf)}</div><div class="kpi-sub">{sub1}</div></div>""", unsafe_allow_html=True)
with k2:
    if rade_df is not None and rade_j_date is not None:
        st.markdown(f"""<div class="kpi-card rade"><div class="kpi-label">Rade Jorf</div><div class="kpi-value">{fmt_number(rade_j_val)}</div><div class="kpi-sub">Engrais en attente</div><div class="kpi-date">📅 Derniere valeur : {rade_j_date}</div></div>""", unsafe_allow_html=True)
    else:
        st.markdown(f"""<div class="kpi-card rade"><div class="kpi-label">Rade Jorf</div><div class="kpi-value">—</div><div class="kpi-sub">Fichier non charge</div></div>""", unsafe_allow_html=True)
with k3:
    sub2 = "Export Engrais + VL Camions" if safi_df is not None else "Fichier non charge"
    st.markdown(f"""<div class="kpi-card safi"><div class="kpi-label">Total Safi</div><div class="kpi-value">{fmt_number(cumul_safi)}</div><div class="kpi-sub">{sub2}</div></div>""", unsafe_allow_html=True)
with k4:
    st.markdown(f"""<div class="kpi-card total"><div class="kpi-label">Total Jorf + Safi</div><div class="kpi-value">{fmt_number(cumul_total)}</div><div class="kpi-sub">Consolide toutes unites</div></div>""", unsafe_allow_html=True)

st.divider()

# ─── TABLE UNIFIEE ────────────────────────────────────────────────────────────
st.markdown('<div class="section-header total">Tableau Consolide — Toutes Donnees par Jour (KT)</div>', unsafe_allow_html=True)

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
  <div class="grp-rade">RADE JORF</div>
  <div class="grp-total">TOTAL</div>
</div>
""", unsafe_allow_html=True)

any_data = jorf_df is not None or safi_df is not None or rade_df is not None

if any_data:
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
        if jorf_f is not None:
            r = jorf_f[jorf_f["Date"] == d]
            row["J_Engrais"] = round(r["Export Engrais"].sum(), 1) if not r.empty else 0.0
            row["J_Camions"] = round(r["Export Camions"].sum(), 1) if not r.empty else 0.0
            row["J_VL"]      = round(r["VL Camions"].sum(), 1)     if not r.empty else 0.0
        if safi_f is not None:
            r = safi_f[safi_f["Date"] == d]
            row["S_Engrais"] = round(r["TSP Export"].sum(), 1) if not r.empty else 0.0
            row["S_VL"]      = round(r["TSP ML"].sum(), 1)     if not r.empty else 0.0
        j_tot = round(row.get("J_Engrais",0.0)+row.get("J_Camions",0.0)+row.get("J_VL",0.0), 1) if jorf_f is not None else 0.0
        s_tot = round(row.get("S_Engrais",0.0)+row.get("S_VL",0.0), 1) if safi_f is not None else 0.0
        if jorf_f is not None: row["J_TOTAL"] = j_tot
        if safi_f is not None: row["S_TOTAL"] = s_tot
        row["TOTAL"] = round(j_tot + s_tot, 1)
        if rade_f is not None:
            r = rade_f[rade_f["Date"] == d]
            row["RADE_J"] = round(r["Engrais en attente"].sum(), 1) if not r.empty else 0.0
        unified_rows.append(row)

    unified_df = pd.DataFrame(unified_rows)

    col_order = ["Date"]
    if jorf_f is not None: col_order += ["J_Engrais", "J_Camions", "J_VL"]
    if safi_f is not None: col_order += ["S_Engrais", "S_VL"]
    if jorf_f is not None: col_order += ["J_TOTAL"]
    if safi_f is not None: col_order += ["S_TOTAL"]
    col_order += ["TOTAL"]
    if rade_f is not None: col_order += ["RADE_J"]
    col_order = [c for c in col_order if c in unified_df.columns]
    unified_df = unified_df[col_order]

    rade_cols = {"RADE_J"}
    total_row = {"Date": "TOTAL GENERAL"}
    for col in unified_df.columns:
        if col == "Date": continue
        elif col in rade_cols: total_row[col] = None
        else: total_row[col] = round(unified_df[col].sum(), 1)
    disp_unified = pd.concat([unified_df, pd.DataFrame([total_row])], ignore_index=True)

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
        col_cfg["RADE_J"] = st.column_config.NumberColumn("Rade Jorf", format="%.1f")

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

    g_left, g_right = st.columns(2)

    with g_left:
        st.markdown('<div class="section-header rade">Rade Jorf — Engrais en Attente</div>', unsafe_allow_html=True)
        if rade_f is not None and "RADE_J" in unified_df.columns and len(unified_df) > 1:
            rade_chart = unified_df[unified_df["RADE_J"] > 0].copy()
            if len(rade_chart) > 0:
                st.bar_chart(rade_chart.set_index("Date")[["RADE_J"]].rename(columns={"RADE_J": "Rade Jorf"}), color="#6B3FA0")
            else:
                st.info("Pas de donnees Rade disponibles.")
        else:
            st.info("Chargez le fichier Jorf pour voir la Rade.")

    with g_right:
        cols_line = [c for c in ["J_TOTAL", "S_TOTAL", "TOTAL"] if c in unified_df.columns]
        if cols_line and len(unified_df) > 1:
            line_df = unified_df.copy()
            line_df["Mois"] = line_df["Date"].apply(extract_mois_label)
            line_df = line_df[line_df["Mois"] != "Inconnu"]
            mois_line = line_df.groupby("Mois")[cols_line].sum().reset_index()
            mois_line["_sort"] = mois_line["Mois"].apply(mois_sort_key)
            mois_line = mois_line.sort_values("_sort").drop(columns=["_sort"]).reset_index(drop=True)
            mois_line = mois_line.rename(columns={"J_TOTAL":"Total Jorf","S_TOTAL":"Total Safi","TOTAL":"Total Jorf+Safi"}).set_index("Mois")

            st.markdown('<div class="section-header jorf" style="font-size:15px;padding:7px 14px;">Total Jorf vs Total Safi par Jour</div>', unsafe_allow_html=True)
            day_js_cols = [c for c in ["J_TOTAL", "S_TOTAL"] if c in unified_df.columns]
            if day_js_cols and len(unified_df) > 1:
                day_js = unified_df.set_index("Date")[day_js_cols].rename(columns={"J_TOTAL": "Total Jorf", "S_TOTAL": "Total Safi"})
                c_js = ["#00843D" if c == "Total Jorf" else "#1A6FA8" for c in day_js.columns]
                st.line_chart(day_js, color=c_js)

            st.markdown('<div class="section-header total" style="font-size:15px;padding:7px 14px;">Total Jorf+Safi par Mois</div>', unsafe_allow_html=True)
            if "Total Jorf+Safi" in mois_line.columns and len(mois_line) > 0:
                st.line_chart(mois_line[["Total Jorf+Safi"]], color="#C05A00")
        else:
            st.info("Chargez les fichiers pour voir le graphique.")
else:
    st.info("Chargez au moins un fichier pour voir le tableau consolide.")
