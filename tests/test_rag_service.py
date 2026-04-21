from pathlib import Path

from rag_service import (
    ConversationMemory,
    OllamaChromaRAG,
    _FallbackCollection,
    chromadb_status_message,
)


def test_split_text_creates_overlapping_chunks() -> None:
    text = "A" * 1000
    chunks = OllamaChromaRAG._split_text(text, chunk_size=300, overlap=50)

    assert len(chunks) >= 4
    assert chunks[0][-50:] == chunks[1][:50]


def test_split_text_validation() -> None:
    try:
        OllamaChromaRAG._split_text("hello", chunk_size=100, overlap=100)
        assert False, "A ValueError should have been raised"
    except ValueError as exc:
        assert "strictement supérieur" in str(exc)


def test_chunk_id_is_stable() -> None:
    path = Path("demo/doc.txt")
    c1 = OllamaChromaRAG._chunk_id(path, 0, "bonjour")
    c2 = OllamaChromaRAG._chunk_id(path, 0, "bonjour")
    c3 = OllamaChromaRAG._chunk_id(path, 1, "bonjour")

    assert c1 == c2
    assert c1 != c3


def test_memory_supports_isolated_conversations() -> None:
    memory = ConversationMemory()
    memory.append("user", "q1", conversation_id="convA")
    memory.append("assistant", "a1", conversation_id="convA")
    memory.append("user", "q2", conversation_id="convB")

    assert len(memory.get("convA")) == 2
    assert len(memory.get("convB")) == 1


def test_fallback_collection_can_upsert_and_query() -> None:
    col = _FallbackCollection()
    col.upsert(
        ids=["a", "b"],
        documents=["bonjour monde", "chatbot local"],
        metadatas=[{"source": "a.txt"}, {"source": "b.txt"}],
        embeddings=[[1.0, 0.0], [0.0, 1.0]],
    )

    res = col.query(query_embeddings=[[1.0, 0.0]], n_results=1)
    assert res["documents"][0][0] == "bonjour monde"


def test_chromadb_status_message_returns_text() -> None:
    assert isinstance(chromadb_status_message(), str)
