# ... (tes imports et ton CSS en haut) ...

# 1. Définir la page actuelle
page = st.session_state["page"]

# 2. Structure de contrôle des pages
if page == "accueil":
    st.markdown("### Page Accueil")
    # ... ton code accueil ...

elif page == "suivi":
    st.markdown("### Page Suivi")
    # ... ton code suivi ...

elif page == "ventes":  # <--- C'est ici que ton erreur se produisait
    st.markdown('<div class="topbar"><div class="tb-title">Pipeline des Ventes</div></div>', unsafe_allow_html=True)
    
    # --- ZONE D'IMPORTATION ---
    uc1, _ = st.columns([1, 2])
    with uc1:
        st.markdown('<div class="upload-zone">', unsafe_allow_html=True)
        f_v = st.file_uploader("Fichier Pipeline Ventes", type=["xlsx", "xlsb"], key="up_v")
        if f_v:
            df_raw = pd.read_excel(f_v)
            targets_v = ["Physical Month", "Status Planif", "D1", "D2", "D3"]
            
            with st.expander("🤖 IA : Détection Décades", expanded=True):
                mapping_v = get_smart_mapping(list(df_raw.columns), targets_v, "Ventes")
                final_map_v = st.data_editor(mapping_v, use_container_width=True)
                
                if st.button("Valider Pipeline", type="primary"):
                    df_v = df_raw.rename(columns=final_map_v)
                    for d in ["D1", "D2", "D3"]: 
                        if d in df_v.columns: df_v[d] = df_v[d].apply(force_n)
                    st.session_state["ventes_df"] = df_v
                    save_cache(VENTES_CACHE, {"df": df_v})
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # --- AFFICHAGE DES RÉSULTATS ---
    if st.session_state.get("ventes_df") is not None:
        df = st.session_state["ventes_df"]
        # Vérification des colonnes pour éviter le KeyError
        needed = ["Physical Month", "Status Planif", "D1", "D2", "D3"]
        if all(c in df.columns for c in needed):
            mois_sel = st.selectbox("Mois d'analyse", df["Physical Month"].unique())
            df_m = df[df["Physical Month"] == mois_sel]
            
            st.markdown(f'<div class="stitle orange">Situation Décades — {mois_sel}</div>', unsafe_allow_html=True)
            c1, c2, c3 = st.columns(3)
            confs = [(c3, "📦 Chargé", "blue", "0."), (c2, "🚢 En cours", "green", "1."), (c1, "⚓ En Rade", "purple", "2.")]
            
            for col, title, color, code in confs:
                sub = df_m[df_m["Status Planif"].astype(str).str.contains(code, na=False)]
                d1, d2, d3 = sub["D1"].sum(), sub["D2"].sum(), sub["D3"].sum()
                with col:
                    st.markdown(f'<div class="decade-wrap"><div style="font-weight:700;">{title}</div><div class="decade-grid"><div class="decade-block"><div class="decade-block-label">D1</div><div class="decade-block-val">{fmt(d1)}</div></div><div class="decade-block"><div class="decade-block-label">D2</div><div class="decade-block-val">{fmt(d2)}</div></div><div class="decade-block"><div class="decade-block-label">D3</div><div class="decade-block-val">{fmt(d3)}</div></div></div><div style="text-align:right;font-weight:800;color:var(--{color});margin-top:10px;">Total: {fmt(d1+d2+d3)} KT</div></div>', unsafe_allow_html=True)
        else:
            st.warning("Mapping incomplet dans le fichier Ventes.")

elif page == "stock":
    st.markdown("### Page Stock")
    # ... ton code stock ...
