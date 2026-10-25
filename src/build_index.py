"""Construit (ou reconstruit) l'index FAISS : python -m src.build_index"""
from .vectorstore import VectorStore


def main() -> None:
    store = VectorStore.build()
    docs = {c["doc_id"] for c in store.chunks}
    print(f"Index construit : {len(docs)} documents, {len(store.chunks)} fragments, dimension {store.index.d}")


if __name__ == "__main__":
    main()
