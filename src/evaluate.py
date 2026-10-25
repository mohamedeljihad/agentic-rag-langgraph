"""Évaluation réelle sur 10 questions simples + 10 complexes (+ démonstration de la mémoire).

Mesures enregistrées pour chaque question (aucune valeur n'est saisie à la main) :
- latence_s            : temps de bout en bout de l'appel au graphe (hors chargement des modèles)
- docs_recuperes       : documents (doc_id) récupérés par l'outil de recherche, par score décroissant
- hit@k / rappel@k     : présence / proportion des sources attendues parmi les documents récupérés
- mrr                  : 1 / rang du premier document attendu dans la liste récupérée
- precision_pertinents : part des documents jugés pertinents par le nœud d'évaluation qui sont attendus
- couverture_faits     : part des faits clés attendus présents dans la réponse (comparaison normalisée)
- citation_correcte    : 1 si au moins une source citée fait partie des sources attendues
- score_qualite        : 0,7 × couverture_faits + 0,3 × citation_correcte (score défini de façon transparente)

Usage : python -m src.evaluate [--ids S01,C02] [--reprendre]
"""
from __future__ import annotations

import argparse
import json
import re
import time
import traceback

from .config import CONFIG, ROOT
from .graph import Agent
from .llm import get_llm
from .tools import sans_accents

QUESTIONS = ROOT / "eval" / "questions.json"
SORTIE = CONFIG.results_dir / "eval_results.json"


def normaliser(t: str) -> str:
    t = sans_accents(t.lower()).replace(" ", " ").replace(" ", " ").replace("’", "'")
    t = re.sub(r"(?<=\d) (?=\d{3}\b)", "", t)   # 40 000 000 -> 40000000
    return re.sub(r"\s+", " ", t)


def fait_present(reponse: str, variantes: list[str]) -> bool:
    r = normaliser(reponse)
    for v in variantes:
        v = normaliser(v)
        if re.fullmatch(r"\d+", v.strip()):
            if re.search(rf"(?<![\d,.]){v.strip()}(?![\d]|[,.]\d)", r):
                return True
        elif v in r:
            return True
    return False


def evaluer_question(agent: Agent, q: dict) -> dict:
    llm = get_llm()
    avant = llm.stats()
    t0 = time.time()
    try:
        res = agent.ask(q["question"], thread_id=f"eval-{q['id']}")
        erreur = ""
    except Exception as e:  # noqa: BLE001 - on enregistre l'échec tel quel
        res, erreur = {"reponse": "", "documents": [], "sources": [], "trace": []}, f"{e}\n{traceback.format_exc()}"
    latence = time.time() - t0
    apres = llm.stats()

    docs = res.get("documents", [])
    recuperes = list(dict.fromkeys(d["doc_id"] for d in docs))
    if "GLOSSAIRE" in res.get("sources", []):
        recuperes = ["GLOSSAIRE"] + recuperes
    pertinents = list(dict.fromkeys(d["doc_id"] for d in docs if d.get("pertinent")))
    attendus = q["sources"]
    trouves = [s for s in attendus if s in recuperes]
    rang = next((i + 1 for i, d in enumerate(recuperes) if d in attendus), None)
    faits = [fait_present(res.get("reponse", ""), f) for f in q["faits"]]
    couverture = sum(faits) / len(faits)
    citation = int(any(s in attendus for s in res.get("sources", [])))
    return {
        "id": q["id"], "type": q["type"], "question": q["question"], "reponse": res.get("reponse", ""),
        "erreur": erreur, "latence_s": round(latence, 2), "route": res.get("route", ""),
        "question_autonome": res.get("question_autonome", ""), "sous_questions": res.get("sous_questions", []),
        "nb_reecritures": res.get("nb_reecritures", 0), "calcul": res.get("calcul"),
        "sources_attendues": attendus, "docs_recuperes": recuperes, "docs_pertinents": pertinents,
        "sources_citees": res.get("sources", []),
        "hit_at_k": int(bool(trouves)), "rappel_at_k": round(len(trouves) / len(attendus), 3),
        "mrr": round(1 / rang, 3) if rang else 0.0,
        "precision_pertinents": round(sum(d in attendus for d in pertinents) / len(pertinents), 3) if pertinents else None,
        "faits_trouves": faits, "couverture_faits": round(couverture, 3), "citation_correcte": citation,
        "score_qualite": round(0.7 * couverture + 0.3 * citation, 3), "ancrage": res.get("ancrage"),
        "appels_llm": apres["appels"] - avant["appels"], "tokens_generes": apres["tokens"] - avant["tokens"],
        "temps_llm_s": round(apres["temps_llm_s"] - avant["temps_llm_s"], 2),
        "trace": res.get("trace", []),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ids", default="")
    ap.add_argument("--reprendre", action="store_true", help="ne pas recalculer les questions déjà évaluées")
    a = ap.parse_args()
    questions = json.loads(QUESTIONS.read_text(encoding="utf-8"))
    if a.ids:
        questions = [q for q in questions if q["id"] in a.ids.split(",")]
    CONFIG.results_dir.mkdir(exist_ok=True)
    data = json.loads(SORTIE.read_text(encoding="utf-8")) if a.reprendre and SORTIE.exists() else {}
    resultats = {r["id"]: r for r in data.get("resultats", [])}

    t0 = time.time()
    agent = Agent()
    llm = get_llm()
    llm.chat([{"role": "user", "content": "Bonjour"}], max_new_tokens=5)  # préchauffage (exclu des mesures)
    chargement = round(time.time() - t0, 1)
    print(f"Modèles chargés en {chargement} s — LLM : {llm.name}", flush=True)

    meta = {"llm": llm.name, "embeddings": CONFIG.embedding_model, "top_k": CONFIG.top_k,
            "seuils": [CONFIG.seuil_bas, CONFIG.seuil_haut], "max_reecritures": CONFIG.max_reecritures,
            "chargement_et_prechauffage_s": chargement, "threads": CONFIG.num_threads,
            "date": time.strftime("%Y-%m-%d %H:%M")}
    for q in questions:
        if q["id"] in resultats and a.reprendre:
            continue
        r = evaluer_question(agent, q)
        resultats[q["id"]] = r
        print(f"[{r['id']}] {r['latence_s']:6.1f} s | hit={r['hit_at_k']} rappel={r['rappel_at_k']} "
              f"faits={r['couverture_faits']} cit={r['citation_correcte']} | {r['reponse'][:90]!r}", flush=True)
        SORTIE.write_text(json.dumps({"meta": meta, "resultats": sorted(resultats.values(), key=lambda x: x["id"][0] == "C")},
                                     ensure_ascii=False, indent=1), encoding="utf-8")

    # Démonstration de la mémoire conversationnelle (même thread_id, deux tours)
    if not a.ids:
        demo = []
        for question in ["Quel est le délai de notification d'une violation de données selon le RGPD ?",
                         "Et quelle amende maximale risque-t-on pour un manquement grave ?"]:
            t1 = time.time()
            res = agent.ask(question, thread_id="demo-memoire")
            demo.append({"question": question, "question_autonome": res["question_autonome"],
                         "reponse": res["reponse"], "sources": res["sources"], "latence_s": round(time.time() - t1, 2),
                         "trace": res["trace"]})
            print(f"[mémoire] {question} -> {res['question_autonome']}", flush=True)
        demo_hist = [{"role": m.type, "contenu": m.content[:200]} for m in agent.historique("demo-memoire")]
        (CONFIG.results_dir / "memoire_demo.json").write_text(
            json.dumps({"tours": demo, "historique_thread": demo_hist}, ensure_ascii=False, indent=1), encoding="utf-8")
    meta["duree_totale_s"] = round(time.time() - t0, 1)
    SORTIE.write_text(json.dumps({"meta": meta, "resultats": sorted(resultats.values(), key=lambda x: (x["id"][0] == "C", x["id"]))},
                                 ensure_ascii=False, indent=1), encoding="utf-8")
    print("Terminé en", meta["duree_totale_s"], "s", flush=True)


if __name__ == "__main__":
    main()
