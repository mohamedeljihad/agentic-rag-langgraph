"""Génère la vidéo de démonstration (≤ 2 min, 1280x720) à partir des VRAIS résultats d'exécution.

Diapositives dessinées avec Pillow, voix off française (edge-tts, sinon gTTS, sinon espeak-ng),
assemblage avec ffmpeg. Usage : python scripts/make_video.py [sortie.mp4]
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "results"
BUILD = ROOT / "video" / "build"
W, H = 1280, 720
BLEU, ORANGE, ENCRE, ENCRE2, FOND, CARTE = "#1f5f8b", "#eb6834", "#16202a", "#52514e", "#f7f8fa", "#ffffff"
F = "/usr/share/fonts/truetype/dejavu/DejaVuSans{}.ttf"


def police(taille, style=""):
    return ImageFont.truetype(F.format(style), taille)


def mono(taille):
    return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", taille)


def base(titre: str, etape: str = ""):
    im = Image.new("RGB", (W, H), FOND)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 78], fill=BLEU)
    d.text((40, 20), titre, font=police(32, "-Bold"), fill="white")
    if etape:
        d.text((W - 40, 28), etape, font=police(20), fill="#cfe3f2", anchor="ra")
    d.text((40, H - 32), "Agentic RAG avec LangGraph — Mohammed ELJIHAD — Master II-BDCC, ENSET", font=police(15), fill=ENCRE2)
    return im, d


def paragraphe(d, xy, texte, taille=22, largeur=70, couleur=ENCRE, interligne=1.35, style=""):
    x, y = xy
    for ligne in texte.split("\n"):
        for l in textwrap.wrap(ligne, largeur) or [""]:
            d.text((x, y), l, font=police(taille, style), fill=couleur)
            y += int(taille * interligne)
    return y


def diapos(res, syn, meta, memo):
    par_id = {r["id"]: r for r in res}
    S = []

    # 1. Titre
    im = Image.new("RGB", (W, H), BLEU); d = ImageDraw.Draw(im)
    d.text((W // 2, 230), "Agent RAG agentique avec LangGraph", font=police(50, "-Bold"), fill="white", anchor="mm")
    d.text((W // 2, 300), "Questions complexes sur une base documentaire cybersécurité & réglementation",
           font=police(24), fill="#dbeaf5", anchor="mm")
    d.text((W // 2, 420), "Mohammed ELJIHAD — Master II-BDCC, ENSET", font=police(26, "-Bold"), fill="white", anchor="mm")
    d.text((W // 2, 462), "Module SMA et IAD — Pr. Sara RETAL", font=police(22), fill="#dbeaf5", anchor="mm")
    S.append((im, "Bonjour. Je présente mon agent RAG agentique construit avec LangGraph. Il répond à des questions "
                  "complexes sur une base documentaire de cybersécurité et de réglementation numérique."))

    # 2. Données et modèles
    im, d = base("1. Base documentaire et modèles", "prétraitement")
    y = paragraphe(d, (60, 120), "• 15 documents rédigés par l'auteur : RGPD, NIS2, lois marocaines 09-08 et 05-20, "
                   "ISO 27001, rançongiciels, hameçonnage, Zero Trust, CVSS…", 24, 75)
    y = paragraphe(d, (60, y + 14), "• Nettoyage Markdown, découpage par paragraphes et phrases (≈ 650 caractères, "
                   "recouvrement 120) : 58 fragments", 24, 75)
    y = paragraphe(d, (60, y + 14), f"• Vectorisation : {meta['embeddings']} + index FAISS (cosinus)", 24, 75)
    y = paragraphe(d, (60, y + 14), f"• LLM local sur CPU : {meta['llm']}", 24, 75)
    y = paragraphe(d, (60, y + 14), "• Outils : recherche sémantique, calculatrice sûre, glossaire, liste des documents", 24, 75)
    S.append((im, "J'ai rédigé quinze documents en français. Ils sont nettoyés, découpés en cinquante-huit fragments, "
                  "puis vectorisés avec le modèle E5 multilingue et indexés dans FAISS. Le modèle de langage est "
                  "Qwen 2.5 de 1,5 milliard de paramètres, exécuté sur CPU avec une quantification int8 partielle."))

    # 3. Graphe
    im, d = base("2. Architecture du graphe LangGraph", "StateGraph + MemorySaver")
    g = Image.open(ROOT / "docs" / "graph.png").convert("RGB")
    g.thumbnail((440, 555))
    im.paste(g, (60, 95))
    x = 560
    y = paragraphe(d, (x, 120), "contextualiser : mémoire du fil (thread_id)", 21, 52)
    y = paragraphe(d, (x, y + 8), "analyser : routeur règles + LLM (direct / glossaire / recherche)", 21, 52)
    y = paragraphe(d, (x, y + 8), "planifier : décomposition en sous-questions", 21, 52)
    y = paragraphe(d, (x, y + 8), "rechercher → évaluer : notation de la pertinence", 21, 52)
    y = paragraphe(d, (x, y + 8), "boucle reecrire → rechercher (max 2)", 21, 52, ORANGE, style="-Bold")
    y = paragraphe(d, (x, y + 8), "calculer : outil calculatrice", 21, 52)
    y = paragraphe(d, (x, y + 8), "generer → verifier : citations [Dxx], ancrage", 21, 52)
    S.append((im, "Le graphe est un StateGraph explicite. La question est d'abord contextualisée grâce à la mémoire, "
                  "puis un routeur choisit entre réponse directe, glossaire ou recherche. Les questions complexes sont "
                  "décomposées, les documents sont notés, et une arête conditionnelle relance la recherche avec une "
                  "requête reformulée si rien n'est pertinent. La réponse est enfin générée, citée et vérifiée."))

    # 4. Trace réelle d'une question complexe (calcul)
    r = par_id["C02"]
    im, d = base("3. Exécution réelle — question complexe avec calcul", f"C02 — {r['latence_s']:.0f} s")
    y = paragraphe(d, (50, 100), "Q : " + r["question"], 20, 105, BLEU, style="-Bold")
    y += 6
    for t in r["trace"]:
        d.text((60, y), f"{t['noeud']:<18}{t['duree_s']:>6.1f} s  {t['info'][:78]}", font=mono(15), fill=ENCRE)
        y += 23
    y = paragraphe(d, (50, y + 10), "R : " + r["reponse"][:430], 18, 118, ENCRE)
    S.append((im, "Voici une trace réelle. Pour cette question sur l'amende du RGPD, le routeur propose à tort une réponse "
                  "directe, mais le garde-fou par similarité impose la recherche. Les fragments sont notés, puis l'outil "
                  "calculatrice évalue l'expression proposée par le modèle : quarante millions d'euros, avec la source D06."))

    # 5. Question de comparaison
    r = par_id["C01"]
    im, d = base("4. Exécution réelle — comparaison multi-documents", f"C01 — {r['latence_s']:.0f} s")
    y = paragraphe(d, (50, 100), "Q : " + r["question"], 20, 105, BLEU, style="-Bold")
    y = paragraphe(d, (50, y + 6), "Sous-questions : " + " | ".join(r["sous_questions"]), 17, 125, ENCRE2)
    y = paragraphe(d, (50, y + 6), f"Documents récupérés : {', '.join(r['docs_recuperes'])}   —   "
                   f"jugés pertinents : {', '.join(r['docs_pertinents'])}", 17, 125, ENCRE2)
    y = paragraphe(d, (50, y + 12), "R : " + r["reponse"][:640] + " […]", 18, 118)
    paragraphe(d, (50, max(y + 10, 600)), "Jugement manuel : partiel — délais NIS2 (24 h / 72 h / 1 mois) absents de la réponse.",
               18, 118, ORANGE, style="-Bold")
    S.append((im, "Pour une comparaison entre le RGPD et NIS2, le planificateur produit deux sous-questions, recherchées "
                  "séparément, et les fragments des deux textes sont fusionnés. La réponse traite bien le RGPD, mais omet "
                  "les délais de NIS2 : c'est une limite du petit modèle."))

    # 6. Mémoire
    im, d = base("5. Mémoire conversationnelle (MemorySaver, même thread_id)", "checkpointer")
    y = 110
    for i, t in enumerate(memo["tours"], 1):
        y = paragraphe(d, (50, y), f"Tour {i} — Utilisateur : {t['question']}", 20, 105, BLEU, style="-Bold")
        if i > 1:
            y = paragraphe(d, (70, y + 2), f"Question reformulée : {t['question_autonome']}", 18, 110, ORANGE)
        y = paragraphe(d, (70, y + 4), "Agent : " + t["reponse"][:300], 17, 120)
        y += 18
    S.append((im, "La mémoire repose sur le checkpointer MemorySaver. Au deuxième tour, la question elliptique "
                  "est reformulée à partir de l'historique du même fil de discussion."))

    # 7. Résultats
    im, d = base("6. Évaluation réelle : 10 questions simples + 10 complexes")
    m = Image.open(RES / "metriques_par_type.png").convert("RGB"); m.thumbnail((1180, 420))
    im.paste(m, (50, 92))
    s, c = syn["simple"], syn["complexe"]
    paragraphe(d, (60, 92 + m.height + 12),
               f"Latence moyenne : {s['latence_moy_s']} s (simples) / {c['latence_moy_s']} s (complexes) sur CPU 2 cœurs.   "
               f"Hit@k : {s['hit_at_k']:.2f} / {c['hit_at_k']:.2f}.   Score qualité : {s['score_qualite']:.2f} / {c['score_qualite']:.2f}.",
               19, 115)
    S.append((im, f"Sur les vingt questions, la bonne source est retrouvée dans {round(syn['global']['hit_at_k']*100)} pour cent "
                  f"des cas. Le score de qualité moyen est de {str(s['score_qualite']).replace('.', ',')} pour les questions simples "
                  f"et de {str(c['score_qualite']).replace('.', ',')} pour les complexes. La latence moyenne est d'environ "
                  f"{round(s['latence_moy_s'])} secondes pour une question simple et {round(c['latence_moy_s'])} secondes "
                  f"pour une complexe, sur deux cœurs CPU."))

    # 8. Limites
    im, d = base("7. Limites et améliorations", "conclusion")
    y = paragraphe(d, (60, 120), "• Petit modèle local : réponses partielles sur 5 questions complexes sur 10, "
                   "1 réponse incorrecte (C10), latence de 38 à 84 s en moyenne sur CPU", 24, 75)
    y = paragraphe(d, (60, y + 12), "• Boucle de réécriture validée hors jeu de test (« OIV obligations ») mais "
                   "reformulations parfois inexactes", 24, 75)
    y = paragraphe(d, (60, y + 12), "• Métrique de qualité automatique (faits clés + citations) : approximative", 24, 75)
    y = paragraphe(d, (60, y + 12), "• Améliorations : LLM plus grand via API (déjà branchable), reranker cross-encoder, "
                   "recherche hybride BM25 + vecteurs, évaluation LLM-juge / RAGAS", 24, 75)
    S.append((im, "Les limites viennent surtout du petit modèle local : réponses partielles sur les comparaisons, un calcul "
                  "raté et une latence élevée. "
                  "Le système accepte déjà un modèle plus puissant via une API compatible OpenAI. Merci de votre attention."))
    return S


def tts(texte: str, mp3: Path) -> None:
    if shutil.which("edge-tts"):
        r = subprocess.run(["edge-tts", "--voice", "fr-FR-HenriNeural", "--rate", "+14%", "--text", texte,
                            "--write-media", str(mp3)] + (["--proxy", p] if (p := __import__("os").environ.get("HTTPS_PROXY")) else []),
                           capture_output=True)
        if r.returncode == 0 and mp3.exists() and mp3.stat().st_size > 1000:
            return
    try:
        from gtts import gTTS
        gTTS(texte, lang="fr").save(str(mp3)); return
    except Exception:  # noqa: BLE001
        pass
    wav = mp3.with_suffix(".wav")
    subprocess.run(["espeak-ng", "-v", "fr", "-w", str(wav), texte], check=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav), str(mp3)], check=True)


def duree(f: Path) -> float:
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
                                          "default=nw=1:nk=1", str(f)]).strip())


def main() -> None:
    sortie = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "video" / "demo_agentic_rag.mp4"
    BUILD.mkdir(parents=True, exist_ok=True)
    data = json.loads((RES / "eval_results.json").read_text(encoding="utf-8"))
    syn = json.loads((RES / "summary.json").read_text(encoding="utf-8"))["synthese"]
    memo = json.loads((RES / "memoire_demo.json").read_text(encoding="utf-8"))
    clips = []
    for i, (im, texte) in enumerate(diapos(data["resultats"], syn, data["meta"], memo)):
        png, mp3, mp4 = BUILD / f"s{i}.png", BUILD / f"s{i}.mp3", BUILD / f"s{i}.mp4"
        im.save(png); tts(texte, mp3)
        dur = duree(mp3) + 0.4
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-i", str(png), "-i", str(mp3),
                        "-af", "apad=pad_dur=0.4", "-t", f"{dur:.2f}", "-c:v", "libx264", "-tune", "stillimage",
                        "-pix_fmt", "yuv420p", "-r", "25", "-c:a", "aac", "-b:a", "128k", "-ar", "44100", str(mp4)],
                       check=True)
        clips.append(mp4)
        print(f"diapo {i}: {dur:.1f} s")
    liste = BUILD / "liste.txt"
    liste.write_text("".join(f"file '{c}'\n" for c in clips))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(liste), "-c", "copy",
                    str(sortie)], check=True)
    print("Vidéo :", sortie, f"{duree(sortie):.1f} s")


if __name__ == "__main__":
    main()
