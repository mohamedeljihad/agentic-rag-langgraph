"""Configuration centralisée (surchargeable par variables d'environnement)."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _env(name: str, default: str) -> str:
    return os.environ.get(name, default)


@dataclass
class Config:
    # --- Données ---
    corpus_dir: Path = ROOT / "data" / "corpus"
    glossary_path: Path = ROOT / "data" / "glossaire.json"
    index_dir: Path = ROOT / "data" / "index"
    results_dir: Path = ROOT / "results"

    # --- Prétraitement / vectorisation ---
    chunk_size: int = 650          # taille cible d'un fragment (caractères)
    chunk_overlap: int = 120       # recouvrement (caractères) entre fragments consécutifs
    embedding_model: str = _env("EMBEDDING_MODEL", "intfloat/multilingual-e5-small")

    # --- Recherche ---
    top_k: int = 4                 # fragments récupérés par sous-question
    max_context_chunks: int = 5    # fragments transmis au générateur
    seuil_haut: float = 0.88       # score cosinus au-dessus duquel un fragment est gardé d'office
    seuil_bas: float = 0.82        # score minimal pour qu'un « oui » du LLM soit accepté
    max_reecritures: int = 2       # nombre maximal de boucles de reformulation

    # --- LLM ---
    llm_provider: str = _env("LLM_PROVIDER", "local")   # "local" (transformers) ou "openai" (API compatible)
    local_model: str = _env("LOCAL_MODEL", "Qwen/Qwen2.5-1.5B-Instruct")
    local_quant: str = _env("LOCAL_QUANT", "int8-mlp")    # "int8-mlp" ou "none" (float32)
    api_base_url: str = _env("LLM_BASE_URL", "https://api.openai.com/v1")
    api_model: str = _env("LLM_MODEL", "gpt-4o-mini")
    api_key: str = field(default_factory=lambda: os.environ.get("LLM_API_KEY")
                         or os.environ.get("OPENAI_API_KEY") or os.environ.get("GROQ_API_KEY") or "")
    max_new_tokens: int = 220
    num_threads: int = int(_env("NUM_THREADS", "2"))


CONFIG = Config()
