from __future__ import annotations

import os

import streamlit as st

from rag_service import get_default_rag, ollama_available_models, ollama_healthcheck


st.set_page_config(page_title="RAG Chroma + Ollama", layout="wide")
st.title("📚 RAG Documents (ChromaDB + Ollama)")

if "rag" not in st.session_state:
    st.session_state.rag = get_default_rag()
if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = "default"

rag = st.session_state.rag

ok, status = ollama_healthcheck()
st.info(status)

with st.sidebar:
    st.header("Configuration")
    st.caption("La structure interne supporte déjà plusieurs conversations. Pour le moment, une seule conversation active est utilisée.")
    st.text_input("Conversation ID", key="conversation_id", disabled=True)
    st.divider()
    st.caption("Déploiement client (.exe)")
    st.code("1) Installer Ollama\n2) ollama pull llama3.1\n3) ollama pull nomic-embed-text")
    st.caption(f"OLLAMA_CHAT_MODEL={os.getenv('OLLAMA_CHAT_MODEL', 'llama3.1')}")
    st.caption(f"OLLAMA_EMBED_MODEL={os.getenv('OLLAMA_EMBED_MODEL', 'nomic-embed-text')}")
    models = ollama_available_models()
    if models:
        st.caption("Modèles locaux détectés :")
        for model_name in models:
            st.caption(f"- {model_name}")
    else:
        st.warning("Aucun modèle Ollama détecté.")

col1, col2 = st.columns(2)

with col1:
    st.subheader("1) Déposer un dossier serveur")
    folder_path = st.text_input("Chemin du dossier", placeholder="/data/docs")
    if st.button("Indexer le dossier"):
        if not folder_path:
            st.warning("Veuillez renseigner un chemin de dossier.")
        else:
            with st.spinner("Indexation en cours..."):
                try:
                    nb_chunks = rag.ingest_folder(folder_path)
                    st.success(f"Indexation terminée: {nb_chunks} chunk(s) ajoutés/mis à jour.")
                except Exception as exc:
                    st.error(f"Erreur pendant l'indexation: {exc}")

with col2:
    st.subheader("2) Upload de fichiers")
    uploads = st.file_uploader(
        "Ajoutez un ou plusieurs documents",
        type=["txt", "md", "pdf", "py", "json", "csv"],
        accept_multiple_files=True,
    )

    if st.button("Indexer les fichiers uploadés"):
        if not uploads:
            st.warning("Aucun fichier uploadé.")
        else:
            with st.spinner("Upload + indexation..."):
                data = [(u.name, u.getvalue()) for u in uploads]
                try:
                    nb_chunks = rag.ingest_files(data)
                    st.success(f"Indexation terminée: {nb_chunks} chunk(s) ajoutés/mis à jour.")
                except Exception as exc:
                    st.error(f"Erreur pendant l'indexation: {exc}")

st.divider()
st.subheader("3) Chat avec vos documents")

question = st.text_input("Votre question")
if st.button("Poser la question"):
    if not question.strip():
        st.warning("Veuillez saisir une question.")
    else:
        with st.spinner("Génération en cours..."):
            try:
                response = rag.ask(question=question, conversation_id=st.session_state.conversation_id)
                st.markdown("### Réponse")
                st.write(response.answer)

                st.markdown("### Sources")
                if response.sources:
                    for src in response.sources:
                        st.code(src)
                else:
                    st.write("Aucune source retrouvée dans la base.")
            except Exception as exc:
                st.error(f"Erreur pendant la génération: {exc}")

st.divider()
st.subheader("Documents indexés")
for src in rag.list_sources():
    st.caption(f"- {src}")
