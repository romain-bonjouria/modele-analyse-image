from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

try:
    import chromadb
except ImportError:  # pragma: no cover - dépend de l'environnement
    chromadb = None  # type: ignore[assignment]
    CHROMADB_IMPORT_ERROR = "chromadb non importable (module manquant)."
except Exception as exc:  # pragma: no cover - dépend de l'environnement
    chromadb = None  # type: ignore[assignment]
    CHROMADB_IMPORT_ERROR = f"chromadb import error: {exc}"
else:
    CHROMADB_IMPORT_ERROR = ""

try:
    import ollama
except ImportError:  # pragma: no cover - dépend de l'environnement
    ollama = None  # type: ignore[assignment]


SUPPORTED_EXTENSIONS = {".txt", ".md", ".py", ".json", ".csv", ".pdf"}


class _FallbackCollection:
    """Fallback vector store used when chromadb is unavailable."""

    def __init__(self) -> None:
        self._rows: dict[str, dict[str, object]] = {}

    @staticmethod
    def _cosine_distance(a: list[float], b: list[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        return 1.0 - dot

    def get(self, include: list[str] | None = None) -> dict[str, list[dict[str, object]]]:
        del include
        return {"metadatas": [row["metadata"] for row in self._rows.values()]}

    def upsert(
        self,
        ids: list[str],
        documents: list[str],
        metadatas: list[dict[str, str | int]],
        embeddings: list[list[float]],
    ) -> None:
        for i, chunk_id in enumerate(ids):
            self._rows[chunk_id] = {
                "document": documents[i],
                "metadata": metadatas[i],
                "embedding": embeddings[i],
            }

    def query(
        self,
        query_embeddings: list[list[float]],
        n_results: int,
        include: list[str] | None = None,
    ) -> dict[str, list[list[object]]]:
        del include
        if not query_embeddings:
            return {"documents": [[]], "metadatas": [[]]}

        query_embedding = query_embeddings[0]
        scored: list[tuple[float, dict[str, object]]] = []
        for row in self._rows.values():
            emb = row.get("embedding")
            if isinstance(emb, list):
                scored.append((self._cosine_distance(query_embedding, emb), row))

        scored.sort(key=lambda x: x[0])
        top = [r for _, r in scored[: max(1, n_results)]]

        return {
            "documents": [[str(r.get("document", "")) for r in top]],
            "metadatas": [[r.get("metadata", {}) for r in top]],
        }


class _FallbackClient:
    def __init__(self) -> None:
        self._collections: dict[str, _FallbackCollection] = {}

    def get_or_create_collection(self, name: str) -> _FallbackCollection:
        if name not in self._collections:
            self._collections[name] = _FallbackCollection()
        return self._collections[name]


@dataclass
class DocumentChunk:
    chunk_id: str
    text: str
    source: str
    chunk_index: int


@dataclass
class RAGAnswer:
    answer: str
    sources: list[str]


class ConversationMemory:
    """Stocke l'historique d'une conversation.

    La structure est déjà prête pour plusieurs conversations afin d'ajouter
    le multi-chat plus tard sans refonte majeure.
    """

    def __init__(self) -> None:
        self._messages_by_conversation: dict[str, list[dict[str, str]]] = {}

    def get(self, conversation_id: str = "default") -> list[dict[str, str]]:
        return self._messages_by_conversation.setdefault(conversation_id, [])

    def append(self, role: str, content: str, conversation_id: str = "default") -> None:
        self.get(conversation_id).append({"role": role, "content": content})


class OllamaChromaRAG:
    def __init__(
        self,
        chroma_path: str = "./chroma_db",
        collection_name: str = "documents",
        embedding_model: str = "nomic-embed-text",
        chat_model: str = "llama3.1",
        top_k: int = 4,
    ) -> None:
        if ollama is None:
            raise RuntimeError(
                "Dépendances manquantes. Installez ollama via requirements.txt."
            )
        self.embedding_model = embedding_model
        self.chat_model = chat_model
        self.top_k = top_k
        self.memory = ConversationMemory()

        self.using_fallback_store = chromadb is None
        if chromadb is None:
            self._client = _FallbackClient()
        else:
            self._client = chromadb.PersistentClient(path=chroma_path)
        self._collection = self._client.get_or_create_collection(name=collection_name)

    def list_sources(self) -> list[str]:
        data = self._collection.get(include=["metadatas"])
        metadatas = data.get("metadatas", [])
        return sorted({m.get("source", "") for m in metadatas if m and m.get("source")})

    @staticmethod
    def _read_pdf(path: Path) -> str:
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise RuntimeError("pypdf est requis pour lire les PDF.") from exc

        reader = PdfReader(str(path))
        return "\n".join((page.extract_text() or "") for page in reader.pages)

    @staticmethod
    def _read_file(path: Path) -> str:
        suffix = path.suffix.lower()
        if suffix == ".pdf":
            return OllamaChromaRAG._read_pdf(path)
        return path.read_text(encoding="utf-8", errors="ignore")

    @staticmethod
    def _split_text(text: str, chunk_size: int = 800, overlap: int = 120) -> list[str]:
        clean = " ".join(text.split())
        if not clean:
            return []
        if chunk_size <= overlap:
            raise ValueError("chunk_size doit être strictement supérieur à overlap")

        chunks: list[str] = []
        start = 0
        while start < len(clean):
            end = min(start + chunk_size, len(clean))
            chunks.append(clean[start:end])
            if end == len(clean):
                break
            start = end - overlap
        return chunks

    @staticmethod
    def _chunk_id(path: Path, chunk_index: int, content: str) -> str:
        digest = hashlib.sha1(content.encode("utf-8")).hexdigest()[:12]
        return f"{path.as_posix()}::{chunk_index}::{digest}"

    def _embed(self, text: str) -> list[float]:
        response = ollama.embeddings(model=self.embedding_model, prompt=text)
        return response["embedding"]

    def _iter_supported_files(self, root: Path) -> Iterable[Path]:
        for p in sorted(root.rglob("*")):
            if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS:
                yield p

    def ingest_folder(self, folder_path: str) -> int:
        folder = Path(folder_path)
        if not folder.exists() or not folder.is_dir():
            raise ValueError(f"Dossier invalide: {folder}")

        documents: list[str] = []
        metadatas: list[dict[str, str | int]] = []
        ids: list[str] = []
        embeddings: list[list[float]] = []

        for file_path in self._iter_supported_files(folder):
            content = self._read_file(file_path)
            for i, chunk in enumerate(self._split_text(content)):
                chunk_id = self._chunk_id(file_path.relative_to(folder), i, chunk)
                documents.append(chunk)
                metadatas.append({"source": str(file_path), "chunk_index": i})
                ids.append(chunk_id)
                embeddings.append(self._embed(chunk))

        if not documents:
            return 0

        # upsert pour éviter les doublons si on ré-ingère les mêmes fichiers
        self._collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=embeddings,
        )
        return len(documents)

    def ingest_files(self, files: list[tuple[str, bytes]], temp_dir: str = "/tmp/rag_uploads") -> int:
        temp_root = Path(temp_dir)
        temp_root.mkdir(parents=True, exist_ok=True)

        saved_dir = temp_root / "current_batch"
        if saved_dir.exists():
            for f in saved_dir.rglob("*"):
                if f.is_file():
                    f.unlink()
        saved_dir.mkdir(parents=True, exist_ok=True)

        for filename, content in files:
            target = saved_dir / Path(filename).name
            target.write_bytes(content)

        return self.ingest_folder(str(saved_dir))

    def _retrieve(self, question: str) -> tuple[str, list[str]]:
        question_embedding = self._embed(question)
        result = self._collection.query(
            query_embeddings=[question_embedding],
            n_results=self.top_k,
            include=["documents", "metadatas"],
        )

        docs = (result.get("documents") or [[]])[0]
        metas = (result.get("metadatas") or [[]])[0]

        contexts: list[str] = []
        sources: list[str] = []
        for d, m in zip(docs, metas):
            if not d:
                continue
            contexts.append(d)
            if m and m.get("source"):
                sources.append(str(m["source"]))

        return "\n\n".join(contexts), sorted(set(sources))

    def ask(self, question: str, conversation_id: str = "default") -> RAGAnswer:
        context, sources = self._retrieve(question)
        history = self.memory.get(conversation_id)

        system_prompt = (
            "Tu es un assistant RAG. Réponds en français de manière concise et fiable. "
            "Utilise uniquement le CONTEXTE fourni. Si l'information n'est pas présente, dis-le clairement."
        )

        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(history[-8:])
        messages.append(
            {
                "role": "user",
                "content": f"CONTEXTE:\n{context or 'Aucun contexte'}\n\nQUESTION: {question}",
            }
        )

        response = ollama.chat(model=self.chat_model, messages=messages)
        answer = response["message"]["content"]

        self.memory.append("user", question, conversation_id)
        self.memory.append("assistant", answer, conversation_id)

        return RAGAnswer(answer=answer, sources=sources)


def ollama_healthcheck() -> tuple[bool, str]:
    if ollama is None:
        return False, "Package ollama non installé."
    try:
        ollama.list()
        return True, "Connexion Ollama OK"
    except Exception as exc:  # pragma: no cover - dépend de l'environnement
        return False, f"Ollama indisponible: {exc}"


def chromadb_status_message() -> str:
    if chromadb is None:
        return CHROMADB_IMPORT_ERROR or "chromadb indisponible."
    return "ChromaDB OK"


def ollama_available_models() -> list[str]:
    if ollama is None:
        return []
    try:
        payload = ollama.list()
        models = payload.get("models", [])
        names: list[str] = []
        for model in models:
            if isinstance(model, dict):
                names.append(str(model.get("name", "")))
        return sorted(n for n in names if n)
    except Exception:  # pragma: no cover - dépend de l'environnement
        return []


def ollama_ensure_models(model_names: list[str]) -> tuple[bool, str]:
    if ollama is None:
        return False, "Package ollama non installé."
    try:
        existing = set(ollama_available_models())
        for name in model_names:
            if name in existing:
                continue
            ollama.pull(name)
        return True, "Modèles Ollama prêts."
    except Exception as exc:  # pragma: no cover - dépend de l'environnement
        return False, f"Impossible de préparer les modèles Ollama: {exc}"


def get_default_rag() -> OllamaChromaRAG:
    return OllamaChromaRAG(
        chroma_path=os.getenv("CHROMA_PATH", "./chroma_db"),
        collection_name=os.getenv("CHROMA_COLLECTION", "documents"),
        embedding_model=os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text"),
        chat_model=os.getenv("OLLAMA_CHAT_MODEL", "llama3.1"),
    )
