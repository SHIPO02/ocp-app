# ══════════════════════════════════════════════════════════════════════════════
# PAGE : PIPELINE DES VENTES (IA & DÉCADES)
# ══════════════════════════════════════════════════════════════════════════════
elif page == "ventes":
    st.markdown('<div class="topbar"><div class="tb-title">Pipeline des Ventes — Situation Décades</div></div>', unsafe_allow_html=True)
    
    # 1. ZONE D'IMPORTATION INTELLIGENTE
    uc1, _ = st.columns([1, 2])
    with uc1:
        st.markdown('<div class="upload-zone">', unsafe_allow_html=True)
        f_v = st.file_uploader("Importer Pipeline Ventes", type=["xlsx", "xlsb"], key="up_v", label_visibility="collapsed")
        
        if f_v:
            df_raw = pd.read_excel(f_v)
            # On définit les 5 colonnes que l'IA doit retrouver dans l'Excel
            targets_v = ["Physical Month", "Status Planif", "D1", "D2", "D3"]
            
            with st.expander("🤖 IA : Détection des volumes décades", expanded=True):
                # Appel à la fonction LLM pour trouver les colonnes
                mapping_v = get_smart_mapping(list(df_raw.columns), targets_v, "Ventes")
                # Affiche le résultat pour validation/correction manuelle si besoin
                final_map_v = st.data_editor(mapping_v, use_container_width=True)
                
                if st.button("Valider et Calculer", type="primary"):
                    df_v = df_raw.rename(columns=final_map_v)
                    # Conversion numérique forcée pour D1, D2, D3
                    for d in ["D1", "D2", "D3"]: 
                        if d in df_v.columns: 
                            df_v[d] = df_v[d].apply(force_n)
                    
                    st.session_state["ventes_df"] = df_v
                    save_cache(VENTES_CACHE, {"df": df_v})
                    st.success("✅ Pipeline importé !")
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # 2. AFFICHAGE DES RÉSULTATS (Cartes par Statut)
    if st.session_state.get("ventes_df") is not None:
        df = st.session_state["ventes_df"]
        
        # Vérification de sécurité pour éviter les crashs (KeyError)
        needed = ["Physical Month", "Status Planif", "D1", "D2", "D3"]
        if all(c in df.columns for c in needed):
            # Filtre par mois
            mois_sel = st.selectbox("Mois d'analyse", df["Physical Month"].unique())
            df_m = df[df["Physical Month"] == mois_sel]
            
            st.markdown(f'<div class="stitle orange">Situation des décades — {mois_sel}</div>', unsafe_allow_html=True)
            
            # Disposition en 3 colonnes pour tes 3 statuts
            c1, c2, c3 = st.columns(3)
            # Configuration : (Colonne Streamlit, Titre, Couleur CSS, Code Statut Excel)
            confs = [
                (c3, "📦 Chargé / Nommé", "blue", "0."),
                (c2, "🚢 En cours", "green", "1."),
                (c1, "⚓ En Rade", "purple", "2.")
            ]
            
            for col, title, color, code in confs:
                # Filtrage sur le code statut (0., 1. ou 2.)
                sub = df_m[df_m["Status Planif"].astype(str).str.contains(code, na=False)]
                d1, d2, d3 = sub["D1"].sum(), sub["D2"].sum(), sub["D3"].sum()
                
                with col:
                    st.markdown(f"""
                    <div class="decade-wrap">
                        <div style="font-weight:700; color:var(--text); margin-bottom:10px;">{title}</div>
                        <div class="decade-grid">
                            <div class="decade-block">
                                <div class="decade-block-label">D1</div>
                                <div class="decade-block-val">{fmt(d1)}</div>
                            </div>
                            <div class="decade-block">
                                <div class="decade-block-label">D2</div>
                                <div class="decade-block-val">{fmt(d2)}</div>
                            </div>
                            <div class="decade-block">
                                <div class="decade-block-label">D3</div>
                                <div class="decade-block-val">{fmt(d3)}</div>
                            </div>
                        </div>
                        <div style="text-align:right; font-weight:800; color:var(--{color}); margin-top:10px; font-size:16px;">
                            Total: {fmt(d1+d2+d3)} KT
                        </div>
                    </div>""", unsafe_allow_html=True)
            
            st.markdown('<div style="margin-top:20px"></div>', unsafe_allow_html=True)
            st.dataframe(df_m[needed], use_container_width=True, hide_index=True)
        else:
            missing = [c for c in needed if c not in df.columns]
            st.warning(f"⚠️ Mapping incomplet. Colonnes manquantes : {', '.join(missing)}. Merci de corriger dans le tableau IA.")
    else:
        # Message si vide
        st.markdown('<div class="ph-card"><h2>Pipeline des Ventes</h2><p>Chargez un fichier Excel pour générer les cartes de décades par statut.</p></div>', unsafe_allow_html=True)
