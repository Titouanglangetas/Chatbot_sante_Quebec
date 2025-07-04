# streamlit_app/utils/llm_api.py

import os
import re
import requests
from dotenv import load_dotenv
from typing import Optional

# Charge .env
load_dotenv()

# URL de l'API Mistral
MISTRAL_URL = "https://api.mistral.ai/v1/chat/completions"

def _load_and_clean_api_key() -> str:
    """
    Récupère la clé depuis l'env, affiche sa repr pour debug,
    et supprime tout caractère hors-ASCII ou guillemets.
    """
    raw = os.getenv("MISTRAL_API_KEY", "")
    # DEBUG : voir exactement ce qu'on a chargé
    print("DEBUG MISTRAL_API_KEY repr:", repr(raw))

    # on enlève espaces en tête/queue, guillemets simples ou doubles
    key = raw.strip().strip('"').strip("'")
    # on supprime tout caractère non-ASCII (0x00-0x7F)
    key = re.sub(r'[^\x00-\x7F]', '', key)

    return key

def get_llm_response(
    prompt: str,
    model: str = "mistral-medium",
    
) -> str:
    """
    Envoie un prompt à l'API Mistral et renvoie la réponse textuelle.
    """
    api_key = _load_and_clean_api_key()
    if not api_key:
        raise RuntimeError(
            "MISTRAL_API_KEY non configurée ou incorrecte. "
            "Vérifiez votre fichier .env sans espaces, guillemets, ni caractères spéciaux."
        )

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}]
    }

    try:
        resp = requests.post(MISTRAL_URL, headers=headers, json=payload)
    except requests.RequestException as e:
        raise RuntimeError(f"Erreur de connexion à l'API LLM : {e}")

    if resp.status_code == 429:
        # Cas de saturation du service
        return "Désolé, le service est temporairement surchargé. Veuillez réessayer dans quelques instants."
    if resp.status_code != 200:
        msg = resp.text or resp.reason
        raise RuntimeError(f"Erreur API (status {resp.status_code}) : {msg}")

    data = resp.json()
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as e:
        raise RuntimeError(f"Format de réponse inattendu : {e}")
