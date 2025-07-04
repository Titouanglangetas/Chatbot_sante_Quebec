import re
from typing import Dict, Any
from matplotlib.figure import Figure


def get_graph_data(fig: Figure) -> Dict[str, Any]:
    """
    Extrait les données essentielles d'une figure Matplotlib.

    Args:
        fig: instance de matplotlib.figure.Figure

    Returns:
        Dictionnaire contenant :
          - title : titre du graphique
          - xlabel : label de l'axe X
          - ylabel : label de l'axe Y
          - xdata : liste des valeurs X (si une seule ligne tracée)
          - ydata : liste des valeurs Y (si une seule ligne tracée)
    """
    data: Dict[str, Any] = {}
    if fig.axes:
        ax = fig.axes[0]
        data['title'] = ax.get_title()
        data['xlabel'] = ax.get_xlabel()
        data['ylabel'] = ax.get_ylabel()

        if ax.lines:
            line = ax.lines[0]
            data['xdata'] = line.get_xdata().tolist()
            data['ydata'] = line.get_ydata().tolist()

    return data


def generate_graph_filename(query: str) -> str:
    """
    Génère un nom de fichier PNG pour un graphique basé sur la requête utilisateur.
    """
    types_donnees = {
        'troubles respiratoires': 'troubles_respiratoires',
        'anxiété': 'anxiete',
        'stress': 'stress',
        'solitude': 'solitude',
        'hospitali': 'occupation_hospitaliere',
        'soins': 'acces_soins'
    }
    dim_temporelle = {
        'années': 'par_annees',
        'evolution': 'par_annees',
        'annuel': 'par_annees',
        'mois': 'par_mois',
        'mensuel': 'par_mois'
    }

    q_lower = query.lower()
    type_donnee = 'donnees'
    for key, val in types_donnees.items():
        if key in q_lower:
            type_donnee = val
            break

    dimension = 'evolution'
    for key, val in dim_temporelle.items():
        if key in q_lower:
            dimension = val
            break

    filename = f"{type_donnee}_{dimension}.png"
    # Assurer un nom valide de fichier
    return re.sub(r'[^a-zA-Z0-9_\-\.]+', '_', filename)
