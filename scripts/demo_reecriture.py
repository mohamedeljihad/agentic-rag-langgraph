"""Démonstration de la boucle évaluer -> reecrire -> rechercher sur des questions mal formulées (hors jeu d'évaluation).
Usage : python scripts/demo_reecriture.py "question 1" "question 2" …  -> results/demo_reecriture.json"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.graph import Agent  # noqa: E402

agent, sortie = Agent(), []
for i, q in enumerate(sys.argv[1:]):
    t0 = time.time()
    r = agent.ask(q, thread_id=f"demo-reecriture-{i}")
    sortie.append({"question": q, "latence_s": round(time.time() - t0, 1), "nb_reecritures": r["nb_reecritures"],
                   "docs_pertinents": list(dict.fromkeys(d["doc_id"] for d in r["documents"] if d["pertinent"])),
                   "reponse": r["reponse"], "trace": r["trace"]})
    print(f"\n### {q} ({sortie[-1]['latence_s']} s, réécritures={r['nb_reecritures']})")
    for t in r["trace"]:
        print(f"  {t['noeud']:<18}{t['duree_s']:>6.1f} s  {t['info'][:160]}")
    print(r["reponse"])
Path(__file__).resolve().parent.parent.joinpath("results", "demo_reecriture.json").write_text(
    json.dumps(sortie, ensure_ascii=False, indent=1), encoding="utf-8")
