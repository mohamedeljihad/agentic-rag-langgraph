"""Construction explicite du graphe LangGraph (StateGraph, nœuds, arêtes, arêtes conditionnelles, mémoire)."""
from __future__ import annotations

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from . import nodes as N
from .state import AgentState, etat_initial


def construire_graphe(checkpointer=None):
    g = StateGraph(AgentState)
    for nom, fn in [("contextualiser", N.contextualiser), ("analyser", N.analyser),
                    ("repondre_direct", N.repondre_direct), ("glossaire", N.glossaire),
                    ("planifier", N.planifier), ("rechercher", N.rechercher),
                    ("evaluer_documents", N.evaluer_documents), ("reecrire", N.reecrire),
                    ("calculer", N.calculer), ("generer", N.generer), ("verifier", N.verifier),
                    ("finaliser", N.finaliser)]:
        g.add_node(nom, fn)

    g.add_edge(START, "contextualiser")
    g.add_edge("contextualiser", "analyser")
    g.add_conditional_edges("analyser", N.route_apres_analyse,
                            {"direct": "repondre_direct", "glossaire": "glossaire", "recherche": "planifier"})
    g.add_conditional_edges("glossaire", N.route_apres_glossaire, {"trouve": "finaliser", "non_trouve": "planifier"})
    g.add_edge("planifier", "rechercher")
    g.add_edge("rechercher", "evaluer_documents")
    g.add_conditional_edges("evaluer_documents", N.route_apres_evaluation,
                            {"reecrire": "reecrire", "calculer": "calculer", "generer": "generer"})
    g.add_edge("reecrire", "rechercher")          # boucle de re-recherche
    g.add_edge("calculer", "generer")
    g.add_edge("generer", "verifier")
    g.add_edge("verifier", "finaliser")
    g.add_edge("repondre_direct", "finaliser")
    g.add_edge("finaliser", END)
    return g.compile(checkpointer=checkpointer if checkpointer is not None else MemorySaver())


class Agent:
    """Façade simple : un graphe compilé + une mémoire MemorySaver partagée entre les threads."""

    def __init__(self):
        self.graph = construire_graphe()

    def ask(self, question: str, thread_id: str = "defaut") -> dict:
        cfg = {"configurable": {"thread_id": thread_id}, "recursion_limit": 40}
        return self.graph.invoke(etat_initial(question), cfg)

    def historique(self, thread_id: str) -> list:
        return self.graph.get_state({"configurable": {"thread_id": thread_id}}).values.get("messages", [])
