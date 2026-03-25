# --- AFFICHAGE DES RÉSULTATS (PROTECTION CONTRE LES ERREURS) ---
if st.session_state.get("ventes_df") is not None:
    df = st.session_state["ventes_df"]
    
    # 1. Filtre dynamique par mois
    if "Physical Month" in df.columns:
        mois_sel = st.selectbox("Sélectionner le Mois", df["Physical Month"].dropna().unique())
        df_m = df[df["Physical Month"] == mois_sel]
    else:
        df_m = df
        mois_sel = "Tout"

    # 2. GÉNÉRATION DES 3 CARTES (CARDS)
    st.markdown(f"### 📊 Situation — {mois_sel}")
    c1, c2, c3 = st.columns(3)
    
    # Configuration des statuts basés sur tes chiffres (1, 2, 0/3)
    confs = [
        (c1, "🚢 En cours de chargement", "#00843D", "1."),
        (c2, "⚓ En Rade", "#6B3FA0", "2."),
        (c3, "📦 Nommé / Chargé", "#1565C0", "0.|3.")
    ]

    for col, title, color, pattern in confs:
        if "Status Planif" in df_m.columns:
            # Filtrage intelligent : on cherche le code dans la colonne Status Planif
            mask = df_m["Status Planif"].astype(str).str.lower().str.contains(pattern, na=False)
            sub = df_m[mask]
            
            # Somme des volumes décades pour ce statut précis
            d1_sum = sub["D1"].sum() if "D1" in sub.columns else 0
            d2_sum = sub["D2"].sum() if "D2" in sub.columns else 0
            d3_sum = sub["D3"].sum() if "D3" in sub.columns else 0
            total_kt = d1_sum + d2_sum + d3_sum
            
            with col:
                st.markdown(f"""
                <div style="background:white; border-radius:10px; padding:18px; border-top:5px solid {color}; box-shadow:0 1px 3px rgba(0,0,0,0.1); margin-bottom:20px;">
                    <div style="font-weight:700; color:{color}; font-size:14px; margin-bottom:10px;">{title}</div>
                    <div style="display:flex; justify-content:space-between; border-bottom:1px solid #F0F2F6; padding-bottom:8px;">
                        <div style="text-align:center;"><div style="font-size:10px;color:#94A3B8;">D1</div><b style="font-size:14px;">{fmt(d1_sum)}</b></div>
                        <div style="text-align:center;"><div style="font-size:10px;color:#94A3B8;">D2</div><b style="font-size:14px;">{fmt(d2_sum)}</b></div>
                        <div style="text-align:center;"><div style="font-size:10px;color:#94A3B8;">D3</div><b style="font-size:14px;">{fmt(d3_sum)}</b></div>
                    </div>
                    <div style="text-align:right; font-weight:800; color:{color}; margin-top:10px; font-size:20px;">
                        {fmt(total_kt)} <span style="font-size:11px;">KT</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # 3. TABLE DE DÉTAIL (AVEC STATUS PLANIF)
    st.markdown("### 📋 TABLE DE DÉTAIL")
    # Liste des colonnes à afficher pour correspondre à ton image
    cols_disp = [c for c in ["Physical Month", "D1", "D2", "D3", "Status Planif"] if c in df_m.columns]
    st.dataframe(df_m[cols_disp], use_container_width=True, hide_index=True)
