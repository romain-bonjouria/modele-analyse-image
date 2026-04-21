from __future__ import annotations

import os

import streamlit as st

import rag_service as rag_module

chromadb_status_message = getattr(rag_module, "chromadb_status_message", lambda: "Diagnostic indisponible.")
get_default_rag = getattr(rag_module, "get_default_rag")
ollama_available_models = getattr(rag_module, "ollama_available_models", lambda: [])
ollama_healthcheck = getattr(rag_module, "ollama_healthcheck", lambda: (False, "Healthcheck indisponible."))


def ollama_ensure_models_safe(model_names: list[str]) -> tuple[bool, str]:
    fn = getattr(rag_module, "ollama_ensure_models", None)
    if fn is None:
        return (
            False,
            "La fonction ollama_ensure_models est absente du runtime packagé. Regénérez l'exécutable.",
        )
    return fn(model_names)


st.set_page_config(page_title="RAG Chroma + Ollama", layout="wide")
st.title("📚 RAG Documents (ChromaDB + Ollama)")

if "rag" not in st.session_state:
    try:
        st.session_state.rag = get_default_rag()
        st.session_state.rag_init_error = ""
    except Exception as exc:
        st.session_state.rag = None
        st.session_state.rag_init_error = str(exc)
if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = "default"

rag = st.session_state.rag
rag_init_error = st.session_state.get("rag_init_error", "")

ok, status = ollama_healthcheck()
st.info(status)
if rag_init_error:
    st.error(f"Initialisation RAG impossible: {rag_init_error}")
    st.caption("Vérifiez que l'exécutable a été régénéré et que les dépendances sont bien embarquées.")
elif rag is not None and getattr(rag, "using_fallback_store", False):
    st.warning("ChromaDB indisponible: un store local de secours est utilisé pour cette session.")
    st.caption(f"Diagnostic ChromaDB: {chromadb_status_message()}")

with st.sidebar:
    st.header("Configuration")
    st.caption("La structure interne supporte déjà plusieurs conversations. Pour le moment, une seule conversation active est utilisée.")
    st.text_input("Conversation ID", key="conversation_id", disabled=True)
    st.divider()
    st.caption("Déploiement client (.exe)")
    st.code("1) Installer Ollama\n2) ollama pull llama3.1\n3) ollama pull nomic-embed-text")
    st.caption(f"OLLAMA_CHAT_MODEL={os.getenv('OLLAMA_CHAT_MODEL', 'llama3.1')}")
    st.caption(f"OLLAMA_EMBED_MODEL={os.getenv('OLLAMA_EMBED_MODEL', 'nomic-embed-text')}")
    if st.button("Préparer automatiquement les modèles"):
        if rag is None:
            st.error("RAG non initialisé. Impossible de préparer les modèles.")
            st.stop()
        with st.spinner("Téléchargement des modèles Ollama..."):
            target_models = [
                os.getenv("OLLAMA_CHAT_MODEL", "llama3.1"),
                os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text"),
            ]
            done, msg = ollama_ensure_models_safe(target_models)
            if done:
                st.success(msg)
            else:
                st.error(msg)

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
                    if rag is None:
                        raise RuntimeError("RAG non initialisé")
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
                    if rag is None:
                        raise RuntimeError("RAG non initialisé")
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
                if rag is None:
                    raise RuntimeError("RAG non initialisé")
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
if rag is None:
    st.caption("RAG indisponible: aucune source affichée.")
else:
    for src in rag.list_sources():
        st.caption(f"- {src}")
