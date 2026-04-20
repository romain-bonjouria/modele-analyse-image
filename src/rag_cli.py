from __future__ import annotations

import argparse

from rag_service import get_default_rag


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="CLI RAG (ChromaDB + Ollama)")
    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest_parser = subparsers.add_parser("ingest", help="Indexer un dossier")
    ingest_parser.add_argument("folder", help="Chemin du dossier à indexer")

    ask_parser = subparsers.add_parser("ask", help="Poser une question")
    ask_parser.add_argument("question", help="Question utilisateur")
    ask_parser.add_argument("--conversation-id", default="default")

    subparsers.add_parser("sources", help="Lister les sources indexées")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    rag = get_default_rag()

    if args.command == "ingest":
        chunks = rag.ingest_folder(args.folder)
        print(f"{chunks} chunk(s) indexés.")
        return

    if args.command == "ask":
        result = rag.ask(question=args.question, conversation_id=args.conversation_id)
        print("\nRéponse:\n")
        print(result.answer)
        print("\nSources:")
        for src in result.sources:
            print(f"- {src}")
        return

    if args.command == "sources":
        for source in rag.list_sources():
            print(f"- {source}")


if __name__ == "__main__":
    main()
