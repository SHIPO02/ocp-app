import streamlit as st
import pandas as pd
import re
import os
import io
import pickle
import json
from datetime import datetime
import plotly.graph_objects as go

# ─── CONFIGURATION DE LA PAGE ────────────────────────────────────────────────
st.set_page_config(page_title="OCP - Dashboard Manufacturing", layout="wide")

# Injection du CSS (Style OCP conservé)
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Barlow:wght@400;600;700&family=Barlow+Condensed:wght@600;700&display=swap');
        :root { --ocp-green: #00843D; --ocp-dark: #005C2A; --jorf-color: #00843D; --safi-color: #1A6FA8; --total-color: #C05A00; --rade-color: #6B3FA0; }
        html, body, [class*="css"] { font-family: 'Barlow', sans-serif; }
        .stApp { background-color: #F4F7F5; }
        h1, h2, h3 { color: var(--ocp-dark) !important; font-family: 'Barlow Condensed', sans-serif !important; }
        .kpi-card { border-radius: 12px; padding: 16px 18px; color: white; box-shadow: 0 4px 16px rgba(0,0,0,0.12); position: relative; overflow: hidden; min-height: 160px; height: 160px; display: flex; flex-direction: column; justify-content: space-between; box-sizing: border-box; }
        .kpi-card.jorf  { background: linear-gradient(135deg, #00843D, #005C2A); }
        .kpi-card.safi  { background: linear-gradient(135deg, #1A6FA8, #0D4A73); }
        .kpi-card.total { background: linear-gradient(135deg, #C05A00, #8A3F00); }
        .kpi-card.rade  { background: linear-gradient(135deg, #6B3FA0, #4A2A73); }
        .kpi-label { font-size: 11px; font-weight: 700; opacity: 0.9; letter-spacing: 1px; text-transform: uppercase; }
        .kpi-value { font-family: 'Barlow Condensed', sans-serif; font-size: 32px; font-weight: 700; }
        .section-header { display: flex; align-items: center; gap: 10px; padding: 10px 16px; border-radius: 8px; margin: 20px 0 10px 0; font-family: 'Barlow Condensed', sans-serif; font-size: 20px; font-weight: 700; color: white; }
        .section-header.total { background: var(--total-color); }
        .section-header.jorf  { background: var(--jorf-color); }
        .section-header.safi  { background: var(--safi-color); }
        .section-header.rade  { background: var(--rade-color); }
    </style>
""", unsafe_allow_html=True)

# ─── CONSTANTES ET CACHE ─────────────────────────────────────────────────────
CACHE_DIR    = ".ocp_cache"
JORF_CACHE   = os.path.join(CACHE_DIR, "jorf.pkl")
SAFI_CACHE   = os.path.join(CACHE_DIR, "safi.pkl")
HIST_JORF    = os.path.join(CACHE_DIR, "hist_jorf.json")
HIST_SAFI    = os.path.join(CACHE_DIR, "hist_safi.json")
HIST_FILES   = os.path.join(CACHE_DIR, "hist_files")
os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(HIST_FILES, exist_ok=True)

# ─── FONCTIONS UTILITAIRES (Dashboard) ───────────────────────────────────────
# [Insérer ici toutes les fonctions de ton premier code : save_cache, load_cache, add_to_historique, parse_jorf, etc.]
# (Je les omets ici pour la brièveté mais elles doivent être présentes dans ton fichier final)
# ... (Gardez toutes vos fonctions d'extraction et de formatage du code 1) ...

# ─── FONCTIONS DE SIMULATION (Code 2) ────────────────────────────────────────
def simulation_stock_soufre(stock_initial, consommation_journaliere, navires, retards, conso_reelle=None, seuil_critique=36000):
    navires = sorted(navires, key=lambda x: x[0])
    today = pd.Timestamp.today()
    debut_mois = pd.Timestamp(today.year, today.month, 1)
    fin_mois = debut_mois + pd.DateOffset(days=60)
    calendrier = pd.date_range(start=debut_mois, end=fin_mois, freq='D')
    stock = stock_initial
    stock_values, dates, navire_arrivees, navire_quantites = [], [], [], []
    for jour in calendrier:
        for (date_prevue, quantite) in navires:
            date_effective = date_prevue + pd.Timedelta(days=retards.get(date_prevue, 0))
            if jour == date_effective:
                stock += quantite
                navire_arrivees.append(jour)
                navire_quantites.append(quantite)
        conso = conso_reelle.get(jour.date(), consommation_journaliere) if conso_reelle else consommation_journaliere
        stock -= conso
        stock_values.append(stock)
        dates.append(jour)
    return dates, stock_values, navire_arrivees, navire_quantites

def afficher_graphique_simulation(dates, stock_values, navire_arrivees, navire_quantites, titre, seuil=36000):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dates, y=stock_values, mode='lines+markers', name='Stock', line=dict(color='#1A6FA8')))
    fig.add_trace(go.Scatter(x=dates, y=[seuil]*len(dates), mode='lines', name='Seuil critique', line=dict(dash='dash', color='red')))
    for i, date in enumerate(navire_arrivees):
        fig.add_trace(go.Scatter(x=[date], y=[stock_values[dates.index(date)]], mode='markers+text', 
                                 name='Arrivée navire', marker=dict(symbol='triangle-up', color='green', size=12),
                                 text=[f"{navire_quantites[i]} T"], textposition='top center'))
    fig.update_layout(title=titre, xaxis_title='Date', yaxis_title='Stock (tonnes)', hovermode='x unified', template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)

# ─── NAVIGATION SIDEBAR ──────────────────────────────────────────────────────
st.sidebar.image("https://upload.wikimedia.org/wikipedia/fr/thumb/d/d1/OCP_Logo.svg/1200px-OCP_Logo.svg.png", width=100) # Optionnel
menu = st.sidebar.radio("Navigation principale", ["📊 Suivi des Chargements", "📉 Simulation de Stock"], index=0)

# ─── PAGE 1 : SUIVI DES CHARGEMENTS ──────────────────────────────────────────
if menu == "📊 Suivi des Chargements":
    # Mettre ici tout le corps de ton PREMIER CODE (Header, File Uploaders, Table unifiée, Graphiques)
    st.title("Suivi chargement Manufacturing")
    st.markdown("##### Jorf Lasfar & Safi")
    st.divider()
    
    # [Reste de la logique de chargement de fichiers et affichage du tableau consolidé...]
    st.info("Utilisez la barre latérale pour charger vos fichiers Excel Jorf et Safi.")

# ─── PAGE 2 : SIMULATION DE STOCK ────────────────────────────────────────────
elif menu == "📉 Simulation de Stock":
    st.title("📊 Simulation Prévisionnelle des Stocks")
    
    tab_safi, tab_jorf = st.tabs(["🌊 Site de Safi", "⚓ Site de Jorf"])

    with tab_safi:
        st.header("🔍 Paramètres - SAFI")
        # [Logique de simulation Safi du code 2]
        col1, col2 = st.columns(2)
        with col1:
            stock_init = st.number_input("Stock initial (T)", value=40000, key="sim_safi_init")
        with col2:
            conso_j = st.number_input("Consommation journalière (T)", value=3600, key="sim_safi_conso")
        
        # Exemple rapide pour montrer l'intégration
        if st.button("Lancer la simulation Safi"):
            # Simulation simplifiée pour l'exemple
            d, sv, na, nq = simulation_stock_soufre(stock_init, conso_j, [], {})
            afficher_graphique_simulation(d, sv, na, nq, "Évolution Stock Soufre Safi")

    with tab_jorf:
        st.header("🔍 Paramètres - JORF")
        matiere = st.selectbox("Matière première", ["Soufre", "NH3", "KCL", "ACS"])
        
        if matiere == "ACS":
            # [Logique complexe ACS du code 2]
            st.subheader("Production ACS multi-périodes")
            # ... (Copier-coller votre logique de calcul ACS ici)
        else:
            # [Logique Soufre/NH3/KCL du code 2]
            st.subheader(f"Simulation {matiere}")
            # ...
