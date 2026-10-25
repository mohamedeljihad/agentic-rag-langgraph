"""Interface en ligne de commande : python -m src.main [--question "..."] [--thread ID] [--trace]."""
from __future__ import annotations

import argparse
import time

from .graph import Agent


def afficher(res: dict, trace: bool, duree: float) -> None:
    if trace:
        print("\n— Parcours du graphe —")
        for t in res["trace"]:
            print(f"  • {t['noeud']:<18} {t['duree_s']:>6.2f} s  {t['info']}")
    print(f"\nRéponse ({duree:.1f} s) :\n{res['reponse']}\n")


def main() -> None:
    ap = argparse.ArgumentParser(description="Agent RAG agentique (LangGraph) — cybersécurité & réglementation")
    ap.add_argument("--question", "-q", help="question unique (sinon mode conversation)")
    ap.add_argument("--thread", default="cli", help="identifiant de conversation (mémoire)")
    ap.add_argument("--trace", action="store_true", help="afficher le parcours des nœuds")
    a = ap.parse_args()
    print("Chargement des modèles…")
    agent = Agent()
    if a.question:
        t0 = time.time(); r = agent.ask(a.question, a.thread); afficher(r, a.trace, time.time() - t0)
        return
    print("Posez vos questions (« quitter » pour sortir). La conversation est mémorisée dans le thread", a.thread)
    while True:
        try:
            q = input("Vous > ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if q.lower() in {"quitter", "exit", "q"}:
            break
        if q:
            t0 = time.time(); r = agent.ask(q, a.thread); afficher(r, a.trace, time.time() - t0)


if __name__ == "__main__":
    main()
