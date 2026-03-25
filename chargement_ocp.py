# --- AFFICHAGE DES RÉSULTATS ---
if st.session_state.ventes_df is not None:
    df = st.session_state.ventes_df
    
    # 1. Filtre Mois
    if "Physical Month" in df.columns:
        mois_sel = st.selectbox("Mois", df["Physical Month"].dropna().unique())
        df_m = df[df["Physical Month"] == mois_sel]
    else:
        df_m = df
        mois_sel = "Toutes périodes"

    # 2. GÉNÉRATION DES CARDS (Juste au-dessus de la table)
    st.markdown(f"### 📊 Situation — {mois_sel}")
    c1, c2, c3 = st.columns(3)
    
    # On définit les règles pour les 3 statuts selon ton Excel
    # Le pattern cherche les chiffres 1, 2 ou 0/3 (ou les mots clés)
    confs = [
        (c1, "🚢 En cours", "#00843D", "1.|en cours"),
        (c2, "⚓ En Rade", "#6B3FA0", "2.|rade"),
        (c3, "📦 Nommé", "#1565C0", "0.|3.|nomme|charge")
    ]

    for col, title, color, pattern in confs:
        if "Status Planif" in df_m.columns:
            # On filtre les lignes correspondant au statut
            mask = df_m["Status Planif"].astype(str).str.lower().str.contains(pattern, na=False)
            sub = df_m[mask]
            
            # Sommes D1, D2, D3 pour ce statut
            d1, d2, d3 = sub["D1"].sum(), sub["D2"].sum(), sub["D3"].sum()
            total = d1 + d2 + d3
            
            with col:
                st.markdown(f"""
                <div style="background:white; border-radius:10px; padding:15px; border-top:5px solid {color}; box-shadow:0 2px 4px rgba(0,0,0,0.05); margin-bottom:20px;">
                    <div style="font-weight:700; color:{color}; font-size:14px;">{title}</div>
                    <div style="display:flex; justify-content:space-between; margin-top:10px; border-bottom:1px solid #EEE; padding-bottom:8px;">
                        <div style="text-align:center;"><div style="font-size:10px;color:gray;">D1</div><b style="font-size:14px;">{fmt(d1)}</b></div>
                        <div style="text-align:center;"><div style="font-size:10px;color:gray;">D2</div><b style="font-size:14px;">{fmt(d2)}</b></div>
                        <div style="text-align:center;"><div style="font-size:10px;color:gray;">D3</div><b style="font-size:14px;">{fmt(d3)}</b></div>
                    </div>
                    <div style="text-align:right; font-weight:800; color:{color}; margin-top:8px; font-size:18px;">
                        {fmt(total)} <span style="font-size:10px;">KT</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # 3. TABLE DE DÉTAIL (Incluant Status Planif)
    st.markdown("### 📋 TABLE DE DÉTAIL")
    # On affiche les 5 colonnes demandées
    cols_disp = [c for c in ["Physical Month", "D1", "D2", "D3", "Status Planif"] if c in df_m.columns]
    st.dataframe(df_m[cols_disp], use_container_width=True, hide_index=True)
