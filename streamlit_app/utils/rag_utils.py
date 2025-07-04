# streamlit_app/utils/rag_utils.py
import streamlit as st
import chromadb
from chromadb.utils import embedding_functions
import numpy as np
from typing import List, Dict, Any
from sklearn.metrics.pairwise import cosine_similarity

def init_collection(
    model_name: str = "all-MiniLM-L6-v2",
    collection_name: str = "sante_docs"
) -> chromadb.api.models.Collection.Collection:
    """
    Initialise (ou récupère) la collection ChromaDB avec la fonction d'embedding
    SentenceTransformer all-MiniLM-L6-v2.
    """
    embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=model_name
    )
    client = chromadb.Client()
    collection = client.get_or_create_collection(
        name=collection_name,
        embedding_function=embedding_fn
    )
    return collection

def index_default_documents(collection: chromadb.api.models.Collection.Collection) -> None:
    """
    Indexe un ensemble de documents factices (fake_docs + respiratory_docs) dans la collection.
    """
    fake_docs = [
        # Troubles respiratoires (10 ans)
        {"id": "1", "content": "Évolution des troubles respiratoires dans la région de Québec : 2014 (12%), 2015 (14%), 2016 (13%), 2017 (15%), 2018 (16%), 2019 (14%), 2020 (15%), 2021 (20%), 2022 (27%), 2023 (25%). La hausse significative depuis 2020 est attribuée à plusieurs facteurs environnementaux."},
        {"id": "2", "content": "Cas d'asthme à Montréal sur 10 ans : 2014 (18%), 2015 (17%), 2016 (19%), 2017 (20%), 2018 (21%), 2019 (20%), 2020 (22%), 2021 (19%), 2022 (24%), 2023 (26%). La pollution urbaine reste un facteur majeur."},
        # Santé mentale (5 ans)
        {"id": "3", "content": "Taux d'anxiété chez les jeunes adultes à Montréal : 2019 (24%), 2020 (28%), 2021 (30%), 2022 (31%), 2023 (32%). La pandémie a marqué un tournant dans cette progression."},
        {"id": "4", "content": "Évolution de la dépression chez les étudiants québécois : 2019 (20%), 2020 (25%), 2021 (27%), 2022 (26%), 2023 (28%). Les périodes d'examens montrent des pics à 35%."},
        # Occupation hospitalière (5 ans)
        {"id": "5", "content": "Taux d'occupation des urgences à Montréal : 2019 (75%), 2020 (70%), 2021 (78%), 2022 (85%), 2023 (88%). Les pics hivernaux dépassent souvent 95%."},
        {"id": "6", "content": "Évolution de la surcharge hospitalière à Québec : 2019 (70%), 2020 (65%), 2021 (72%), 2022 (78%), 2023 (82%). Les périodes de grippe saisonnière impactent fortement ces taux."},
        # Accès aux soins (7 ans)
        {"id": "7", "content": "Accès aux médecins de famille à Montréal : 2017 (65%), 2018 (68%), 2019 (70%), 2020 (72%), 2021 (73%), 2022 (74%), 2023 (75%). L'amélioration est constante mais reste insuffisante."},
        {"id": "8", "content": "Délais d'attente moyens pour les spécialistes (en mois) : 2017 (4.2), 2018 (4.0), 2019 (3.8), 2020 (4.5), 2021 (4.2), 2022 (3.8), 2023 (3.5). Les variations reflètent les défis du système de santé."},
        # Habitudes de vie (6 ans)
        {"id": "9", "content": "Taux d'activité physique régulière chez les 18-30 ans : 2018 (35%), 2019 (38%), 2020 (32%), 2021 (36%), 2022 (42%), 2023 (45%). La reprise post-pandémie montre une tendance positive."},
        {"id": "10", "content": "Consommation quotidienne de fruits et légumes à Québec : 2018 (55%), 2019 (58%), 2020 (60%), 2021 (62%), 2022 (64%), 2023 (65%). Les campagnes de sensibilisation ont un impact positif."},
        # Vaccination et dépistage (5 ans)
        {"id": "11", "content": "Couverture vaccinale grippe chez les 65+ ans : 2019 (60%), 2020 (65%), 2021 (68%), 2022 (70%), 2023 (72%). L'augmentation reflète une meilleure sensibilisation."},
        {"id": "12", "content": "Participation au dépistage du cancer du sein : 2019 (58%), 2020 (55%), 2021 (60%), 2022 (63%), 2023 (65%). La baisse de 2020 est liée aux restrictions sanitaires."}
    ]

    respiratory_docs = [
        {"id": "resp_mtl",    "content": "Montréal – Évolution des troubles respiratoires sur 10 ans : 2014 (12 %), 2015 (14 %), 2016 (13 %), 2017 (15 %), 2018 (16 %), 2019 (14 %), 2020 (15 %), 2021 (20 %), 2022 (27 %), 2023 (25 %)."},
        {"id": "resp_qc",     "content": "Québec – Évolution des troubles respiratoires sur 10 ans : 2014 (10 %), 2015 (11 %), 2016 (12 %), 2017 (14 %), 2018 (15 %), 2019 (13 %), 2020 (14 %), 2021 (18 %), 2022 (22 %), 2023 (24 %)."},
        {"id": "resp_levis",  "content": "Lévis – Évolution des troubles respiratoires sur 10 ans : 2014 (8 %), 2015 (9 %), 2016 (11 %), 2017 (13 %), 2018 (14 %), 2019 (12 %), 2020 (13 %), 2021 (17 %), 2022 (21 %), 2023 (23 %)."},
        {"id": "resp_bsl",    "content": "Bas-Saint-Laurent – Évolution des troubles respiratoires sur 10 ans : 2014 (14 %), 2015 (15 %), 2016 (14 %), 2017 (16 %), 2018 (18 %), 2019 (16 %), 2020 (17 %), 2021 (22 %), 2022 (28 %), 2023 (26 %)."},
        {"id": "resp_tr",     "content": "Trois-Rivières – Évolution des troubles respiratoires sur 10 ans : 2014 (9 %), 2015 (10 %), 2016 (11 %), 2017 (12 %), 2018 (13 %), 2019 (11 %), 2020 (12 %), 2021 (16 %), 2022 (20 %), 2023 (22 %)."}
    ]

    all_docs = fake_docs + respiratory_docs
    collection.add(
        documents=[doc["content"] for doc in all_docs],
        ids=[doc["id"] for doc in all_docs]
    )

def get_rag_context(
    collection: chromadb.api.models.Collection.Collection,
    user_query: str,
    all_docs: bool = False
) -> str:
    """
    Récupère soit tous les documents (all_docs=True), soit les 2 plus
    pertinents pour user_query.
    """
    if all_docs:
        docs = collection.get()["documents"]
        return "\n".join(docs)
    results = collection.query(query_texts=[user_query], n_results=2)
    return "\n".join(results["documents"][0])

def get_rag_context_adaptatif(conversation, embedding_fn, threshold=0.7):
    # Récupère les deux dernières questions utilisateur
    user_qs = [m["content"] for m in conversation if m["role"] == "user"]
    if not user_qs:
        return ""
    if len(user_qs) < 2:
        query = user_qs[-1]
    else:
        q_prev, q_cur = user_qs[-2], user_qs[-1]
        emb_prev = np.array(embedding_fn([q_prev])).reshape(1, -1)
        emb_cur  = np.array(embedding_fn([q_cur])).reshape(1, -1)
        sim = cosine_similarity(emb_prev, emb_cur)[0, 0]
        query = q_prev + " " + q_cur if sim >= threshold else q_cur

    # On interroge Chroma via st.session_state.collection
    results = st.session_state.collection.query(
        query_texts=[query], n_results=2
    )
    return "\n".join(results["documents"][0])
