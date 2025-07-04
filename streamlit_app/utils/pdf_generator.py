# streamlit_app/utils/pdf_generator.py

import io
import os
import re
import tempfile
import unicodedata
from typing import Optional

from fpdf import FPDF
from matplotlib.figure import Figure


def make_report_pdf(text: str, fig: Optional[Figure] = None) -> bytes:
    """
    Génère un rapport au format PDF à partir d'un texte (Markdown léger) et
    d'une figure Matplotlib optionnelle.

    Args:
        text: Le contenu textuel du rapport (Markdown simplifié).
        fig:  Une instance de matplotlib.figure.Figure ou None.

    Returns:
        Le contenu du PDF encodé en bytes.
    """
    # 1) Nettoyage du texte : suppression des fences et normalisation
    lines = []
    for line in text.splitlines():
        if re.match(r"^\s*-{3,}\s*$", line):
            continue
        if line.strip().startswith("```"):
            continue
        lines.append(line)
    cleaned = "\n".join(lines)
    cleaned = cleaned.replace("**", "").replace("*", "")
    subs = {
        "–": "-", "—": "-", "‘": "'", "’": "'", "“": '"', "”": '"', "•": "-"
    }
    for src, tgt in subs.items():
        cleaned = cleaned.replace(src, tgt)
    cleaned = unicodedata.normalize("NFKD", cleaned).encode("ascii", "ignore").decode("ascii")

    # 2) Préparation de l'image PNG si la figure est fournie
    img_buf = io.BytesIO()
    if fig is not None:
        fig.savefig(img_buf, format="PNG", dpi=150, bbox_inches="tight")
    img_buf.seek(0)

    # 3) Recherche d'un marqueur de section "Visualisation" pour insertion du graphique
    marker = None
    for key in ("## Visualisation graphique", "## Visualisation des donnees"):
        if key in cleaned:
            marker = key
            break

    before, after = (cleaned, "")
    if marker:
        before, _, after = cleaned.partition(marker)

    # 4) Génération du PDF
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Rapport Santé - Québec", ln=True, align="C")
    pdf.ln(5)

    def _draw_block(block: str):
        for ln in block.split("\n"):
            txt = ln.strip()
            if not txt:
                pdf.ln(4)
                continue
            # Titres Markdown
            if txt.startswith("## "):
                pdf.set_font("Arial", "B", 14)
                pdf.multi_cell(0, 8, txt[3:].strip())
                pdf.ln(2)
            elif txt.startswith("### "):
                pdf.set_font("Arial", "B", 12)
                pdf.multi_cell(0, 7, txt[4:].strip())
                pdf.ln(1)
            # Listes
            elif txt.startswith("- "):
                pdf.set_font("Arial", size=12)
                pdf.cell(6)
                pdf.multi_cell(0, 7, txt)
            else:
                pdf.set_font("Arial", size=12)
                pdf.multi_cell(0, 7, txt)

    # 5) Dessine la partie avant le graphique
    _draw_block(before)

    # 6) Insère le graphique si présent
    if fig is not None:
        pdf.ln(5)
        if marker:
            pdf.set_font("Arial", "B", 14)
            pdf.multi_cell(0, 8, marker)
            pdf.ln(2)
        # Enregistrer l'image dans un fichier temporaire
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp.write(img_buf.getvalue())
            tmp.flush()
            pdf.image(tmp.name, x=15, w=180)
        os.unlink(tmp.name)
        pdf.ln(5)

    # 7) Dessine la partie après le graphique
    if after:
        _draw_block(after)

    # 8) Retourne le PDF en bytes
    return pdf.output(dest="S").encode("latin-1", "ignore")
