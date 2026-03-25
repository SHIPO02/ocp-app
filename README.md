# 🚀 OCP Manufacturing Dashboard - IA Automation

Cette application Streamlit permet de centraliser et d'automatiser le suivi des chargements et du pipeline de ventes pour les sites de **Jorf Lasfar** et **Safi**.

## 🧠 Innovation : Mapping Intelligent par IA
Contrairement aux outils classiques, cette application utilise un **LLM (Gemini 1.5 Flash)** pour analyser sémantiquement les fichiers Excel importés. 
- **Flexibilité totale** : Peu importe si les colonnes changent de nom ou de position (ex: D1, Décade 1, Vol_D1), l'IA les identifie automatiquement.
- **Sécurité** : Un système de validation humaine permet de confirmer le mapping suggéré par l'IA avant l'importation.

## 📊 Fonctionnalités principales
- **Suivi Chargement** : Consolidation journalière des exports Engrais et Camions.
- **Pipeline Ventes** : Analyse des tonnages par décades (D1, D2, D3) et par statut (En Rade, En cours, Chargé).
- **Simulation de Stock** : Projection des stocks de matières premières (Soufre, NH3, etc.) avec gestion des arrivées navires.
- **Persistance** : Système de cache local pour conserver les dernières données chargées.

## 🛠️ Installation
1. Cloner le projet
2. Installer les dépendances : `pip install -r requirements.txt`
3. Configurer votre clé API Gemini dans les secrets Streamlit ou fichier `.env`
4. Lancer l'app : `streamlit run chargement_ocp.py`

---
*Développé pour l'optimisation des flux logistiques OCP.*
