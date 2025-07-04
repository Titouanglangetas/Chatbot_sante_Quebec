# streamlit_app/main.py

import os
import uuid
import io
import re
import json
import base64
import streamlit as st
from datetime import date
from dotenv import load_dotenv

# -- Utils --
from utils.history       import load_history, save_history
from utils.llm_api       import get_llm_response
from utils.rag_utils     import (
    init_collection,
    index_default_documents,
    get_rag_context,
    get_rag_context_adaptatif,
)
from utils.viz           import get_graph_data, generate_graph_filename
from utils.pdf_generator import make_report_pdf
from utils.auth import check_auth
from chromadb.utils import embedding_functions

# Pour l’exécution de blocs matplotlib dynamiques
import matplotlib.pyplot as plt
import numpy as np
import chromadb

def load_css(path: str) -> None:
    """Charge un fichier CSS externe dans Streamlit."""
    if os.path.exists(path):
        with open(path, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Exemples de questions pour tester
example_questions = [
    "Montre l'évolution des troubles respiratoires à Québec sur les 10 dernières années.",
    "Compare les cas d'asthme à Montréal entre 2014 et 2023.",
    "Trace l'évolution de l'anxiété chez les jeunes adultes depuis 2019.",
    "Affiche la progression du taux d'occupation des urgences à Montréal depuis 2019.",
    "Comment a évolué l'accès aux médecins de famille à Montréal depuis 2017 ?",
    "Montre l'évolution des délais d'attente pour les spécialistes depuis 2017.",
    "Trace la courbe de l'activité physique chez les 18-30 ans depuis 2018.",
    "Comment a évolué la couverture vaccinale chez les 65+ ans depuis 2019 ?",
    "Montre la progression du dépistage du cancer du sein entre 2019 et 2023.",
    "Compare la consommation de fruits et légumes à Québec depuis 2018."
]
def clear_report() -> None:
    """Réinitialise l’état du panneau rapport."""
    st.session_state.report_type = "➤ Sélectionnez…"
    st.session_state.report_text = None
    st.session_state.report_fig  = None


#generation du titre de la conversation
def generate_smart_title(user_query):
    words = user_query.split()
    if len(words) <= 3:
        return user_query
    return " ".join(words[:3]) + "..."

def analyze_question(question: str, context: str) -> dict:
    """
    Appelle le modèle pour décider :
      - si les données sont disponibles,
      - si on doit tracer un graphique,
      - le type de réponse attendu.
    Retourne un dict {data_available, needs_visualization, response_type, explanation}.
    """
    prompt = f"""Tu es un assistant spécialisé dans l'analyse...
Question : {question}
Contexte : {context}

Réponds uniquement avec un JSON :
{{"data_available":bool,"needs_visualization":bool,"response_type":"graph"/"text","explanation":"..."}}
"""
    raw = get_llm_response(prompt)
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    if m:
        return json.loads(m.group())
    # fallback par défaut
    return {
        "data_available": True,
        "needs_visualization": any(k in question.lower() for k in ["montre","trace","affiche","compare"]),
        "response_type": "graph" if "montre" in question.lower() else "text",
        "explanation": "Analyse automatique par défaut."
    }


def get_graph_description(question: str, graph_data: dict, rag_context: str) -> str:
    """
    Formule un prompt pour décrire factuellement le graphique,
    à partir des données extraites et du contexte RAG.
    """
    prompt = f"""Tu es un assistant...
Contexte : {rag_context}

Données graphiques :
Titre : {graph_data.get("title")}
X : {graph_data.get("xlabel")} → {graph_data.get("xdata")}
Y : {graph_data.get("ylabel")} → {graph_data.get("ydata")}

Question : {question}

Donne 2–3 phrases factuelles en français."""
    return get_llm_response(prompt)


def main():
    # 0) page config
    st.set_page_config(page_title="Chat Santé Québec", layout="wide")
    load_dotenv()

    # 1) Auth
    if not check_auth():
        st.error("🔒 Vous devez être connecté·e pour accéder à cette page")
        return
    user = st.session_state.username

    # 2) CSS
    load_css("assets/chat_llm.css")

    if "collection" not in st.session_state:
        # 1) Créer et stocker la fonction d’embedding
        st.session_state.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        # 2) Créer le client Chroma et la collection
        st.session_state.chroma_client = chromadb.Client()
        st.session_state.collection = st.session_state.chroma_client.get_or_create_collection(
            name="sante_docs",
            embedding_function=st.session_state.embedding_fn
        )
        # 3) Indexer vos documents “fake_docs” + “respiratory_docs”
        index_default_documents(st.session_state.collection)

    # 4) Historique des conversations
    if "conversations" not in st.session_state:
        st.session_state.conversations = load_history(user)
        st.session_state.current_conversation_id = None
    if st.session_state.conversations:
        ids = [c["id"] for c in st.session_state.conversations]
        if st.session_state.current_conversation_id not in ids:
            st.session_state.current_conversation_id = ids[0]
    current_conversation = next(
        (c for c in st.session_state.conversations
         if c["id"] == st.session_state.current_conversation_id),
        None
    )

    # ─── 5) MENU RAPPORT ───────────────────────────────────────────────────────
    col_title, col_opts = st.columns([8, 2])
    with col_title:
        st.markdown("<h1>🤖 Chatbot Santé – Québec</h1>", unsafe_allow_html=True)
    with col_opts:
        DEFAULT = "➤ Sélectionnez…"
        report_types = [
            DEFAULT,
            "📈 Évolution troubles respiratoires",
            "📈 Évolution cas d'asthme",
            "📈 Taux d'anxiété Montréal",
            "📈 Surcharge hospitalière",
            "📄 Synthèse générale",
        ]
        report_type = st.selectbox("Type de rapport", report_types, key="report_type")

        if report_type != DEFAULT:
            communes = ["Toutes", "Québec", "Montréal", "Lévis", "Bas-Saint-Laurent"]
            commune = st.selectbox("Commune", communes, key="report_commune")
            today = date.today()
            default_start = today.replace(year=today.year - 1)
            start_date, end_date = st.date_input(
                "Période",
                value=(default_start, today),
                key="report_dates"
            )

            if st.button("✅ Générer le rapport", key="btn_report"):
                with st.spinner("🖨️ Génération du rapport…"):
                    if commune == "Toutes":
                        rag_ctx = get_rag_context(
                            st.session_state.collection,
                            report_type,
                            all_docs=True
                        )
                    else:
                        rag_ctx = get_rag_context(
                            st.session_state.collection,
                            f"{commune} {report_type}"
                        )

                    prompt = f"""
Tu es un assistant professionnel spécialisé en santé au Québec.

Type de rapport : {report_type}
Commune : {commune}
Période : {start_date.isoformat()} → {end_date.isoformat()}

Documents utiles (RAG) :
{rag_ctx}

Génère un rapport structuré en Markdown avec ces rubriques :
## Introduction

…ton texte…

## Points clés

…ton texte…

## Visualisation graphique

<!-- si pertinent, insère ici un bloc fenced Python pour tracer le graphique -->

## Analyse graphique

…ton texte…

## Conclusion

…ton texte…
"""
                    raw = get_llm_response(prompt)

                # ─── Traitement du code graphique (fenced ET inline) ───
                report_text, report_fig = raw, None

                # 1) Bloc fenced ```python ... ```
                m = re.search(r"```(?:python)?\n([\s\S]+?)```", raw)

                # 2) Fallback inline si pas de fenced
                if not m and "import matplotlib.pyplot" in raw:
                    m2 = re.search(r"(import matplotlib\.pyplot[\s\S]+?plt\.show\(\))", raw)
                    code = m2.group(1) if m2 else None
                else:
                    code = m.group(1) if m else None

                if code:
                    plt.close("all")
                    # Exécution safe
                    exec_globals = {"plt": plt, "np": np}
                    exec(code, exec_globals)
                    report_fig = plt.gcf()

                    # On retire le code du texte
                    if m:
                        report_text = raw.replace(m.group(0), "").strip()
                    else:
                        report_text = raw.replace(code, "").strip()

                # On stocke pour affichage ultérieur
                st.session_state.report_text = report_text
                st.session_state.report_fig  = report_fig


            st.button("❌ Fermer", on_click=clear_report, key="close_report")

    # ─── 6) AFFICHAGE DU RAPPORT ────────────────────────────────────────────────
    if st.session_state.get("report_text"):
        full_md = st.session_state.report_text
        fig     = st.session_state.report_fig

        # Métadonnées
        st.markdown("## 📄 Rapport généré")
        st.markdown("#### Informations du rapport")
        st.markdown(
            f"- **Type de rapport** : {st.session_state.report_type}  \n"
            f"- **Commune**         : {st.session_state.report_commune}  \n"
            f"- **Période**        : {st.session_state.report_dates[0]} → {st.session_state.report_dates[1]}"
        )
        st.markdown("---")

        # Découpage en sections
        HEADERS = [
            "## Introduction",
            "## Points clés",
            "## Visualisation graphique",
            "## Analyse graphique",
            "## Conclusion",
        ]
        sections = {}
        for i, h in enumerate(HEADERS):
            nxt = HEADERS[i+1] if i+1 < len(HEADERS) else None
            pat = (
                rf"{re.escape(h)}\s*(.*?)(?={re.escape(nxt)})"
                if nxt else rf"{re.escape(h)}\s*(.*)$"
            )
            m = re.search(pat, full_md, re.S)
            sections[h] = m.group(1).strip() if m else ""

        # Affichage
        st.markdown("### Introduction")
        st.markdown(sections["## Introduction"], unsafe_allow_html=True)

        st.markdown("### Points clés")
        st.markdown(sections["## Points clés"], unsafe_allow_html=True)

        st.markdown("### Visualisation graphique")
        if fig:
            st.pyplot(fig)
        else:
            st.markdown("_Aucun graphique à afficher._")

        st.markdown("### Analyse graphique")
        st.markdown(sections["## Analyse graphique"], unsafe_allow_html=True)

        st.markdown("### Conclusion")
        st.markdown(sections["## Conclusion"], unsafe_allow_html=True)

        st.markdown("---")

        # Télécharger en PDF
        pdf_bytes = make_report_pdf(full_md, fig)
        st.download_button(
            "📥 Télécharger le rapport (PDF)",
            data=pdf_bytes,
            file_name="rapport_sante_quebec.pdf",
            mime="application/pdf"
        )


    ####################
    # 6) Zone de chat
    ####################
    with st.form(key="chat_form"):
        col1, col2 = st.columns([8,1])
        with col1:
            user_input = st.text_input(
                "", placeholder="Posez votre question…",
                value=st.session_state.get("user_input",""),
                label_visibility="collapsed"
            )
        with col2:
            submitted = st.form_submit_button("💬")

    #traitement de la question de l'utilisateur
    if submitted and user_input:
        question = user_input
        st.session_state.user_input = ""  # Réinitialiser l'input après soumission
        # 1) Gestion "par rapport au graphique"
        ql = question.lower()
        followup_pattern = re.compile(
        r"\b(ce graphique|cette courbe|ce trac[eé]|\bdans ce graphique\b)", 
        flags=re.IGNORECASE
        )
        if followup_pattern.search(question) and st.session_state.get("last_graph_data"):
            gd  = st.session_state.last_graph_data
            ctx = st.session_state.last_graph_rag_context
            desc = get_graph_description(question, gd, ctx)
            current_conversation["messages"].append({"role": "user", "content": question})
            current_conversation["messages"].append({"role":"bot","content":desc,"type":"text"})
            save_history(user, st.session_state.conversations)
            st.rerun()

        current_conversation["messages"].append({"role": "user", "content": question})
        save_history(user, st.session_state.conversations)

        # Si c'est le premier message de la conversation, définir le titre
        if len(current_conversation["messages"]) == 1:
            current_conversation["title"] = generate_smart_title(question)
            save_history(user, st.session_state.conversations)
        # 1) Regroupe les N dernières questions utilisateur
        last_user_qs = [
            msg["content"] for msg in current_conversation["messages"]
            if msg["role"] == "user"
        ]
        # Choisis la fenêtre qui te convient (ici 2)
        rag_query = " ".join(last_user_qs[-2:])

        # 2) Interroge Chroma avec cette requête enrichie
        context = get_rag_context_adaptatif(
            current_conversation["messages"],
            st.session_state.embedding_fn
        )

        # Analyser la question avec le LLM
        analysis = analyze_question(question, context)
        
        # Nettoyer la question des éventuels marqueurs de code
        clean_question = re.sub(r'```.*?```', '', question, flags=re.DOTALL)

        if not analysis["data_available"]:
            # 1) Warning dans les logs
            warning_text="⚠️ Je n'ai pas trouvé de données santé pour cette question, je passe en mode conversation générale…"
            # 2) Enregistre le warning dans l'historique
            # 2) Affiche-le visuellement
            
            # 2) Construis un prompt simple sans RAG
            general_prompt = f"""
        Tu es un assistant polyvalent qui répond à toute question générale.
        Question : {clean_question}
        Réponds en français de manière concise.
        """

            # 3) Interroge l'API LLM en mode « général »
            reply = get_llm_response(general_prompt)
            combined = f"{warning_text}\n\n{reply}"
            # 4) Affiche et sauvegarde
            st.write(reply)
            current_conversation["messages"].append({"role":"bot","content":combined,"type": "text"})
            save_history(user, st.session_state.conversations)
            st.rerun()

        else:
            # L'historique du prompt doit inclure TOUS les messages de la conversation actuelle
            # S'assurer de n'envoyer que le contenu textuel au LLM, pas les images
            history_prompt_messages = []
            for msg in current_conversation["messages"]:
                if msg["role"] == "user":
                    history_prompt_messages.append(f"Utilisateur : {msg['content']}")
                elif msg["role"] == "bot" and msg.get("type") != "graph": # Ne pas inclure le contenu des images dans l'historique du prompt
                    history_prompt_messages.append(f"Assistant : {msg['content']}")
            # Limiter le contexte à 10 messages récents (ex : 5 échanges utilisateur/assistant)
            history_prompt_messages = history_prompt_messages[-10:]

            history_prompt = "\n".join(history_prompt_messages)

            full_prompt = f"""Tu es un assistant destiné aux professionnels de santé au Québec.
    IMPORTANT : Tu dois TOUJOURS répondre en FRANÇAIS, quelle que soit la langue de la question.

    Voici des documents utiles :
    {context}

    Historique de la conversation :
    {history_prompt}

    Question de l'utilisateur : {clean_question}

    Instructions STRICTES :
    1. Tu DOIS répondre UNIQUEMENT en français
    2. Si les données demandées ne sont pas disponibles dans le contexte, explique clairement pourquoi tu ne peux pas répondre
    3. Si la question demande une visualisation (selon l'analyse) :
    - Fournis UNIQUEMENT le code matplotlib nécessaire
    - NE donne AUCUNE autre explication
    4. Si la question ne demande PAS de visualisation :
    - Donne une réponse claire et concise en français
    - N'inclus PAS de code
    - Concentre-toi sur les informations pertinentes

    Type de réponse attendu : {analysis['response_type']}"""

            with st.spinner("💬 Réflexion en cours..."):
                bot_reply_raw = get_llm_response(full_prompt)

            if analysis["needs_visualization"]:
                try:
                    match = re.search(r"(import matplotlib\.pyplot[\s\S]+?plt\.show\(\))", bot_reply_raw)
                    if match:
                        code_to_exec = match.group(1)
                        # Ajouter des configurations matplotlib pour améliorer la lisibilité
                        code_to_exec = """
import matplotlib.pyplot as plt
plt.style.use('bmh')  # Style intégré à matplotlib
plt.figure(figsize=(12, 6))
plt.rcParams['axes.grid'] = True
plt.rcParams['grid.alpha'] = 0.3
""" + code_to_exec
                        exec_globals = {"plt": plt, "np": np}
                        try:
                            # Effacer la figure précédente pour éviter les superpositions
                            plt.clf()
                            exec(code_to_exec, exec_globals)
                            
                            # Extraire les données du graphique
                            graph_data = get_graph_data(plt.gcf())
                            # juste après avoir généré et sauvegardé graph_data
                            st.session_state.last_graph_data = graph_data
                            st.session_state.last_graph_rag_context = context

                            # Obtenir une description pertinente du LLM basée sur le contexte RAG
                            description = get_graph_description(question, graph_data, context)
                            
                            # Sauvegarder le graphique en format PNG et encoder en base64
                            img_buf = io.BytesIO()
                            plt.gcf().savefig(img_buf, format='png', dpi=300, bbox_inches='tight')
                            img_buf.seek(0)
                            image_base64 = base64.b64encode(img_buf.getvalue()).decode('utf-8')
                            
                            # ⬅️ Ajouter d'abord la description textuelle
                            current_conversation["messages"].append({
                                "role": "bot",
                                "content": description,
                                "type": "text"
                            })
                            # Ajouter la description et les données de l'image au message
                            current_conversation["messages"].append({
                                "role": "bot", 
                                "content": description, 
                                "type": "graph", 
                                "image_base64": image_base64,
                                "original_query": question # Stocker la question originale pour le nom du fichier
                            })
                            save_history(user, st.session_state.conversations)

                        except Exception as e:
                            error_msg = f"Désolé, je n'ai pas pu générer le graphique : {str(e)}"
                            st.error(error_msg)
                            current_conversation["messages"].append({"role": "bot", "content": error_msg})
                    else:
                        warning_msg = "Je n'ai pas pu générer de visualisation pour cette question."
                        st.warning(warning_msg)
                        current_conversation["messages"].append({"role": "bot", "content": warning_msg})
                except Exception as e:
                    error_msg = f"Une erreur s'est produite : {str(e)}"
                    st.error(error_msg)
                    current_conversation["messages"].append({"role": "bot", "content": error_msg})
                print("====== RAW LLM RESPONSE ======")
                print(bot_reply_raw)
                st.warning(f"Réponse brute : {bot_reply_raw}")

            else:
                try:
                    # Pour les réponses sans graphique, supprimer tout code Python de la réponse
                    cleaned_reply = re.sub(r'```.*?```', '', bot_reply_raw, flags=re.DOTALL).strip()
                    st.write(cleaned_reply)
                    current_conversation["messages"].append({
                        "role": "bot",
                        "content": cleaned_reply,
                        "type": "text"
                    })
                    save_history(user, st.session_state.conversations)

                except Exception as e:
                    st.error(f"❌ Erreur lors de l'affichage de la réponse texte : {str(e)}")
                    current_conversation["messages"].append({
                        "role": "bot",
                        "content": f"[Erreur] {str(e)}",
                        "type": "text"
                    })
                    save_history(user, st.session_state.conversations)

    

        st.rerun()


    ####################
    # 7) Sidebar : historique & actions
    ####################
    # Sidebar
    with st.sidebar:
        # ➕ Bouton pour démarrer une nouvelle conversation (plein largeur)
        if st.button(
            "➕ Nouvelle conversation",
            key="new_conv",
            use_container_width=True
        ):
            new_conv_id = str(uuid.uuid4())
            st.session_state.conversations.append({
                "id": new_conv_id,
                "title": "Nouvelle conversation",
                "messages": []
            })
            st.session_state.current_conversation_id = new_conv_id
            st.session_state.user_input = ""  # Réinitialiser l'input
            # Vider aussi le rapport s'il existe
            st.session_state.pop("report_text", None)
            st.session_state.pop("report_fig",  None)
            save_history(user, st.session_state.conversations)
            st.rerun()

        st.markdown("### 🧾 Historique des conversations")

        if st.session_state.conversations:
            # On affiche les plus récentes en premier
            sorted_convs = sorted(
                st.session_state.conversations,
                key=lambda x: x["id"],
                reverse=True
            )
            for conv in sorted_convs:
                is_current = (conv["id"] == st.session_state.current_conversation_id)

                # deux colonnes 4/1 pour titre + corbeille
                colA, colB = st.columns([4, 1], gap="small")

                # — bouton large de sélection
                with colA:
                    if st.button(
                        conv["title"],
                        key=f"conv_select_{conv['id']}",
                        type="primary" if is_current else "secondary",
                        use_container_width=True
                    ):
                        st.session_state.current_conversation_id = conv["id"]
                        st.rerun()

                # — petite corbeille à droite
                with colB:
                    if st.button(
                        "🗑️",
                        key=f"delete_{conv['id']}",
                        help="Supprimer cette conversation",
                        use_container_width=True
                    ):
                        st.session_state.conversations = [
                            c for c in st.session_state.conversations
                            if c["id"] != conv["id"]
                        ]
                        # si on supprime la conv courante, on en choisit une autre
                        if is_current:
                            st.session_state.current_conversation_id = (
                                st.session_state.conversations[0]["id"]
                                if st.session_state.conversations else None
                            )
                        save_history(user, st.session_state.conversations)
                        st.rerun()

                # — un petit trou sous chaque paire pour aérer
                st.markdown("<br>", unsafe_allow_html=True)
        else:
            st.info("Aucune conversation.")

        # Exemple de questions (si tu en as)
        st.markdown("### 💡 Exemples de questions")
        for i, q in enumerate(example_questions):
            if st.button(q, key=f"example_question_{i}", use_container_width=True):
                st.session_state.user_input = q
                st.rerun()

    ####################
    # 8) Affichage final de l’historique dans la page
    ####################
    chat_container = st.container()
    messages = current_conversation["messages"] if current_conversation else []
    blocks = []
    i = 0
    while i < len(messages):
        if messages[i]["role"] == "user":
            block = [messages[i]]
            j = i+1
            while j < len(messages) and messages[j]["role"]=="bot":
                block.append(messages[j])
                j += 1
            blocks.append(block)
            i = j
        else:
            i += 1

    for block in reversed(blocks):
        for msg in block:
            if msg["role"]=="user":
                st.markdown(
                    f"<div class='user-bubble'>{msg['content']}</div>",
                    unsafe_allow_html=True
                )
            elif msg.get("type")=="text":
                st.markdown(
                    f"<div class='bot-bubble'>{msg['content']}</div>",
                    unsafe_allow_html=True
                )
            elif msg.get("type")=="graph":
                img = base64.b64decode(msg["image_base64"])
                st.image(img, use_column_width=True)
                st.download_button(
                    "📥 Télécharger",
                    data=img,
                    file_name=generate_graph_filename(msg["original_query"]),
                    mime="image/png",
                    key=f"download_graph_{msg['original_query']}_{uuid.uuid4()}"
                )

        st.markdown("---")


if __name__ == "__main__":
    main()
