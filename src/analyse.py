"""Synthèse des résultats (usage : python -m src.analyse [dossier_resultats]) d'évaluation : tableau récapitulatif (Markdown/CSV) et graphiques PNG."""
from __future__ import annotations

import csv
import json
import statistics as st
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from .config import CONFIG  # noqa: E402

R = Path(sys.argv[1]) if len(sys.argv) > 1 else CONFIG.results_dir  # dossier de résultats
COUL = {"simple": "#2a78d6", "complexe": "#eb6834"}   # palette catégorielle de référence (bleu, orange)
TXT, TXT2, GRILLE = "#0b0b0b", "#52514e", "#e4e3df"
METRIQUES = [("hit_at_k", "Hit@k"), ("rappel_at_k", "Rappel@k"), ("mrr", "MRR"),
             ("precision_pertinents", "Précision\n(docs pertinents)"), ("couverture_faits", "Couverture\ndes faits"),
             ("citation_correcte", "Citation\ncorrecte"), ("citation_native", "Citation\nnative"),
             ("score_qualite", "Score\nqualité")]


def enrichir(res: list[dict]) -> None:
    """Ajoute citation_native et, s'il existe, le jugement manuel (eval/jugement_manuel.json)."""
    jm_f = CONFIG.results_dir.parent / "eval" / "jugement_manuel.json"
    jm = json.loads(jm_f.read_text(encoding="utf-8")) if jm_f.exists() and R == CONFIG.results_dir else {}
    for r in res:
        r["jugement_manuel"] = jm.get(r["id"], ["", ""])[0]
    """citation_native = 1 si le LLM a cité lui-même une source valide (sans ajout automatique par « verifier »)."""
    for r in res:
        infos = " ".join(t["info"] for t in r["trace"] if t["noeud"] == "verifier")
        r["citation_native"] = int(r["citation_correcte"] == 1 and "sources ajoutées automatiquement" not in infos)


def moyenne(rs, cle):
    v = [r[cle] for r in rs if r.get(cle) is not None]
    return round(st.mean(v), 3) if v else None


def synthese(res: list[dict]) -> dict:
    out = {}
    for groupe, rs in [("simple", [r for r in res if r["type"] == "simple"]),
                       ("complexe", [r for r in res if r["type"] == "complexe"]), ("global", res)]:
        lat = [r["latence_s"] for r in rs]
        out[groupe] = {"n": len(rs), "latence_moy_s": round(st.mean(lat), 1), "latence_med_s": round(st.median(lat), 1),
                       "latence_max_s": round(max(lat), 1), "erreurs": sum(bool(r["erreur"]) for r in rs),
                       "reecritures": sum(r["nb_reecritures"] for r in rs),
                       "appels_llm_moy": round(st.mean(r["appels_llm"] for r in rs), 1),
                       **{k: moyenne(rs, k) for k, _ in METRIQUES}}
    return out


def _style(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(GRILLE)
    ax.tick_params(colors=TXT2, labelsize=8.5)
    ax.yaxis.grid(True, color=GRILLE, linewidth=0.8)
    ax.set_axisbelow(True)


def graphiques(res: list[dict], syn: dict) -> None:
    plt.rcParams.update({"font.family": "DejaVu Sans", "text.color": TXT, "axes.labelcolor": TXT2})
    # 1) latence par question
    fig, ax = plt.subplots(figsize=(9, 3.2), dpi=160)
    xs = range(len(res))
    ax.bar(xs, [r["latence_s"] for r in res], width=0.72, color=[COUL[r["type"]] for r in res],
           edgecolor="white", linewidth=1.5)
    for t in ("simple", "complexe"):
        ax.plot([-0.5, len(res) - 0.5], [syn[t]["latence_moy_s"]] * 2, color=COUL[t], linestyle=(0, (4, 3)), linewidth=1.2)
        ax.text(len(res) - 0.3, syn[t]["latence_moy_s"], f"moyenne {t} : {syn[t]['latence_moy_s']} s",
                va="center", fontsize=8, color=TXT2)
    for i, r in enumerate(res):
        if r["latence_s"] < 3:
            ax.text(i, 2, f"{r['latence_s']:.1f} s\n({r['route']})", ha="center", va="bottom", fontsize=6.5, color=TXT2)
    ax.set_xticks(list(xs), [r["id"] for r in res], fontsize=8)
    ax.set_ylabel("Latence (s)")
    ax.set_title("Temps de réponse par question (CPU, 2 cœurs)", fontsize=10, loc="left", color=TXT)
    ax.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=COUL[t]) for t in COUL], labels=["Simple", "Complexe"],
              frameon=False, fontsize=8, loc="upper left")
    _style(ax)
    ax.set_xlim(-0.6, len(res) + 3.6)
    fig.tight_layout(); fig.savefig(R / "latence_par_question.png"); plt.close(fig)

    # 2) métriques moyennes par type
    fig, ax = plt.subplots(figsize=(9.5, 3.2), dpi=160)
    w = 0.38
    for j, t in enumerate(("simple", "complexe")):
        vals = [syn[t][k] or 0 for k, _ in METRIQUES]
        pos = [i + (j - 0.5) * w for i in range(len(METRIQUES))]
        ax.bar(pos, vals, width=w - 0.04, color=COUL[t], label=t.capitalize(), edgecolor="white", linewidth=1)
        for p, v in zip(pos, vals):
            ax.text(p, v + 0.02, f"{v:.2f}", ha="center", fontsize=7, color=TXT2)
    ax.set_xticks(range(len(METRIQUES)), [l for _, l in METRIQUES], fontsize=8)
    ax.set_ylim(0, 1.12)
    ax.set_title("Pertinence des documents et qualité des réponses (moyennes)", fontsize=10, loc="left", color=TXT)
    ax.legend(frameon=False, fontsize=8, ncol=2, loc="upper right", bbox_to_anchor=(1, 1.13))
    _style(ax)
    fig.tight_layout(); fig.savefig(R / "metriques_par_type.png"); plt.close(fig)


def main() -> None:
    data = json.loads((R / "eval_results.json").read_text(encoding="utf-8"))
    res = data["resultats"]
    enrichir(res)
    syn = synthese(res)
    (R / "summary.json").write_text(json.dumps({"meta": data["meta"], "synthese": syn}, ensure_ascii=False, indent=1),
                                    encoding="utf-8")
    champs = ["id", "type", "latence_s", "route", "nb_reecritures", "hit_at_k", "rappel_at_k", "mrr",
              "precision_pertinents", "couverture_faits", "citation_correcte", "citation_native", "score_qualite", "jugement_manuel", "ancrage",
              "appels_llm", "sources_attendues", "docs_recuperes", "docs_pertinents", "sources_citees", "question",
              "reponse", "erreur"]
    with open(R / "eval_results.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=champs, extrasaction="ignore")
        w.writeheader()
        for r in res:
            w.writerow({k: (";".join(r[k]) if isinstance(r[k], list) else r[k]) for k in champs})
    lignes = ["| Groupe | n | Latence moy. (s) | Hit@k | Rappel@k | MRR | Précision pert. | Couverture faits | Citation | Citation native | Score qualité |",
              "|---|---|---|---|---|---|---|---|---|---|---|"]
    for g in ("simple", "complexe", "global"):
        s = syn[g]
        lignes.append(f"| {g} | {s['n']} | {s['latence_moy_s']} | {s['hit_at_k']} | {s['rappel_at_k']} | {s['mrr']} | "
                      f"{s['precision_pertinents']} | {s['couverture_faits']} | {s['citation_correcte']} | {s['citation_native']} | {s['score_qualite']} |")
    detail = ["", "| ID | Latence (s) | Route | Réécr. | Docs récupérés (ordre) | Cités | Rappel | Faits | Qualité | Jugement manuel |",
              "|---|---|---|---|---|---|---|---|---|---|"]
    for r in res:
        detail.append(f"| {r['id']} | {r['latence_s']} | {r['route']} | {r['nb_reecritures']} | "
                      f"{', '.join(r['docs_recuperes'][:5])} | {', '.join(r['sources_citees'])} | {r['rappel_at_k']} | "
                      f"{r['couverture_faits']} | {r['score_qualite']} | {r.get('jugement_manuel', '')} |")
    (R / "summary.md").write_text("# Synthèse de l'évaluation\n\n" + f"Modèle : {data['meta']['llm']} — embeddings : "
                                  f"{data['meta']['embeddings']}\n\n" + "\n".join(lignes + detail) + "\n", encoding="utf-8")
    from collections import Counter
    for g in ("simple", "complexe"):
        syn[g]["jugement_manuel"] = dict(Counter(r["jugement_manuel"] for r in res if r["type"] == g and r["jugement_manuel"]))
    (R / "summary.json").write_text(json.dumps({"meta": data["meta"], "synthese": syn}, ensure_ascii=False, indent=1),
                                    encoding="utf-8")
    graphiques(res, syn)
    print("\n".join(lignes))


if __name__ == "__main__":
    main()
