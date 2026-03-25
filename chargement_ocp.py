"""
=============================================================
PAGE : PIPELINE DES VENTES
À COLLER dans votre fichier principal, remplacer le bloc :
  elif page=="ventes":
      st.markdown(...)
=============================================================
DÉPENDANCES SUPPLÉMENTAIRES :
  pip install anthropic
=============================================================
"""

# ─── Remplacez le bloc `elif page=="ventes":` par ce qui suit ───

elif page=="ventes":
    import json as _json
    import anthropic as _anthropic

    # ══════════════════════════════════════════════════════
    # STYLES SUPPLÉMENTAIRES — Pipeline des Ventes
    # ══════════════════════════════════════════════════════
    st.markdown("""
    <style>
    /* ─── STATUT PLANIF ─── */
    .status-pill {
      display:inline-flex; align-items:center; gap:5px;
      padding:3px 10px; border-radius:20px;
      font-size:10px; font-weight:700; letter-spacing:.5px; text-transform:uppercase;
    }
    .status-pill.ok      { background:var(--green-lt);  color:var(--green-dk); }
    .status-pill.warning { background:var(--orange-lt); color:var(--orange); }
    .status-pill.danger  { background:#FDECEA;          color:var(--red); }
    .status-pill.neutral { background:var(--border2);   color:var(--text3); }

    /* ─── DECADE VENTES CARDS ─── */
    .vkcard {
      background:var(--white); border:1px solid var(--border);
      border-radius:10px; padding:18px 20px; box-shadow:var(--sh1);
      position:relative; overflow:hidden; transition:transform .18s,box-shadow .18s;
    }
    .vkcard:hover { transform:translateY(-2px); box-shadow:var(--sh2); }
    .vkcard::after {
      content:''; position:absolute; top:0; left:0; right:0;
      height:3px; border-radius:10px 10px 0 0;
    }
    .vkcard.d1::after { background:var(--green); }
    .vkcard.d2::after { background:var(--blue); }
    .vkcard.d3::after { background:var(--orange); }
    .vkcard-lbl { font-size:9px; font-weight:700; letter-spacing:1.4px; text-transform:uppercase; color:var(--text3); }
    .vkcard-dec { font-family:'Barlow Condensed',sans-serif; font-size:13px; font-weight:800; letter-spacing:1px; }
    .vkcard-dec.d1 { color:var(--green); }
    .vkcard-dec.d2 { color:var(--blue); }
    .vkcard-dec.d3 { color:var(--orange); }
    .vkcard-val { font-family:'Barlow Condensed',sans-serif; font-size:32px; font-weight:700; line-height:1; margin:6px 0 2px; }
    .vkcard-val.d1 { color:var(--green); }
    .vkcard-val.d2 { color:var(--blue); }
    .vkcard-val.d3 { color:var(--orange); }
    .vkcard-unit { font-size:12px; font-weight:500; color:var(--text3); margin-left:2px; }
    .vkcard-sub { font-size:11px; color:var(--text2); margin-top:2px; }

    /* ─── TABLEAU VENTES ─── */
    .vtable-wrap {
      background:var(--white); border:1px solid var(--border);
      border-radius:10px; overflow:hidden; box-shadow:var(--sh1);
    }
    .vtable { width:100%; border-collapse:collapse; }
    .vtable th {
      background:#F8FAFB; border-bottom:2px solid var(--border);
      padding:10px 16px; text-align:left;
      font-size:10px; font-weight:700; letter-spacing:1px;
      text-transform:uppercase; color:var(--text2);
      white-space:nowrap;
    }
    .vtable th.center { text-align:center; }
    .vtable td {
      padding:11px 16px; border-bottom:1px solid var(--border2);
      font-size:13px; color:var(--text); vertical-align:middle;
    }
    .vtable td.center { text-align:center; }
    .vtable td.mono {
      font-family:'Barlow Condensed',sans-serif; font-size:14px;
      font-weight:700; color:var(--text);
    }
    .vtable td.green-val { color:var(--green); font-weight:700; font-family:'Barlow Condensed',sans-serif; font-size:14px; }
    .vtable td.blue-val  { color:var(--blue);  font-weight:700; font-family:'Barlow Condensed',sans-serif; font-size:14px; }
    .vtable td.orange-val{ color:var(--orange);font-weight:700; font-family:'Barlow Condensed',sans-serif; font-size:14px; }
    .vtable tr:last-child td { border-bottom:none; }
    .vtable tr:hover td { background:#FAFBFC; }
    .vtable tr.total-row td {
      background:#F8FAFB; border-top:2px solid var(--border);
      font-weight:700; border-bottom:none;
    }
    .vtable tr.total-row td.green-val { color:var(--green); font-size:15px; }
    .vtable tr.total-row td.blue-val  { color:var(--blue);  font-size:15px; }
    .vtable tr.total-row td.orange-val{ color:var(--orange);font-size:15px; }

    /* ─── AI BADGE ─── */
    .ai-badge {
      display:inline-flex; align-items:center; gap:6px;
      background:linear-gradient(135deg,#6B3FA0,#1565C0);
      color:white; border-radius:20px; padding:4px 14px;
      font-size:10px; font-weight:700; letter-spacing:.5px;
    }
    .ai-badge-dot {
      width:6px; height:6px; background:#fff;
      border-radius:50%; opacity:.8;
      animation:pulse 1.5s ease-in-out infinite;
    }
    @keyframes pulse { 0%,100%{opacity:.8;transform:scale(1)} 50%{opacity:1;transform:scale(1.2)} }

    /* ─── ANALYSE AI CARD ─── */
    .ai-analysis-card {
      background:linear-gradient(135deg,#F0EBF8,#E3EAF8);
      border:1px solid rgba(107,63,160,.2);
      border-radius:10px; padding:18px 20px;
      margin-top:16px; box-shadow:var(--sh1);
    }
    .ai-analysis-title {
      font-family:'Barlow Condensed',sans-serif; font-size:15px;
      font-weight:700; color:#4A1E8A; margin-bottom:10px;
      display:flex; align-items:center; gap:8px;
    }
    .ai-analysis-body {
      font-size:13px; color:#2D3748; line-height:1.7;
    }
    .ai-analysis-body p { margin:0 0 8px; }
    .ai-analysis-body strong { color:#4A1E8A; }

    /* ─── MAPPING INFO ─── */
    .mapping-card {
      background:var(--green-lt); border:1px solid rgba(0,132,61,.2);
      border-radius:8px; padding:12px 16px; margin-bottom:14px;
      display:flex; align-items:flex-start; gap:10px;
    }
    .mapping-icon { font-size:18px; flex-shrink:0; margin-top:1px; }
    .mapping-text { font-size:11px; color:var(--green-dk); line-height:1.5; }
    .mapping-text strong { font-weight:700; }
    </style>
    """, unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════
    # HELPERS VENTES
    # ══════════════════════════════════════════════════════
    VENTES_CACHE = os.path.join(CACHE_DIR, "ventes.pkl")
    HIST_VENTES  = os.path.join(CACHE_DIR, "hist_ventes.json")

    def load_ventes_cache():
        return load_cache(VENTES_CACHE)

    def save_ventes_cache(data):
        save_cache(VENTES_CACHE, data)

    # ── Lecture brute du fichier ──
    def read_excel_raw(raw_bytes, fname):
        """Retourne toutes les feuilles en dict {sheet_name: DataFrame}"""
        ff = io.BytesIO(raw_bytes); ff.name = fname
        r, e = read_bytes(ff)
        xl = pd.ExcelFile(io.BytesIO(r), engine=e)
        sheets = {}
        for sn in xl.sheet_names:
            try:
                df_s = pd.read_excel(io.BytesIO(r), sheet_name=sn, header=None, engine=e)
                sheets[sn] = df_s
            except:
                pass
        return sheets, r, e

    def df_to_text_sample(df, max_rows=6):
        """Convertit un df en texte lisible pour le LLM."""
        lines = []
        for ri in range(min(max_rows, len(df))):
            row_vals = [str(v).strip() for v in df.iloc[ri].tolist()]
            lines.append(" | ".join(row_vals))
        return "\n".join(lines)

    # ── Appel LLM pour détecter colonnes ──
    def llm_detect_columns(sheets_sample: dict) -> dict:
        """
        Envoie un échantillon des feuilles au LLM.
        Retourne un dict avec le mapping détecté :
          {
            "sheet": "nom de la feuille",
            "header_row": int,   # index 0-based de la ligne d'en-tête
            "month_col": "nom ou index",
            "d1_col": "nom ou index",
            "d2_col": "nom ou index",
            "d3_col": "nom ou index",
            "status_col": "nom ou index ou null",
            "unit": "KT ou T ou autre",
            "explanation": "..."
          }
        """
        # Construire le prompt
        sample_text = ""
        for sn, df_s in list(sheets_sample.items())[:3]:  # max 3 feuilles
            sample_text += f"\n\n=== FEUILLE: {sn} ===\n"
            sample_text += df_to_text_sample(df_s, max_rows=8)

        prompt = f"""Tu es un expert en analyse de fichiers Excel industriels pour OCP Manufacturing (phosphates, engrais).

Voici un échantillon d'un fichier Excel Pipeline des Ventes :
{sample_text}

Ton objectif : identifier précisément les colonnes qui correspondent à :
1. Le MOIS (month) — colonne contenant les noms de mois ou périodes
2. La DÉCADE 1 (D1) — production/ventes de la 1ère décade (jours 1-10)
3. La DÉCADE 2 (D2) — production/ventes de la 2ème décade (jours 11-20)
4. La DÉCADE 3 (D3) — production/ventes de la 3ème décade (jours 21-fin)
5. Le STATUT PLANIFICATION (status_planif) — colonne de statut ou confirmation (peut être absent)

Les colonnes peuvent avoir des noms très variés comme :
- Mois : "Mois", "Month", "Période", "Mese", "MOIS", "période planif", etc.
- D1 : "D1", "Décade 1", "Dec1", "1ère décade", "D.1", "Décade I", "1-10", etc.
- D2 : "D2", "Décade 2", "Dec2", "2ème décade", "D.2", "Décade II", "11-20", etc.
- D3 : "D3", "Décade 3", "Dec3", "3ème décade", "D.3", "Décade III", "21-31", etc.
- Status : "Statut", "Status", "Planif", "Confirmation", "State", "Etat", peut être absent

Identifie aussi :
- La feuille la plus pertinente (celle qui contient les données de ventes/planification)
- La ligne d'en-tête (header_row, index 0-based)
- L'unité utilisée (KT, T, etc.)

Réponds UNIQUEMENT avec un JSON valide, sans markdown, sans explication hors JSON :
{{
  "sheet": "nom de la feuille",
  "header_row": 0,
  "month_col": "nom exact de la colonne mois ou null",
  "d1_col": "nom exact de la colonne D1 ou null",
  "d2_col": "nom exact de la colonne D2 ou null",
  "d3_col": "nom exact de la colonne D3 ou null",
  "status_col": "nom exact de la colonne statut ou null",
  "unit": "KT",
  "explanation": "explication courte en français de ce que tu as trouvé"
}}"""

        client = _anthropic.Anthropic()
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=800,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = response.content[0].text.strip()
        # Nettoyer le JSON
        raw = raw.replace("```json", "").replace("```", "").strip()
        return _json.loads(raw)

    # ── Parser ventes avec mapping LLM ──
    def parse_ventes_with_mapping(raw_bytes, fname, mapping: dict):
        """Parse le fichier en utilisant le mapping détecté par le LLM."""
        ff = io.BytesIO(raw_bytes); ff.name = fname
        r, e = read_bytes(ff)
        sheet = mapping.get("sheet", 0)
        hrow  = int(mapping.get("header_row", 0))

        df_raw = pd.read_excel(io.BytesIO(r), sheet_name=sheet, header=hrow, engine=e)
        df_raw.columns = [str(c).strip() for c in df_raw.columns]

        # Mapper les colonnes
        def find_col(df, name):
            if name is None: return None
            name = str(name).strip()
            if name in df.columns: return name
            # Recherche insensible à la casse
            for c in df.columns:
                if str(c).strip().lower() == name.lower(): return c
            return None

        col_month  = find_col(df_raw, mapping.get("month_col"))
        col_d1     = find_col(df_raw, mapping.get("d1_col"))
        col_d2     = find_col(df_raw, mapping.get("d2_col"))
        col_d3     = find_col(df_raw, mapping.get("d3_col"))
        col_status = find_col(df_raw, mapping.get("status_col"))

        rows = []
        for _, row in df_raw.iterrows():
            if col_month is None: continue
            mois_val = str(row[col_month]).strip() if pd.notna(row[col_month]) else ""
            if mois_val in ("", "nan", "None"): continue
            if any(k in mois_val.upper() for k in ["TOTAL","CUMUL","MOIS","MONTH","NaN"]): continue

            d1  = force_n(row[col_d1])     if col_d1     else 0.
            d2  = force_n(row[col_d2])     if col_d2     else 0.
            d3  = force_n(row[col_d3])     if col_d3     else 0.
            st_ = str(row[col_status]).strip() if col_status and pd.notna(row.get(col_status)) else ""

            total = round(d1 + d2 + d3, 1)
            rows.append({
                "Mois":   mois_val,
                "D1":     round(d1, 1),
                "D2":     round(d2, 1),
                "D3":     round(d3, 1),
                "Total":  total,
                "Status": st_,
            })
        return pd.DataFrame(rows) if rows else None

    # ── Analyse AI narrative ──
    def llm_analyse_ventes(df_ventes: pd.DataFrame, unit: str = "KT") -> str:
        """Génère une analyse narrative des données de ventes par le LLM."""
        summary = df_ventes.to_string(index=False, max_rows=20)
        total_global = df_ventes["Total"].sum()
        meilleur = df_ventes.loc[df_ventes["Total"].idxmax()]["Mois"] if not df_ventes.empty else "—"

        prompt = f"""Tu es un analyste expert OCP Manufacturing. Voici les données du Pipeline des Ventes :

{summary}

Total global : {round(total_global, 1)} {unit}
Meilleur mois : {meilleur}

Fournis une analyse concise (3-4 phrases) en français professionnel qui couvre :
1. La tendance générale des volumes D1/D2/D3
2. Les mois les plus performants
3. L'équilibre entre les décades
4. Un commentaire sur le statut de planification si disponible

Réponds directement avec le texte de l'analyse, sans titre, sans bullet points, en HTML inline (<strong> pour accentuer)."""

        client = _anthropic.Anthropic()
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text.strip()

    # ── Status badge HTML ──
    def status_badge(s):
        if not s or s in ("nan", "None", ""): return '<span class="status-pill neutral">—</span>'
        su = s.upper()
        if any(k in su for k in ["CONFIRM","OK","VALID","APPROV","OUI","YES","DONE"]):
            return f'<span class="status-pill ok">✓ {s}</span>'
        elif any(k in su for k in ["ATTENT","PENDING","WAIT","EN COURS","PARTIAL"]):
            return f'<span class="status-pill warning">⏳ {s}</span>'
        elif any(k in su for k in ["NON","NO","REFUS","ANNUL","CANCEL","KO"]):
            return f'<span class="status-pill danger">✗ {s}</span>'
        else:
            return f'<span class="status-pill neutral">{s}</span>'

    # ══════════════════════════════════════════════════════
    # SESSION STATE VENTES
    # ══════════════════════════════════════════════════════
    if "ventes_df"      not in st.session_state: st.session_state["ventes_df"]      = None
    if "ventes_mapping" not in st.session_state: st.session_state["ventes_mapping"] = None
    if "ventes_name"    not in st.session_state: st.session_state["ventes_name"]    = ""
    if "ventes_analyse" not in st.session_state: st.session_state["ventes_analyse"] = ""

    # Charger depuis cache
    if st.session_state["ventes_df"] is None:
        cached = load_ventes_cache()
        if cached:
            st.session_state["ventes_df"]      = cached.get("df")
            st.session_state["ventes_mapping"] = cached.get("mapping")
            st.session_state["ventes_name"]    = cached.get("filename", "")
            st.session_state["ventes_analyse"] = cached.get("analyse", "")

    # ══════════════════════════════════════════════════════
    # UPLOAD SECTION
    # ══════════════════════════════════════════════════════
    st.markdown('<div class="stitle">Chargement du fichier Ventes</div>', unsafe_allow_html=True)

    with st.container():
        st.markdown("""<div class="upload-zone">
        <div class="zone-title">
          📊 Fichier Pipeline des Ventes
          &nbsp;&nbsp;<span class="ai-badge"><span class="ai-badge-dot"></span>IA — Détection automatique des colonnes</span>
        </div>
        <div class="zone-desc">Excel avec colonnes Mois, D1, D2, D3 — les noms de colonnes sont détectés automatiquement par l'IA</div>
        """, unsafe_allow_html=True)

        file_ventes = st.file_uploader(
            "Choisir fichier Ventes", type=EXCEL_T, key="ventes_up",
            label_visibility="collapsed"
        )
        vn = st.session_state.get("ventes_name", "")
        if vn:
            st.success(f"Actif : {vn}")

        if file_ventes:
            with st.spinner("🤖 L'IA analyse la structure du fichier…"):
                try:
                    file_ventes.seek(0)
                    raw_v = file_ventes.read()

                    # Lire les feuilles
                    sheets, r_v, e_v = read_excel_raw(raw_v, file_ventes.name)
                    sheets_sample = {k: v for k, v in list(sheets.items())[:3]}

                    # LLM détecte les colonnes
                    mapping = llm_detect_columns(sheets_sample)
                    st.session_state["ventes_mapping"] = mapping

                    # Parser avec le mapping
                    df_v = parse_ventes_with_mapping(raw_v, file_ventes.name, mapping)
                    st.session_state["ventes_df"]   = df_v
                    st.session_state["ventes_name"] = file_ventes.name
                    st.session_state["ventes_analyse"] = ""  # reset analyse

                    # Sauvegarder
                    save_ventes_cache({
                        "df": df_v, "mapping": mapping,
                        "filename": file_ventes.name, "analyse": ""
                    })

                    if df_v is not None and not df_v.empty:
                        st.success(f"✅ Fichier chargé — {len(df_v)} mois détectés")
                    else:
                        st.warning("⚠️ Fichier chargé mais aucune donnée extraite. Vérifiez la structure.")

                except Exception as ex:
                    st.error(f"Erreur : {ex}")

        st.markdown("</div>", unsafe_allow_html=True)

    # ── Afficher le mapping détecté ──
    mapping = st.session_state.get("ventes_mapping")
    if mapping:
        expl = mapping.get("explanation", "")
        unit = mapping.get("unit", "KT")
        st.markdown(f"""
        <div class="mapping-card">
          <div class="mapping-icon">🤖</div>
          <div class="mapping-text">
            <strong>Mapping IA détecté :</strong>
            Feuille <strong>« {mapping.get('sheet','?')} »</strong> —
            Mois : <strong>« {mapping.get('month_col','?')} »</strong> ·
            D1 : <strong>« {mapping.get('d1_col','?')} »</strong> ·
            D2 : <strong>« {mapping.get('d2_col','?')} »</strong> ·
            D3 : <strong>« {mapping.get('d3_col','?')} »</strong> ·
            Statut : <strong>« {mapping.get('status_col') or 'Non détecté'} »</strong><br/>
            {f'<em>{expl}</em>' if expl else ''}
          </div>
        </div>""", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════
    # DONNÉES + FILTRES
    # ══════════════════════════════════════════════════════
    ventes_df = st.session_state.get("ventes_df")
    unit = mapping.get("unit", "KT") if mapping else "KT"

    if ventes_df is not None and not ventes_df.empty:

        # ── Filtre par mois ──
        st.markdown('<div class="stitle">Filtrage par mois</div>', unsafe_allow_html=True)
        tous_mois = ventes_df["Mois"].unique().tolist()

        with st.container():
            st.markdown('<div class="filter-panel"><div class="filter-panel-title">Sélection des mois</div>', unsafe_allow_html=True)
            col_fa, col_fb = st.columns([1, 3])
            with col_fa:
                filtre_mode = st.radio("Mode", ["Tout", "Sélection"], horizontal=True, key="vf_mode")
            with col_fb:
                if filtre_mode == "Sélection":
                    mois_choisis = st.multiselect(
                        "Mois à afficher", options=tous_mois,
                        default=tous_mois[:3] if len(tous_mois) >= 3 else tous_mois,
                        key="vf_mois"
                    )
                else:
                    mois_choisis = tous_mois
            st.markdown('</div>', unsafe_allow_html=True)

        # Filtrer
        df_filtre = ventes_df[ventes_df["Mois"].isin(mois_choisis)].copy() if mois_choisis else ventes_df.copy()

        # ── KPI Cards — Totaux décades ──
        total_d1    = round(df_filtre["D1"].sum(), 1)
        total_d2    = round(df_filtre["D2"].sum(), 1)
        total_d3    = round(df_filtre["D3"].sum(), 1)
        total_all   = round(total_d1 + total_d2 + total_d3, 1)
        periode_lbl = f"{len(df_filtre)} mois sélectionnés"

        st.markdown(f'<div class="stitle">Cumul décades — {periode_lbl}</div>', unsafe_allow_html=True)

        kc1, kc2, kc3 = st.columns(3)
        with kc1:
            pct1 = round(total_d1 / total_all * 100, 1) if total_all > 0 else 0
            st.markdown(f"""
            <div class="vkcard d1">
              <div class="vkcard-lbl">Décade 1 — J1 à J10</div>
              <div class="vkcard-dec d1">D1</div>
              <div class="vkcard-val d1">{fmt(total_d1)}<span class="vkcard-unit">{unit}</span></div>
              <div class="vkcard-sub">{pct1}% du total · {len(df_filtre)} mois</div>
            </div>""", unsafe_allow_html=True)
        with kc2:
            pct2 = round(total_d2 / total_all * 100, 1) if total_all > 0 else 0
            st.markdown(f"""
            <div class="vkcard d2">
              <div class="vkcard-lbl">Décade 2 — J11 à J20</div>
              <div class="vkcard-dec d2">D2</div>
              <div class="vkcard-val d2">{fmt(total_d2)}<span class="vkcard-unit">{unit}</span></div>
              <div class="vkcard-sub">{pct2}% du total · {len(df_filtre)} mois</div>
            </div>""", unsafe_allow_html=True)
        with kc3:
            pct3 = round(total_d3 / total_all * 100, 1) if total_all > 0 else 0
            st.markdown(f"""
            <div class="vkcard d3">
              <div class="vkcard-lbl">Décade 3 — J21 à fin</div>
              <div class="vkcard-dec d3">D3</div>
              <div class="vkcard-val d3">{fmt(total_d3)}<span class="vkcard-unit">{unit}</span></div>
              <div class="vkcard-sub">{pct3}% du total · {len(df_filtre)} mois</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<div style='margin-top:4px'></div>", unsafe_allow_html=True)

        # ── Tableau des 5 colonnes ──
        st.markdown('<div class="stitle blue">Tableau — Mois · D1 · D2 · D3 · Statut Planif</div>', unsafe_allow_html=True)

        rows_html = ""
        for _, row in df_filtre.iterrows():
            sb = status_badge(row.get("Status", ""))
            rows_html += f"""
            <tr>
              <td class="mono">{row['Mois']}</td>
              <td class="center green-val">{fmt(row['D1'])}</td>
              <td class="center blue-val">{fmt(row['D2'])}</td>
              <td class="center orange-val">{fmt(row['D3'])}</td>
              <td class="center">{sb}</td>
            </tr>"""

        # Ligne total
        rows_html += f"""
        <tr class="total-row">
          <td class="mono">▶ TOTAL ({len(df_filtre)} mois)</td>
          <td class="center green-val">{fmt(total_d1)}</td>
          <td class="center blue-val">{fmt(total_d2)}</td>
          <td class="center orange-val">{fmt(total_d3)}</td>
          <td class="center"><span class="status-pill neutral">{fmt(total_all)} {unit}</span></td>
        </tr>"""

        st.markdown(f"""
        <div class="vtable-wrap">
          <table class="vtable">
            <thead>
              <tr>
                <th>Mois</th>
                <th class="center">D1 — {unit}</th>
                <th class="center">D2 — {unit}</th>
                <th class="center">D3 — {unit}</th>
                <th class="center">Statut Planif</th>
              </tr>
            </thead>
            <tbody>
              {rows_html}
            </tbody>
          </table>
        </div>""", unsafe_allow_html=True)

        # ── Graphique barres D1/D2/D3 par mois ──
        st.markdown("<div style='margin-top:20px'></div>", unsafe_allow_html=True)
        st.markdown('<div class="stitle orange">Répartition D1 · D2 · D3 par mois</div>', unsafe_allow_html=True)

        if len(df_filtre) > 0:
            fig_v = go.Figure()
            fig_v.add_trace(go.Bar(
                name="D1", x=df_filtre["Mois"], y=df_filtre["D1"],
                marker_color="#00843D", opacity=.85,
                hovertemplate='<b>%{x}</b><br>D1: %{y:.1f} ' + unit + '<extra></extra>'
            ))
            fig_v.add_trace(go.Bar(
                name="D2", x=df_filtre["Mois"], y=df_filtre["D2"],
                marker_color="#1565C0", opacity=.85,
                hovertemplate='<b>%{x}</b><br>D2: %{y:.1f} ' + unit + '<extra></extra>'
            ))
            fig_v.add_trace(go.Bar(
                name="D3", x=df_filtre["Mois"], y=df_filtre["D3"],
                marker_color="#C05A00", opacity=.85,
                hovertemplate='<b>%{x}</b><br>D3: %{y:.1f} ' + unit + '<extra></extra>'
            ))
            lyt_v = dict(**PL)
            lyt_v["barmode"]  = "group"
            lyt_v["height"]   = 380
            lyt_v["title"]    = dict(text=f"Ventes par décade ({unit})", font=dict(size=13, color="#4A5568"))
            lyt_v["bargap"]   = 0.25
            lyt_v["bargroupgap"] = 0.08
            fig_v.update_layout(**lyt_v)
            st.plotly_chart(fig_v, use_container_width=True)

        # ── Analyse IA narrative ──
        st.markdown('<div class="stitle purple">Analyse IA — Synthèse Pipeline des Ventes</div>', unsafe_allow_html=True)

        cached_analyse = st.session_state.get("ventes_analyse", "")
        btn_col1, btn_col2, _ = st.columns([1, 1, 3])
        with btn_col1:
            gen_btn = st.button("🤖 Générer l'analyse IA", key="ventes_gen_ai", type="primary")
        with btn_col2:
            if cached_analyse:
                if st.button("🔄 Régénérer", key="ventes_regen_ai"):
                    cached_analyse = ""
                    st.session_state["ventes_analyse"] = ""

        if gen_btn or (not cached_analyse and gen_btn):
            with st.spinner("🤖 L'IA analyse vos données de ventes…"):
                try:
                    analyse = llm_analyse_ventes(df_filtre, unit)
                    st.session_state["ventes_analyse"] = analyse
                    cached_analyse = analyse
                    # Mettre à jour le cache
                    save_ventes_cache({
                        "df": ventes_df, "mapping": mapping,
                        "filename": st.session_state["ventes_name"],
                        "analyse": analyse
                    })
                except Exception as ex:
                    st.error(f"Erreur analyse IA : {ex}")

        if cached_analyse:
            st.markdown(f"""
            <div class="ai-analysis-card">
              <div class="ai-analysis-title">
                🤖 Analyse IA — Pipeline des Ventes
                <span class="ai-badge"><span class="ai-badge-dot"></span>Claude</span>
              </div>
              <div class="ai-analysis-body">
                <p>{cached_analyse}</p>
              </div>
            </div>""", unsafe_allow_html=True)

    else:
        # ── Placeholder si pas de données ──
        st.markdown("""
        <div class="ph-card">
          <h2>📊 Pipeline des Ventes</h2>
          <p>Chargez un fichier Excel ci-dessus.<br/>
          L'IA détecte automatiquement les colonnes Mois, D1, D2, D3 et Statut Planification,
          même si leurs noms changent d'un fichier à l'autre.</p>
          <div class="ph-badge-g">IA INTÉGRÉE — DÉTECTION AUTOMATIQUE</div>
        </div>""", unsafe_allow_html=True)
