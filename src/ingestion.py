"""Prétraitement du corpus : lecture, nettoyage, découpage en fragments (chunking)."""
from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from pathlib import Path

from .config import CONFIG


@dataclass
class Document:
    doc_id: str
    titre: str
    categorie: str
    texte: str
    fichier: str


@dataclass
class Chunk:
    chunk_id: str
    doc_id: str
    titre: str
    categorie: str
    texte: str

    def to_dict(self) -> dict:
        return asdict(self)


_FRONT = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.S)


def _parse_frontmatter(raw: str) -> tuple[dict, str]:
    """Sépare l'en-tête YAML simple (clé: valeur) du corps Markdown."""
    m = _FRONT.match(raw)
    if not m:
        return {}, raw
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    return meta, raw[m.end():]


def nettoyer(texte: str) -> str:
    """Retire la syntaxe Markdown et normalise les espaces, en conservant les paragraphes."""
    texte = re.sub(r"^#\s.*\n", "", texte, flags=re.M)               # titre principal (déjà en métadonnée)
    texte = re.sub(r"^\s*[-*]\s+", "", texte, flags=re.M)             # puces
    texte = re.sub(r"^#{2,}\s*(.+?)\s*\n", r"\1 : ", texte, flags=re.M)  # « ## Section » -> « Section : … »
    texte = re.sub(r"[*_`]{1,3}", "", texte)                 # emphase
    texte = re.sub(r"[ \t]+", " ", texte)
    texte = re.sub(r"\n{3,}", "\n\n", texte)
    return texte.strip()


def charger_corpus(corpus_dir: Path | None = None) -> list[Document]:
    corpus_dir = corpus_dir or CONFIG.corpus_dir
    docs = []
    for f in sorted(corpus_dir.glob("*.md")):
        meta, corps = _parse_frontmatter(f.read_text(encoding="utf-8"))
        docs.append(Document(doc_id=meta.get("id", f.stem), titre=meta.get("titre", f.stem),
                             categorie=meta.get("categorie", "divers"), texte=nettoyer(corps), fichier=f.name))
    return docs


def _phrases(paragraphe: str) -> list[str]:
    return [p for p in re.split(r"(?<=[.!?;:])\s+", paragraphe) if p]


def decouper(doc: Document, taille: int | None = None, recouvrement: int | None = None) -> list[Chunk]:
    """Découpage par paragraphes puis par phrases, avec recouvrement de fin de fragment.

    Chaque fragment reste cohérent (on ne coupe jamais au milieu d'une phrase) et reçoit le titre
    du document dans ses métadonnées, utilisé ensuite pour la vectorisation.
    """
    taille = taille or CONFIG.chunk_size
    recouvrement = recouvrement if recouvrement is not None else CONFIG.chunk_overlap
    unites: list[str] = []
    for para in doc.texte.split("\n\n"):
        para = para.replace("\n", " ").strip()
        if not para or para == doc.titre:
            continue
        unites.extend([para] if len(para) <= taille else _phrases(para))

    chunks, courant = [], ""
    for u in unites:
        if courant and len(courant) + len(u) + 1 > taille:
            chunks.append(courant.strip())
            queue = courant[-recouvrement:]
            courant = (queue[queue.find(" ") + 1:] if " " in queue else "") + " " + u
        else:
            courant = f"{courant} {u}" if courant else u
    if courant.strip():
        chunks.append(courant.strip())
    return [Chunk(f"{doc.doc_id}-c{i}", doc.doc_id, doc.titre, doc.categorie, t) for i, t in enumerate(chunks)]


def construire_chunks(docs: list[Document]) -> list[Chunk]:
    return [c for d in docs for c in decouper(d)]
