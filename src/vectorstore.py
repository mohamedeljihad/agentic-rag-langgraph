"""Vectorisation (sentence-transformers e5) et index FAISS (produit scalaire sur vecteurs normalisés)."""
from __future__ import annotations

import json
from functools import lru_cache

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from .config import CONFIG
from .ingestion import charger_corpus, construire_chunks


@lru_cache(maxsize=1)
def get_embedder() -> SentenceTransformer:
    return SentenceTransformer(CONFIG.embedding_model, device="cpu")


def embed_passages(textes: list[str]) -> np.ndarray:
    # Les modèles e5 attendent les préfixes « passage: » / « query: ».
    return get_embedder().encode([f"passage: {t}" for t in textes], normalize_embeddings=True,
                                 batch_size=16, show_progress_bar=False).astype("float32")


def embed_query(texte: str) -> np.ndarray:
    return get_embedder().encode([f"query: {texte}"], normalize_embeddings=True).astype("float32")


class VectorStore:
    def __init__(self, index: faiss.Index, chunks: list[dict]):
        self.index, self.chunks = index, chunks

    # ------------------------------------------------------------------ construction
    @classmethod
    def build(cls) -> "VectorStore":
        docs = charger_corpus()
        chunks = [c.to_dict() for c in construire_chunks(docs)]
        vecs = embed_passages([f"{c['titre']}. {c['texte']}" for c in chunks])
        index = faiss.IndexFlatIP(vecs.shape[1])
        index.add(vecs)
        store = cls(index, chunks)
        store.save()
        return store

    def save(self) -> None:
        CONFIG.index_dir.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(CONFIG.index_dir / "faiss.index"))
        (CONFIG.index_dir / "chunks.json").write_text(json.dumps(self.chunks, ensure_ascii=False, indent=1),
                                                      encoding="utf-8")

    @classmethod
    def load_or_build(cls) -> "VectorStore":
        f, c = CONFIG.index_dir / "faiss.index", CONFIG.index_dir / "chunks.json"
        if f.exists() and c.exists():
            return cls(faiss.read_index(str(f)), json.loads(c.read_text(encoding="utf-8")))
        return cls.build()

    # ------------------------------------------------------------------ recherche
    def search(self, requete: str, k: int = 4, categorie: str | None = None) -> list[dict]:
        q = embed_query(requete)
        scores, ids = self.index.search(q, min(len(self.chunks), k * 3 if categorie else k))
        out = []
        for s, i in zip(scores[0], ids[0]):
            if i < 0:
                continue
            ch = dict(self.chunks[i], score=round(float(s), 4))
            if categorie and ch["categorie"] != categorie:
                continue
            out.append(ch)
        return out[:k]


@lru_cache(maxsize=1)
def get_store() -> VectorStore:
    return VectorStore.load_or_build()
