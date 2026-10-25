"""État partagé du graphe LangGraph."""
from __future__ import annotations

from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage, HumanMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict, total=False):
    # Mémoire conversationnelle : persistée par le checkpointer, cumulée par le réducteur add_messages
    messages: Annotated[list[AnyMessage], add_messages]
    question: str                 # question brute du tour courant
    question_autonome: str        # question reformulée grâce à l'historique (mémoire)
    route: str                    # "recherche" | "glossaire" | "direct"
    complexe: bool                # nécessite une décomposition
    besoin_calcul: bool           # nécessite l'outil calculatrice
    sous_questions: list[str]
    requetes: list[str]           # requêtes à exécuter au prochain passage dans « rechercher »
    origines: dict                # requête reformulée -> sous-question qu'elle doit couvrir
    documents: list[dict]         # fragments récupérés + verdict de pertinence
    nouveaux: int                 # nombre de fragments nouveaux au dernier passage dans « rechercher »
    nb_reecritures: int
    calcul: dict | None           # {"expression", "resultat"}
    reponse: str
    sources: list[str]
    ancrage: float                # similarité réponse / contexte (indicateur d'ancrage)
    trace: list[dict]             # journal des nœuds visités (nom, durée, détail)


def etat_initial(question: str) -> dict:
    """Entrée d'un tour : on ajoute le message utilisateur et on réinitialise les champs de travail
    (les messages des tours précédents sont restaurés par le checkpointer)."""
    return {"messages": [HumanMessage(content=question)], "question": question, "question_autonome": question,
            "route": "", "complexe": False, "besoin_calcul": False, "sous_questions": [], "requetes": [], "origines": {},
            "documents": [], "nouveaux": 0, "nb_reecritures": 0, "calcul": None, "reponse": "", "sources": [],
            "ancrage": 0.0, "trace": []}
