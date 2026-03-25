import streamlit as st
import pandas as pd
import io, json
import google.generativeai as genai

# --- CONFIGURATION (Nécessite ta clé dans les secrets Streamlit) ---
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model_ai = genai.GenerativeModel('gemini-1.5-flash')
except:
    st.error("⚠️ Configurez GEMINI_API_KEY dans les Secrets pour tester l'IA.")

# --- FONCTIONS SUPPORTS ---
def fmt(n): return f"{n:,.1f}".replace(",", " ")

def force_n(v):
    if pd.isna(v): return 0.
    try: return float(str(v).replace(" ", "").replace("\xa0", "").replace(",", "."))
    except: return 0.

def get_smart_mapping(df_columns, target_columns, context=""):
    prompt = f"Analyse ces colonnes : {df_columns}. Trouve les correspondances pour : {target_columns}. Réponds UNIQUEMENT en JSON pur : {{'colonne_excel': 'nom_cible'}}"
    try:
        response = model_ai.generate_content(prompt)
        clean_json = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(clean_json)
    except: return {}

# --- DESIGN CSS (Minimal pour le test) ---
st.markdown("""
<style>
.decade-wrap { background:white; border:1px solid #E0E4EA; border-radius:10px; padding:15px; box-shadow:0 1px 3px rgba(0,0,0,0.07); margin-bottom:10px; }
.decade-grid { display:flex; gap:8px; margin-top:10px; }
.decade-block { flex:1; background:#F2F4F7; border-radius:6px; padding:8px; text-align:center; }
.decade-block-label { font-size:10px; font-weight:700; color:#4A5568; }
.decade-block-val { font-size:18px; font-weight:700; color:#12202E; }
.stitle { font-size:14px; font-weight:700; text-transform:uppercase; color:#4A5568; margin-top:20px; }
</style>
""", unsafe_allow_html=True)

# --- LOGIQUE DE LA PAGE ---
st.title("🧪 Test Module Pipeline Ventes")

# 1. IMPORT
st.markdown("### 1. Importation du fichier")
f_v = st.file_uploader("Charger un Excel Pipeline", type=["xlsx", "xlsb"])

if f_v:
    df_raw = pd.read_excel(f_v)
    targets_v = ["Physical Month", "Status Planif", "D1", "D2", "D3"]
    
    with st.expander("🤖 IA : Mapping des colonnes", expanded=True):
        mapping = get_smart_mapping(list(df_raw.columns), targets_v)
        final_map = st.data_editor(mapping, use_container_width=True)
        
        if st.button("Simuler l'analyse"):
            df_v = df_raw.rename(columns=final_map)
            for d in ["D1", "D2", "D3"]:
                if d in df_v.columns: df_v[d] = df_v[d].apply(force_n)
            st.session_state["test_df"] = df_v

# 2. AFFICHAGE (SI ANALYSÉ)
if st.session_state.get("test_df") is not None:
    df = st.session_state["test_df"]
    needed = ["Physical Month", "Status Planif", "D1", "D2", "D3"]
    
    if all(c in df.columns for c in needed):
        st.divider()
        # Filtre Mois
        mois_sel = st.selectbox("Sélectionner le Mois", df["Physical Month"].unique())
        df_m = df[df["Physical Month"] == mois_sel]
        
        # Cartes par Statut
        st.markdown(f"### Situation — {mois_sel} (KT)")
        c1, c2, c3 = st.columns(3)
        
        # Config des statuts (0, 1, 2)
        confs = [
            (c1, "⚓ En Rade", "#6B3FA0", "2. En rade"),
            (c2, "🚢 En cours", "#00843D", "1. En cours de chargement"),
            (c3, "📦 Chargé / Nommé", "#1565C0", "0. Chargé")
        ]
        
        for col, title, color, code in confs:
            sub = df_m[df_m["Status Planif"].astype(str).str.contains(code, na=False)]
            d1, d2, d3 = sub["D1"].sum(), sub["D2"].sum(), sub["D3"].sum()
            with col:
                st.markdown(f"""
                <div class="decade-wrap">
                    <div style="font-weight:700; color:{color};">{title}</div>
                    <div class="decade-grid">
                        <div class="decade-block"><div class="decade-block-label">D1</div><div class="decade-block-val">{fmt(d1)}</div></div>
                        <div class="decade-block"><div class="decade-block-label">D2</div><div class="decade-block-val">{fmt(d2)}</div></div>
                        <div class="decade-block"><div class="decade-block-label">D3</div><div class="decade-block-val">{fmt(d3)}</div></div>
                    </div>
                    <div style="text-align:right; font-weight:800; color:{color}; margin-top:10px;">Total: {fmt(d1+d2+d3)}</div>
                </div>""", unsafe_allow_html=True)
        
        st.markdown("### Tableau récapitulatif")
        st.dataframe(df_m[needed], use_container_width=True, hide_index=True)
    else:
        st.error(f"Colonnes manquantes : {[c for c in needed if c not in df.columns]}")
