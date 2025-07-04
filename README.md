# 🤖 Chatbot Santé – Québec

> _Une courte description du projet en une phrase ou deux._

---

## 📋 Table des matières

1. [Description](#description)  
2. [Fonctionnalités](#fonctionnalités)  
3. [Prérequis](#prérequis)  
4. [Installation](#installation)  
5. [Configuration](#configuration)  
6. [Usage](#usage)  
7. [Structure du projet](#structure-du-projet)  
8. [Variables d’environnement](#variables-denvironnement)  
9. [Contribuer](#contribuer)  
10. [Licence](#licence)  

---

## 1. Description

Décrivez ici l’objectif principal de l’application, le problème qu’elle résout et son public cible.

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

