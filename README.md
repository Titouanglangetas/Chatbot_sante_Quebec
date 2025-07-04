# 🤖 Chatbot Santé – Québec

>Chatbot Santé Québec est une application web interactive développée avec Streamlit, conçue spécifiquement pour les professionnel·le·s de la santé du Québec. 

---

## 📋 Table des matières

1. [Description](#description)  
2. [Fonctionnalités](#fonctionnalités)  
3. [Prérequis](#prérequis)  
4. [Installation](#installation)  
5. [Configuration](#configuration)  
6. [Usage](#usage)  
7. [Structure du projet](#structure-du-projet)  


---

## 1. Description
    Recherche Augmentée par Argument (RAG) avec ChromaDB pour interroger des documents de santé factices et réels (statistiques sur les troubles respiratoires, l’asthme, l’anxiété, etc.).

    Moteur LLM (via l’API Mistral) pour formuler des réponses contextuelles et générer des analyses chiffrées.

    Visualisations dynamiques (Matplotlib) permettant de tracer l’évolution des indicateurs de santé sur une période donnée.

    Génération de rapports PDF enrichis d’analyses et de graphiques exportables.

    Gestion sécurisée des utilisateurs avec authentification Streamlit et historique persistant des conversations (stocké en JSON par utilisateur).

L’interface offre :

    Un chat contextuel où chaque question déclenche une recherche RAG et, si pertinent, une représentation graphique.

    Un menu Rapport autonome pour générer, consulter et télécharger un rapport détaillé (Introduction, Points clés, Graphique, Analyse, Conclusion).

    Une barre latérale listant les conversations passées, avec création, sélection et suppression de sessions.

Ce projet vise à faciliter l’analyse rapide de données de santé québécoises et à offrir aux professionnel·le·s un outil d’aide à la décision simple, robuste et entièrement personnalisable.

---

## 2. Fonctionnalités

- 🔐 Authentification sécurisée  
- 🗂️ Historique des conversations  
- 📊 RAG (Retrieval-Augmented Generation) avec ChromaDB  
- 🤖 Intégration LLM (Mistral / Ollama)  
- 📈 Génération de rapports texte & graphiques  
- 📄 Export PDF  

---

## 3. Prérequis

- **Python** ≥ 3.8  
- **Git**  
- (Optionnel) `virtualenv` ou `venv`  
- Clé API pour LLM (Mistral ou autre)  

---

## 4. Installation

```bash
# 1. Cloner le dépôt
git clone https://github.com/votre-utilisateur/nom-du-repo.git
cd nom-du-repo

# 2. Créer et activer un environnement virtuel
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows
.venv\Scripts\activate

# 3. Installer les dépendances
pip install -r requirements.txt

Copier le modèle d’environnement
```

## 5. Installation
```bash
cp .env.example .env
```
Éditer .env et renseigner vos clés :
```
MISTRAL_API_KEY=VOTRE_CLE_ICI
```
## 6.Usage
# Lancer l’application Streamlit
```
streamlit run streamlit_app/main.py
```
## 7.Structure
```
├── assets/
│   ├── auth.css
│   ├── chat_llm.css
│   └── logo.png
├── histories/
│   └── <user>.json
├── streamlit_app/
│   ├── main.py
│   ├── .env.example
│   └── utils/
│       ├── auth.py
│       ├── history.py
│       ├── llm_api.py
│       ├── rag_utils.py
│       ├── viz.py
│       └── pdf_generator.py
├── requirements.txt
└── README.md
```
