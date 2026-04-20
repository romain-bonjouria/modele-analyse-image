# RAG Documents avec ChromaDB + Ollama

Ce projet propose une base **RAG (Retrieval Augmented Generation)** en Python, avec :

- **ChromaDB** comme base vectorielle,
- **Ollama** pour les embeddings + génération LLM,
- une **interface Streamlit** pour déposer des dossiers/fichiers et poser des questions sur vos documents.

## Fonctionnalités

- Indexation d'un dossier local (txt, md, pdf, py, json, csv).
- Upload de fichiers via interface web.
- Recherche sémantique Top-K dans ChromaDB.
- Réponse LLM guidée par le contexte récupéré.
- Affichage des sources utilisées.
- Structure mémoire déjà prête pour le **multi-conversations** (à activer ensuite côté UI).

## Option 1 — Installation développeur

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Pré-requis Ollama :

```bash
ollama pull llama3.1
ollama pull nomic-embed-text
```

Lancer l'interface :

```bash
PYTHONPATH=src streamlit run src/streamlit_app.py
```

## Option 2 — Installation client avec un `.exe` (Windows)

### Côté équipe technique (une fois pour produire le binaire)

```powershell
powershell -ExecutionPolicy Bypass -File packaging/build_windows_exe.ps1
```

Le binaire est généré ici : `dist/RagClientApp.exe`.

### Côté client final

1. Installer **Ollama** sur le poste client.
2. Charger les modèles (une seule fois) :

   ```powershell
   ollama pull llama3.1
   ollama pull nomic-embed-text
   ```

3. Double-cliquer sur `RagClientApp.exe`.
4. L'application démarre en local et s'ouvre dans le navigateur.

> Le client n'a donc qu'un exécutable à lancer pour l'application.

## CLI (optionnelle)

Indexer un dossier :

```bash
PYTHONPATH=src python -m rag_cli ingest ./docs
```

Question/réponse :

```bash
PYTHONPATH=src python -m rag_cli ask "Quel est le processus d'installation ?"
```

Lister les sources :

```bash
PYTHONPATH=src python -m rag_cli sources
```

## Variables d'environnement

- `CHROMA_PATH` (défaut `./chroma_db`)
- `CHROMA_COLLECTION` (défaut `documents`)
- `OLLAMA_EMBED_MODEL` (défaut `nomic-embed-text`)
- `OLLAMA_CHAT_MODEL` (défaut `llama3.1`)

## Tests

```bash
PYTHONPATH=src pytest -q
```

---

### Prochaine étape prévue

La base technique supporte déjà plusieurs conversations via `conversation_id` dans `ConversationMemory`.
La prochaine évolution sera d'exposer cette capacité dans l'UI (création/sélection d'un thread).
