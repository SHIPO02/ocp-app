import streamlit as st
import pandas as pd
import json
import google.generativeai as genai

# 1. Initialisation de l'IA (Utilise ta clé dans les secrets)
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model_ai = genai.GenerativeModel('gemini-1.5-flash')
except:
    st.error("⚠️ Clé API non configurée.")

# 2. Fonctions supports
def fmt(n): return f"{n:,.1f}".replace(",", " ")
def force_n(v):
    if pd.isna(v): return 0.
    try: return float(str(v).replace(" ", "").replace(",", "."))
    except: return 0.

def get_smart_mapping(df_columns, target_columns):
    prompt = f"Analyse ces colonnes : {df_columns}. Trouve les correspondances pour : {target_columns}. Réponds en JSON pur : {{'colonne_excel': 'nom_cible'}}"
    try:
        response = model_ai.generate_content(prompt)
        clean_json = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(clean_json)
    except: return {}

# 3. Logique de la page Ventes
if st.session_state.get("page") == "ventes":
    st.markdown("### 💰 Pipeline des Ventes — Pilotage Décades")

    f_v = st.file_uploader("Charger le fichier Pipeline", type=["xlsx", "xlsb"])
    
    if f_v:
        xl = pd.ExcelFile(f_v)
        # On force l'onglet January ou on laisse choisir
        onglet = st.selectbox("Choisir l'onglet", xl.sheet_names, index=0)
        df_raw = xl.parse(onglet)
        
        targets = ["Physical Month", "Status Planif", "D1", "D2", "D3"]
        
        with st.expander("🤖 IA : Mapping intelligent", expanded=True):
            mapping = get_smart_mapping(list(df_raw.columns), targets)
            final_map = st.data_editor(mapping, use_container_width=True)
            
            if st.button("Valider et Générer les Cartes"):
                df_v = df_raw.rename(columns=final_map)
                for d in ["D1", "D2", "D3"]:
                    if d in df_v.columns: df_v[d] = df_v[d].apply(force_n)
                st.session_state["ventes_df"] = df_v

    # --- AFFICHAGE DES CARTES (SÉCURISÉ) ---
    if st.session_state.get("ventes_df") is not None:
        df_m = st.session_state["ventes_df"]
        
        # Filtre par mois si la colonne existe
        if "Physical Month" in df_m.columns:
            mois_sel = st.selectbox("Mois d'analyse", df_m["Physical Month"].unique())
            df_m = df_m[df_m["Physical Month"] == mois_sel]

        st.markdown(f"**Situation — {mois_sel if 'Physical Month' in df_m.columns else 'Globale'}**")
        
        # Définition des catégories (Chiffres ou Mots-clés)
        # On utilise .str.contains pour attraper "1", "1.", ou "En cours"
        confs = [
            {"titre": "🚢 En cours", "color": "#00843D", "pattern": "1|en cours"},
            {"titre": "⚓ En Rade", "color": "#6B3FA0", "pattern": "2|rade"},
            {"titre": "📦 Nommé", "color": "#1565C0", "pattern": "3|nomme|chargé"}
        ]

        cols = st.columns(3) # Cette ligne est maintenant bien placée à l'intérieur du bloc IF
        
        for i, conf in enumerate(confs):
            if "Status Planif" in df_m.columns:
                # Filtrage flexible (Majuscules/Minuscules ignorées)
                mask = df_m["Status Planif"].astype(str).str.lower().str.contains(conf["pattern"], na=False)
                sub = df_m[mask]
                
                d1, d2, d3 = sub["D1"].sum(), sub["D2"].sum(), sub["D3"].sum()
                total = d1 + d2 + d3
                
                with cols[i]:
                    st.markdown(f"""
                    <div style="background:white; border-radius:10px; padding:15px; border-top:5px solid {conf['color']}; box-shadow:0 1px 3px rgba(0,0,0,0.1)">
                        <div style="font-weight:700; color:{conf['color']};">{conf['titre']}</div>
                        <div style="display:flex; justify-content:space-around; margin-top:10px; border-bottom:1px solid #EEE; padding-bottom:5px;">
                            <div style="text-align:center;"><div style="font-size:9px;color:gray;">D1</div><div style="font-weight:700;">{fmt(d1)}</div></div>
                            <div style="text-align:center;"><div style="font-size:9px;color:gray;">D2</div><div style="font-weight:700;">{fmt(d2)}</div></div>
                            <div style="text-align:center;"><div style="font-size:9px;color:gray;">D3</div><div style="font-weight:700;">{fmt(d3)}</div></div>
                        </div>
                        <div style="text-align:right; font-weight:800; color:{conf['color']}; margin-top:8px; font-size:18px;">
                            {fmt(total)} <span style="font-size:10px;">KT</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

        st.markdown("---")
        st.dataframe(df_m[["Physical Month", "Status Planif", "D1", "D2", "D3"]], use_container_width=True, hide_index=True)
