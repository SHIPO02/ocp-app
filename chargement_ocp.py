import streamlit as st
import pandas as pd
import json
import google.generativeai as genai

# 1. CONFIGURATION & SESSION (Indispensable pour éviter l'écran blanc)
st.set_page_config(page_title="OCP Manufacturing", layout="wide")

if "page" not in st.session_state:
    st.session_state["page"] = "accueil"
if "ventes_df" not in st.session_state:
    st.session_state["ventes_df"] = None

# 2. CONFIGURATION IA
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model_ai = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error("Erreur de configuration API. Vérifiez vos secrets.")

# 3. FONCTIONS SUPPORTS
def fmt(n): return f"{n:,.1f}".replace(",", " ")
def force_n(v):
    if pd.isna(v): return 0.
    try: return float(str(v).replace(" ", "").replace(",", "."))
    except: return 0.

def get_smart_mapping(df_columns, target_columns):
    prompt = f"Mappe ces colonnes Excel : {df_columns} vers {target_columns}. Réponds en JSON pur."
    try:
        response = model_ai.generate_content(prompt)
        txt = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(txt)
    except: return {}

# 4. NAVIGATION SIDEBAR
with st.sidebar:
    st.title("OCP DASHBOARD")
    if st.button("Accueil"): st.session_state.page = "accueil"; st.rerun()
    if st.button("Pipeline Ventes"): st.session_state.page = "ventes"; st.rerun()

# 5. LOGIQUE DE LA PAGE VENTES
if st.session_state.page == "ventes":
    st.header("💰 Pipeline des Ventes")
    
    f = st.file_uploader("Charger Pipeline", type=["xlsx", "xlsb"])
    if f:
        xl = pd.ExcelFile(f)
        onglet = st.selectbox("Choisir l'onglet", xl.sheet_names)
        df_raw = xl.parse(onglet)
        
        targets = ["Physical Month", "Status Planif", "D1", "D2", "D3"]
        
        with st.expander("🤖 IA : Mapping automatique", expanded=True):
            mapping = get_smart_mapping(list(df_raw.columns), targets)
            final_map = st.data_editor(mapping, use_container_width=True)
            
            if st.button("Valider et Générer les Cartes"):
                df_v = df_raw.rename(columns=final_map)
                for d in ["D1", "D2", "D3"]:
                    if d in df_v.columns: df_v[d] = df_v[d].apply(force_n)
                st.session_state["ventes_df"] = df_v
                st.rerun()

    # --- AFFICHAGE DES CARTES ET DE LA TABLE ---
    if st.session_state.ventes_df is not None:
        df = st.session_state.ventes_df
        
        # Filtre Mois
        if "Physical Month" in df.columns:
            m_list = df["Physical Month"].dropna().unique()
            sel_m = st.selectbox("Mois", m_list)
            df_m = df[df["Physical Month"] == sel_m]
        else:
            df_m = df

        # Cartes par Statut
        st.subheader(f"Situation — {sel_m if 'Physical Month' in df.columns else ''}")
        c1, c2, c3 = st.columns(3)
        
        # On définit les patterns pour 1, 2, 3 ou les mots clés
        confs = [
            (c1, "🚢 En cours", "#00843D", "1|en cours"),
            (c2, "⚓ En Rade", "#6B3FA0", "2|rade"),
            (c3, "📦 Nommé", "#1565C0", "3|nomme|chargé")
        ]

        for col, title, color, pattern in confs:
            if "Status Planif" in df_m.columns:
                mask = df_m["Status Planif"].astype(str).str.lower().str.contains(pattern, na=False)
                sub = df_m[mask]
                d1, d2, d3 = sub["D1"].sum(), sub["D2"].sum(), sub["D3"].sum()
                
                with col:
                    st.markdown(f"""
                    <div style="background:white; border-radius:10px; padding:15px; border-top:5px solid {color}; box-shadow:0 2px 4px rgba(0,0,0,0.05)">
                        <div style="font-weight:700; color:{color};">{title}</div>
                        <div style="display:flex; justify-content:space-between; margin-top:10px;">
                            <div style="text-align:center;"><div style="font-size:10px;color:gray;">D1</div><b>{fmt(d1)}</b></div>
                            <div style="text-align:center;"><div style="font-size:10px;color:gray;">D2</div><b>{fmt(d2)}</b></div>
                            <div style="text-align:center;"><div style="font-size:10px;color:gray;">D3</div><b>{fmt(d3)}</b></div>
                        </div>
                        <div style="text-align:right; font-weight:800; color:{color}; margin-top:10px; font-size:18px;">{fmt(d1+d2+d3)} KT</div>
                    </div>
                    """, unsafe_allow_html=True)

        st.markdown("### 📋 TABLE DE DÉTAIL")
        # On affiche uniquement les colonnes importantes pour plus de clarté comme ton image 1
        cols_to_show = [c for c in ["Physical Month", "D1", "D2", "D3", "Status Planif"] if c in df_m.columns]
        st.dataframe(df_m[cols_to_show], use_container_width=True, hide_index=True)

elif st.session_state.page == "accueil":
    st.title("Accueil")
    st.write("Bienvenue sur le Dashboard. Sélectionnez 'Pipeline Ventes' dans le menu.")
