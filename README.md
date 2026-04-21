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
- Mode de secours automatique si ChromaDB n'est pas disponible (store local temporaire).

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

Le binaire est généré ici : `dist/RagClientApp/RagClientApp.exe` (mode `onedir`, plus fiable que `onefile` avec les dépendances natives).

> Si vous voyez l'erreur `PackageNotFoundError: No package metadata was found for streamlit`, relancez ce script de build (il embarque les métadonnées streamlit nécessaires).
> Si vous voyez `ModuleNotFoundError: No module named 'rag_service'`, regénérez l'exécutable avec ce script mis à jour.
> Si vous voyez `RuntimeError: Dépendances manquantes. Installez chromadb et ollama...`, regénérez l'exécutable avec ce script (il embarque désormais `chromadb` et `ollama`).
> Si vous voyez `ImportError: cannot import name ... from rag_service`, supprimez le dossier `dist/RagClientApp` puis relancez le build (le script le fait désormais automatiquement).
> Si `ollama_ensure_models` est absent dans un ancien build, l'UI reste fonctionnelle et affiche un message de régénération.

### Côté client final

1. Lancer le script d'installation automatique :

   ```powershell
   powershell -ExecutionPolicy Bypass -File packaging/install_client.ps1
   ```

   Ce script gère automatiquement :
   - installation Ollama si absent,
   - ajout au `PATH` utilisateur,
   - téléchargement des modèles requis.

2. (Option manuelle) Charger les modèles (une seule fois) :

   ```powershell
   ollama pull llama3.1
   ollama pull nomic-embed-text
   ```

3. Si besoin, double-cliquer sur `dist/RagClientApp/RagClientApp.exe`.
   - Ne pas utiliser l'ancien `dist/RagClientApp.exe` (onefile legacy).
4. L'application démarre en local et s'ouvre dans le navigateur.
   - URL attendue: `http://localhost:8501`
   - Si SmartScreen bloque le lancement, cliquer sur `Informations complémentaires` puis `Exécuter quand même`.
   - Si la fenêtre se ferme immédiatement, lancer en debug: `powershell -NoExit -Command "& 'dist/RagClientApp/RagClientApp.exe'"`.

> Pour réduire les erreurs client, utilisez en priorité `packaging/install_client.ps1`.

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
