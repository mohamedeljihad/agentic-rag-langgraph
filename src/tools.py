"""Outils de l'agent, déclarés comme outils LangChain (``@tool``) et appelés par les nœuds du graphe.

- rechercher_documents : recherche sémantique dans l'index FAISS (avec filtre de catégorie optionnel)
- calculatrice         : évaluation sûre d'expressions arithmétiques (AST, sans ``eval``)
- consulter_glossaire  : définition d'un acronyme du domaine
- lister_documents     : métadonnées de la base (identifiant, titre, catégorie)
"""
from __future__ import annotations

import ast
import json
import operator
import re
import unicodedata
from functools import lru_cache

from langchain_core.tools import tool

from .config import CONFIG
from .vectorstore import get_store


# ---------------------------------------------------------------------------- recherche
@tool
def rechercher_documents(requete: str, k: int = 4, categorie: str = "") -> list[dict]:
    """Recherche sémantique des fragments les plus proches de la requête dans la base documentaire.
    Retourne une liste de fragments {chunk_id, doc_id, titre, categorie, texte, score}."""
    return get_store().search(requete, k=k, categorie=categorie or None)


@tool
def lister_documents(categorie: str = "") -> str:
    """Liste les documents de la base (identifiant, titre, catégorie), éventuellement filtrés par catégorie."""
    vus = {}
    for c in get_store().chunks:
        if not categorie or c["categorie"] == categorie:
            vus[c["doc_id"]] = (c["titre"], c["categorie"])
    return "\n".join(f"[{d}] {t} ({cat})" for d, (t, cat) in sorted(vus.items()))


# ---------------------------------------------------------------------------- calculatrice
_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv,
        ast.Pow: operator.pow, ast.Mod: operator.mod, ast.USub: operator.neg, ast.UAdd: operator.pos}
_FUNCS = {"max": max, "min": min, "round": round, "abs": abs}


def _eval(node):
    if isinstance(node, ast.Expression):
        return _eval(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        if isinstance(node.op, ast.Pow) and abs(_eval(node.right)) > 12:
            raise ValueError("exposant trop grand")
        return _OPS[type(node.op)](_eval(node.left), _eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval(node.operand))
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in _FUNCS:
        return _FUNCS[node.func.id](*[_eval(a) for a in node.args])
    raise ValueError(f"élément non autorisé : {ast.dump(node)[:40]}")


def format_nombre(x: float) -> str:
    """Format français : espaces pour les milliers, virgule décimale."""
    if abs(x - round(x)) < 1e-9:
        return f"{int(round(x)):,}".replace(",", " ")
    return f"{x:,.2f}".replace(",", " ").replace(".", ",")


@tool
def calculatrice(expression: str) -> str:
    """Évalue une expression arithmétique (+, -, *, /, **, %, parenthèses, max, min, round).
    Exemple : max(20000000, 0.04*1000000000). Retourne le résultat formaté ou un message d'erreur."""
    expr = expression.replace("×", "*").replace("÷", "/").replace("^", "**").strip()
    try:
        val = _eval(ast.parse(expr, mode="eval"))
        return format_nombre(float(val))
    except Exception as e:  # noqa: BLE001 - l'erreur est renvoyée à l'agent
        return f"ERREUR: {e}"


# ---------------------------------------------------------------------------- glossaire
@lru_cache(maxsize=1)
def _glossaire() -> dict:
    return json.loads(CONFIG.glossary_path.read_text(encoding="utf-8"))


def termes_glossaire(texte: str) -> list[str]:
    """Acronymes du glossaire présents dans un texte (insensible à la casse, mots entiers)."""
    t = texte.upper()
    return [k for k in _glossaire() if re.search(rf"(?<![A-Z0-9]){re.escape(k)}(?![A-Z0-9])", t)]


@tool
def consulter_glossaire(terme: str) -> str:
    """Retourne la définition d'un acronyme ou terme du domaine (ex. MFA, CNDP, NIS2), ou 'INCONNU'."""
    g = _glossaire()
    cle = terme.strip().upper().replace("-", "").replace(" ", "")
    for k, v in g.items():
        if k.replace("-", "") == cle:
            return f"{k} : {v}"
    return "INCONNU"


TOOLS = [rechercher_documents, calculatrice, consulter_glossaire, lister_documents]


# ---------------------------------------------------------------------------- utilitaires texte
def sans_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


_MULT = {"milliard": 1_000_000_000, "milliards": 1_000_000_000, "million": 1_000_000, "millions": 1_000_000}


def normaliser_nombres(texte: str) -> str:
    """« 1 milliard » -> 1000000000, « 1,4 % » -> 1.4 %, « 7,5 » -> 7.5 (aide le petit LLM à calculer)."""
    def rep(m):
        n = float(m.group(1).replace(",", ".")) * _MULT[m.group(2).lower()]
        return str(int(n)) if n == int(n) else str(n)
    texte = re.sub(r"(\d+(?:[.,]\d+)?)\s*(milliards?|millions?)", rep, texte, flags=re.I)
    return re.sub(r"(\d),(\d)", r"\1.\2", texte)
