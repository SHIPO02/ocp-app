# --- LOGIQUE DE CLASSEMENT DES STATUTS ---

# Configuration des 3 catégories demandées
stats_config = [
    {
        "titre": "🚢 En cours de chargement",
        "couleur": "#00843D", # Vert OCP
        "clés": ["1", "en cours", "loading"],
        "id": "c1"
    },
    {
        "titre": "⚓ En rade",
        "couleur": "#6B3FA0", # Violet
        "clés": ["2", "en rade", "waiting"],
        "id": "c2"
    },
    {
        "titre": "📦 Nommé",
        "couleur": "#1565C0", # Bleu
        "clés": ["3", "nommé", "nomme", "appointed"],
        "id": "c3"
    }
]

# --- DANS LA BOUCLE D'AFFICHAGE DES CARTES ---
cols = st.columns(3)

for i, conf in enumerate(stats_config):
    with cols[i]:
        # Filtrage intelligent : on cherche si la valeur contient le chiffre ou le mot clé
        mask = df_m["Status Planif"].astype(str).str.lower().split('.').str[0].isin(conf["clés"]) | \
               df_m["Status Planif"].astype(str).str.lower().str.contains(conf["clés"][1])
        
        sub = df_m[mask]
        
        # Calcul des volumes D1, D2, D3 pour ce statut
        v_d1 = sub["D1"].sum()
        v_d2 = sub["D2"].sum()
        v_d3 = sub["D3"].sum()
        total = v_d1 + v_d2 + v_d3

        # Affichage de la carte (Design OCP)
        st.markdown(f"""
        <div style="background:white; border-radius:10px; padding:15px; border-top:5px solid {conf['couleur']}; box-shadow:0 2px 5px rgba(0,0,0,0.1)">
            <div style="font-weight:700; color:{conf['couleur']}; font-size:14px;">{conf['titre']}</div>
            <div style="display:flex; justify-content:space-around; margin-top:15px; border-bottom:1px solid #EEE; padding-bottom:10px;">
                <div><div style="font-size:10px; color:gray;">D1</div><div style="font-weight:700;">{fmt(v_d1)}</div></div>
                <div><div style="font-size:10px; color:gray;">D2</div><div style="font-weight:700;">{fmt(v_d2)}</div></div>
                <div><div style="font-size:10px; color:gray;">D3</div><div style="font-weight:700;">{fmt(v_d3)}</div></div>
            </div>
            <div style="text-align:right; padding-top:10px;">
                <span style="font-size:20px; font-weight:800; color:{conf['couleur']};">{fmt(total)}</span>
                <span style="font-size:10px; color:gray;"> KT</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
