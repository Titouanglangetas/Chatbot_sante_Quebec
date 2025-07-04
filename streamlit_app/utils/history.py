# streamlit_app/utils/history.py

import os
import json
from typing import List, Dict, Any

# Répertoire où seront stockés les historiques de conversation
HISTO_DIR = "histories"
os.makedirs(HISTO_DIR, exist_ok=True)

def load_history(user_id: str) -> List[Dict[str, Any]]:
    """
    Charge l'historique des conversations pour l'utilisateur donné.
    Si aucun fichier n'existe encore, renvoie une liste vide.
    """
    path = os.path.join(HISTO_DIR, f"{user_id}.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_history(user_id: str, conversations: List[Dict[str, Any]]) -> None:
    """
    Sauvegarde la liste des conversations de l'utilisateur dans un fichier JSON.
    Écrase le fichier précédent si besoin.
    """
    path = os.path.join(HISTO_DIR, f"{user_id}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(conversations, f, ensure_ascii=False, indent=2)
