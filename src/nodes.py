"""Nœuds du graphe agentique et fonctions de routage (arêtes conditionnelles).

Chaque nœud reçoit l'état, renvoie une mise à jour partielle et ajoute une entrée à ``trace``.
Les décisions du petit LLM sont toujours analysées de façon déterministe, avec des règles de repli.
"""
from __future__ import annotations

import re
import time
from functools import wraps

import numpy as np
from langchain_core.messages import AIMessage, HumanMessage

from . import prompts as P
from .config import CONFIG
from .llm import get_llm
from .tools import (calculatrice, consulter_glossaire, normaliser_nombres, rechercher_documents, sans_accents,
                    termes_glossaire)
from .vectorstore import embed_passages


# ============================================================================ utilitaires
def noeud(nom: str):
    """Décorateur : chronomètre le nœud et journalise son passage dans ``trace``."""
    def deco(fn):
        @wraps(fn)
        def wrapper(state):
            t0 = time.time()
            maj = fn(state) or {}
            info = maj.pop("_info", "")
            maj["trace"] = list(state.get("trace", [])) + [
                {"noeud": nom, "duree_s": round(time.time() - t0, 2), "info": info}]
            return maj
        return wrapper
    return deco


def _llm(system: str, user: str, max_tokens: int, exemples: list[tuple[str, str]] | None = None) -> str:
    msgs = [{"role": "system", "content": system}]
    for q, r in exemples or []:
        msgs += [{"role": "user", "content": q}, {"role": "assistant", "content": r}]
    msgs.append({"role": "user", "content": user})
    return get_llm().chat(msgs, max_new_tokens=max_tokens)


def _q(state) -> str:
    return state.get("question_autonome") or state["question"]


_SALUTATION = re.compile(r"^\s*(bonjour|bonsoir|salut|coucou|hello|merci|au revoir)\b", re.I)
_GLOSSAIRE = re.compile(r"(que (signifie|veut dire)|signification|d[ée]finition|acronyme|abr[ée]viation)", re.I)
_CALCUL = re.compile(r"(calcul|combien|montant|plafond|amende|pourcentage|%|total)", re.I)
# quantité = nombre suivi d'une unité (exclut les identifiants comme « ISO 27001 » ou « version 2022 »)
_QUANTITE = re.compile(r"\d+(?:[.,]\d+)?\s*(%|euros?|€|dirhams?|dh|millions?|milliards?|heures?|h\b|jours?|semaines?|"
                       r"mois|ans?|minutes?|go|to|postes?|utilisateurs?|serveurs?)", re.I)
_COMPLEXE = re.compile(r"(compar|diff[ée]ren|compl[eè]tent|combiner|puis|ainsi que|à la fois|et quelles?|"
                       r"et quels?|et comment|apr[eè]s|si une|si un|calcul)", re.I)
_SUITE = re.compile(r"^\s*(et|mais|alors|donc)\b|\b(il|elle|ils|elles|cela|ça|celle|celui|ce dernier|cette|ces)\b",
                    re.I)


# ============================================================================ nœuds
@noeud("contextualiser")
def contextualiser(state):
    """Mémoire : si la question fait suite à un échange précédent (même thread), la rendre autonome."""
    msgs = state.get("messages", [])
    q = state["question"]
    precedents = [m for m in msgs[:-1] if isinstance(m, (HumanMessage, AIMessage))]
    if len(precedents) < 2 or not (_SUITE.search(q) or len(q.split()) < 6):
        return {"question_autonome": q, "_info": "aucun historique pertinent" if len(precedents) < 2 else "question autonome"}
    q_prec = next(m.content for m in reversed(precedents) if isinstance(m, HumanMessage))
    r_prec = next(m.content for m in reversed(precedents) if isinstance(m, AIMessage))[:300]
    sortie = _llm(P.CONTEXTUALISATION_SYSTEME,
                  f"Question précédente : {q_prec}\nRéponse précédente : {r_prec}\nDernière question : {q}\n"
                  "Question réécrite :", 60)
    ligne = sortie.strip().splitlines()[0].strip(' "«»') if sortie.strip() else ""
    if 10 <= len(ligne) <= 300 and ligne.lower() != q.lower():
        autonome, mode = ligne, "LLM"
    else:
        autonome, mode = f"{q} (contexte : {q_prec})", "repli"
    return {"question_autonome": autonome, "_info": f"{mode} -> {autonome}"}


@noeud("analyser")
def analyser(state):
    """Routeur : règles explicites (salutation, glossaire, calcul, complexité) + classification LLM."""
    q = _q(state)
    besoin_calcul = bool(_CALCUL.search(q) and (_QUANTITE.search(q) or re.search(r"calcul", q, re.I)))
    complexe = besoin_calcul or bool(_COMPLEXE.search(q)) or q.count("?") > 1 or len(q.split()) > 22
    if _SALUTATION.search(q) and len(q.split()) <= 8:
        return {"route": "direct", "besoin_calcul": False, "complexe": False, "_info": "règle salutation -> direct"}
    if _GLOSSAIRE.search(q) and termes_glossaire(q):
        return {"route": "glossaire", "besoin_calcul": False, "complexe": False,
                "_info": f"règle glossaire ({', '.join(termes_glossaire(q))})"}
    sortie = _llm(P.ROUTEUR_SYSTEME, q, 4, P.ROUTEUR_EXEMPLES).upper()
    route = "direct" if "DIRECT" in sortie else "recherche"
    garde = ""
    if route == "direct":
        # garde-fou : si la base contient des passages proches, on préfère chercher
        meilleur = rechercher_documents.invoke({"requete": q, "k": 1})
        if meilleur and meilleur[0]["score"] >= CONFIG.seuil_bas:
            route, garde = "recherche", f" (garde-fou : score {meilleur[0]['score']:.3f})"
    return {"route": route, "besoin_calcul": besoin_calcul, "complexe": complexe,
            "_info": f"LLM='{sortie.strip()[:12]}' -> {route}{garde}; complexe={complexe}; calcul={besoin_calcul}"}


@noeud("repondre_direct")
def repondre_direct(state):
    rep = _llm(P.DIRECT_SYSTEME, state["question"], 60)
    return {"reponse": rep or "Bonjour ! Je réponds aux questions de cybersécurité et de réglementation numérique.",
            "sources": [], "_info": "réponse sans recherche"}


@noeud("glossaire")
def glossaire(state):
    """Outil glossaire : réponse immédiate si l'acronyme est connu."""
    termes = termes_glossaire(_q(state))
    defs = [d for d in (consulter_glossaire.invoke({"terme": t}) for t in termes) if d != "INCONNU"]
    if not defs:
        return {"route": "recherche", "_info": "terme inconnu -> recherche"}
    rep = "D'après le glossaire de la base : " + " ; ".join(defs) + " [GLOSSAIRE]"
    return {"reponse": rep, "sources": ["GLOSSAIRE"], "_info": f"{len(defs)} définition(s)"}


@noeud("planifier")
def planifier(state):
    """Décomposition des questions complexes en sous-questions (LLM + analyse déterministe + repli)."""
    q = _q(state)
    if not state.get("complexe"):
        return {"sous_questions": [q], "requetes": [q], "_info": "question simple : pas de décomposition"}
    sortie = _llm(P.PLANIFICATEUR_SYSTEME, q, 90, [PLANIF_EX])
    lignes = [re.sub(r"^\s*(\d+[.)]|[-*•])\s*", "", l).strip() for l in sortie.splitlines()]
    sous = [l for l in lignes if len(l) > 12 and l.endswith("?") and l.lower() != q.lower()][:3]
    mode = "LLM"
    if len(sous) < 2:
        morceaux = [m.strip(" ,;?") for m in re.split(r"\?|;| et (?=quel|quelle|comment|combien|pourquoi)", q)]
        sous = [m + " ?" for m in morceaux if len(m.split()) >= 4][:3]
        mode = "repli"
    sous = sous or [q]
    # la question complète est toujours ajoutée aux requêtes pour préserver le rappel
    return {"sous_questions": sous, "requetes": sous + [q], "_info": f"{mode} : {sous}"}


PLANIF_EX = P.PLANIFICATEUR_EXEMPLE


@noeud("rechercher")
def rechercher(state):
    """Outil de recherche : exécute chaque requête en attente et fusionne les fragments (dédoublonnage)."""
    docs = {d["chunk_id"]: dict(d) for d in state.get("documents", [])}
    origines = state.get("origines", {})          # requête reformulée -> sous-question d'origine
    nouveaux = 0
    for req in state.get("requetes", []):
        origine = origines.get(req, req)
        for ch in rechercher_documents.invoke({"requete": req, "k": CONFIG.top_k}):
            if ch["chunk_id"] in docs:
                d = docs[ch["chunk_id"]]
                d["score"] = max(d["score"], ch["score"])
                d["origines"] = list(dict.fromkeys(d.get("origines", []) + [origine]))
                continue
            docs[ch["chunk_id"]] = dict(ch, requete=origine, origines=[origine], pertinent=None)
            nouveaux += 1
    return {"documents": sorted(docs.values(), key=lambda d: -d["score"]), "requetes": [], "nouveaux": nouveaux,
            "_info": f"{len(state.get('requetes', []))} requête(s), {nouveaux} nouveau(x) fragment(s)"}


@noeud("evaluer_documents")
def evaluer_documents(state):
    """Évaluation de la pertinence : règles sur le score + jugement OUI/NON du LLM pour la zone grise."""
    q = _q(state)
    meilleurs = {}
    for d in state["documents"]:  # meilleur fragment de chaque requête
        if d.get("requete") not in meilleurs or d["score"] > meilleurs[d["requete"]]["score"]:
            meilleurs[d.get("requete")] = d
    ids_meilleurs = {d["chunk_id"] for d in meilleurs.values()}
    docs, n_llm = [], 0
    for d in state["documents"]:
        d = dict(d)
        if d.get("pertinent") is None:
            if d["score"] >= CONFIG.seuil_haut or (d["chunk_id"] in ids_meilleurs and d["score"] >= CONFIG.seuil_bas):
                d["pertinent"], d["juge"] = True, "score"
            elif d["score"] < CONFIG.seuil_bas:
                d["pertinent"], d["juge"] = False, "score"
            else:
                sortie = _llm(P.EVALUATEUR_SYSTEME, f"Question : {d.get('requete', q)}\nExtrait : {d['texte'][:500]}\n"
                              "Cet extrait est-il utile ? (OUI/NON)", 3).upper()
                d["pertinent"], d["juge"] = sans_accents(sortie).startswith("OUI"), "llm"
                n_llm += 1
        docs.append(d)
    n_ok = sum(d["pertinent"] for d in docs)
    return {"documents": docs, "_info": f"{n_ok}/{len(docs)} pertinents ({n_llm} jugement(s) LLM)"}


def _requetes_non_couvertes(state) -> list[str]:
    reqs = state.get("sous_questions") or [_q(state)]
    couvertes = {o for d in state["documents"] if d["pertinent"] for o in d.get("origines", [d.get("requete")])}
    if not any(d["pertinent"] for d in state["documents"]):
        return reqs
    return [r for r in reqs if r not in couvertes and len(reqs) > 1]


@noeud("reecrire")
def reecrire(state):
    """Reformulation des requêtes sans document pertinent (LLM + expansion des acronymes en repli)."""
    nouvelles, origines = [], dict(state.get("origines", {}))
    for r in _requetes_non_couvertes(state):
        sortie = _llm(P.REECRITURE_SYSTEME, f"Requête : {r}\nRequête reformulée :", 40)
        ligne = sortie.strip().splitlines()[0].strip(' "«»') if sortie.strip() else ""
        expansion = " ".join(consulter_glossaire.invoke({"terme": t}).split(":", 1)[1] for t in termes_glossaire(r))
        if len(ligne) < 8 or ligne.lower() == r.lower():
            ligne = f"{r} {expansion}".strip()
        nouvelles.append(ligne)
        origines[ligne] = r
    return {"requetes": nouvelles, "origines": origines, "nb_reecritures": state.get("nb_reecritures", 0) + 1,
            "_info": f"tentative {state.get('nb_reecritures', 0) + 1} : {nouvelles}"}


@noeud("calculer")
def calculer(state):
    """Outil calculatrice : le LLM traduit le problème en expression (few-shot), l'expression est validée
    (elle doit utiliser un nombre de la question), évaluée de façon sûre, avec une seconde tentative guidée."""
    q = normaliser_nombres(_q(state))
    nombres_q = set(re.findall(r"\d+(?:\.\d+)?", q))
    chiffres = [d for d in _contexte(state) if re.search(r"\d", d["texte"])] or _contexte(state)
    contexte = "\n".join(normaliser_nombres(d["texte"][-500:] if "%" in d["texte"][-500:] else d["texte"][:500])
                         for d in chiffres[:2])
    user = f"Informations :\n{contexte}\n\nProblème : {q}\nExpression :"
    essais = []
    for tentative in (1, 2):
        if tentative == 2:
            user += (f"\n(Rappel : l'expression doit utiliser le ou les nombres de la question : "
                     f"{', '.join(sorted(nombres_q))}.)")
        sortie = _llm(P.CALCUL_SYSTEME, user, 40, P.CALCUL_EXEMPLES)
        for c in [l.strip().strip("`").strip() for l in sortie.splitlines()] + [sortie.replace("\n", " ")]:
            c = c.split("=")[-1].strip() if "=" in c else c
            c = re.sub(r"[^0-9+\-*/().,maxin ]", "", c).replace(",", ", ").strip()
            if not re.search(r"\d", c):
                continue
            if not re.search(r"[+\-*/]|max|min", c):
                essais.append(f"{c} (rejetée : aucune opération)")
                break
            if nombres_q and not set(re.findall(r"\d+(?:\.\d+)?", c)) & nombres_q:
                essais.append(f"{c} (rejetée : n'utilise pas les données de la question)")
                break
            res = calculatrice.invoke({"expression": c})
            if not res.startswith("ERREUR"):
                return {"calcul": {"expression": c, "resultat": res},
                        "_info": f"tentative {tentative} : {c} = {res}" + (f" ; échecs : {essais}" if essais else "")}
            essais.append(f"{c} ({res})")
            break
    return {"calcul": None, "_info": f"calcul abandonné après 2 tentatives : {essais}"}


def _contexte(state) -> list[dict]:
    """Sélection du contexte transmis au générateur :
    1) diversité : le meilleur fragment pertinent de chaque (sous-)requête passe en premier ;
    2) fenêtre de contexte : on ajoute les fragments voisins (même document, index ±1) déjà récupérés,
       pour ne pas couper une liste ou une règle répartie sur deux fragments ;
    3) ordre de lecture : fragments regroupés par document et dans l'ordre du texte."""
    docs = state["documents"]
    pert = [d for d in docs if d["pertinent"]] or docs[:2]
    choisis = []
    for req in dict.fromkeys(d.get("requete") for d in pert):
        choisis.append(next(d for d in pert if d.get("requete") == req))
    choisis += [d for d in pert if d not in choisis]
    choisis = choisis[:CONFIG.max_context_chunks]
    par_id = {d["chunk_id"]: d for d in docs}
    for d in list(choisis):
        doc, idx = d["chunk_id"].rsplit("-c", 1)
        for voisin in (f"{doc}-c{int(idx) + 1}", f"{doc}-c{int(idx) - 1}"):
            v = par_id.get(voisin)
            if v and v not in choisis and v["score"] >= CONFIG.seuil_bas and len(choisis) < CONFIG.max_context_chunks:
                choisis.append(v)
    ordre_doc = list(dict.fromkeys(d["doc_id"] for d in choisis))
    return sorted(choisis, key=lambda d: (ordre_doc.index(d["doc_id"]), int(d["chunk_id"].rsplit("-c", 1)[1])))


@noeud("generer")
def generer(state):
    """Génération de la réponse avec citations [Dxx] à partir des fragments pertinents."""
    ctx = _contexte(state)
    bloc = "\n\n".join(f"[{d['doc_id']}] {d['titre']} : {d['texte']}" for d in ctx)
    calc = state.get("calcul")
    extra = (f"\n\nRésultat exact fourni par l'outil calculatrice : {calc['expression']} = {calc['resultat']}. "
             "Reprends ce résultat tel quel dans la réponse.") if calc else ""
    sous = state.get("sous_questions") or []
    if len(sous) > 1:
        extra += "\n\nPoints à traiter, dans l'ordre :\n" + "\n".join(f"- {s}" for s in sous)
    rep = _llm(P.GENERATEUR_SYSTEME, f"Extraits :\n{bloc}{extra}\n\nQuestion : {_q(state)}\nRéponse :",
               CONFIG.max_new_tokens, [P.GENERATEUR_EXEMPLE])
    return {"reponse": rep, "_info": f"{len(ctx)} fragment(s) en contexte, {len(rep)} caractères"}


@noeud("verifier")
def verifier(state):
    """Contrôle déterministe : citations valides, phrases répétées, réponse vide, indicateur d'ancrage."""
    ctx = _contexte(state)
    ids_ctx = list(dict.fromkeys(d["doc_id"] for d in ctx))
    rep = state.get("reponse", "").strip()
    # dédoublonnage des phrases (les petits modèles bouclent parfois)
    phrases, vues = [], set()
    for p in re.split(r"(?<=[.!?])\s+", rep):
        cle = p.strip().lower()
        if cle and cle not in vues:
            vues.add(cle)
            phrases.append(p.strip())
    rep = " ".join(phrases)
    if len(rep) < 20:  # repli extractif
        rep = " ".join(re.split(r"(?<=[.!?])\s+", ctx[0]["texte"])[:2]) if ctx else "Information non disponible."
        notes = "réponse vide -> repli extractif"
    else:
        notes = "ok"
    calc = state.get("calcul")
    if calc and calc["resultat"].replace(" ", "") not in rep.replace(" ", "").replace("\u202f", ""):
        rep += f"\n\nRésultat de l'outil calculatrice : {calc['expression']} = {calc['resultat']}."
        notes += "; résultat du calcul ajouté"
    citees = re.findall(r"\[(D\d{2})\]", rep)
    invalides = [c for c in citees if c not in ids_ctx]
    for c in invalides:
        rep = rep.replace(f"[{c}]", "")
    valides = list(dict.fromkeys(c for c in citees if c in ids_ctx))
    if not valides:
        valides = ids_ctx[:3]
        rep += "\n\nSources : " + ", ".join(f"[{c}]" for c in valides)
        notes += "; sources ajoutées automatiquement"
    v = embed_passages([rep, " ".join(d["texte"] for d in ctx) or rep])
    ancrage = float(np.dot(v[0], v[1]))
    return {"reponse": rep, "sources": valides, "ancrage": round(ancrage, 3),
            "_info": f"{notes}; citations invalides retirées={invalides}; ancrage={ancrage:.3f}"}


@noeud("finaliser")
def finaliser(state):
    """Écrit la réponse dans la mémoire conversationnelle (messages persistés par le checkpointer)."""
    return {"messages": [AIMessage(content=state["reponse"])], "_info": f"sources={state.get('sources', [])}"}


# ============================================================================ routage conditionnel
def route_apres_analyse(state) -> str:
    return state["route"]


def route_apres_glossaire(state) -> str:
    return "trouve" if state.get("reponse") else "non_trouve"


def route_apres_evaluation(state) -> str:
    # on reboucle seulement s'il reste une sous-question non couverte, si le budget n'est pas épuisé
    # et si la reformulation précédente a encore apporté de nouveaux fragments
    stagnation = state.get("nb_reecritures", 0) > 0 and state.get("nouveaux", 1) == 0
    if _requetes_non_couvertes(state) and state.get("nb_reecritures", 0) < CONFIG.max_reecritures and not stagnation:
        return "reecrire"
    return "calculer" if state.get("besoin_calcul") else "generer"
