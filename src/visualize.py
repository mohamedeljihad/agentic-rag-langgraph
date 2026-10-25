"""Visualisation du graphe : texte Mermaid + PNG (API mermaid.ink, sinon rendu local avec mmdc)."""
from __future__ import annotations

import shutil
import subprocess

from .config import ROOT
from .graph import construire_graphe

DOCS = ROOT / "docs"


def main() -> None:
    DOCS.mkdir(exist_ok=True)
    g = construire_graphe().get_graph()
    mermaid = g.draw_mermaid()
    (DOCS / "graph.mmd").write_text(mermaid, encoding="utf-8")
    png = DOCS / "graph.png"
    # variante horizontale (utilisée dans le rapport), rendue localement si mmdc est disponible
    (DOCS / "graph_lr.mmd").write_text(mermaid.replace("graph TD;", "graph LR;"), encoding="utf-8")
    if shutil.which("mmdc"):
        cfg = DOCS / "mermaid_config.json"
        cfg.write_text('{"themeVariables":{"fontSize":"26px"},"flowchart":{"nodeSpacing":18,"rankSpacing":30,"padding":6}}')
        subprocess.run([shutil.which("mmdc"), "-i", str(DOCS / "graph_lr.mmd"), "-o", str(DOCS / "graph_lr.png"),
                        "-c", str(cfg), "-w", "2000", "-b", "white", "-s", "2"], check=False, capture_output=True)
    try:
        png.write_bytes(g.draw_mermaid_png())
        print("PNG généré via draw_mermaid_png ->", png)
        return
    except Exception as e:  # noqa: BLE001 - réseau souvent indisponible
        print("draw_mermaid_png indisponible :", str(e)[:120])
    mmdc = shutil.which("mmdc")
    if not mmdc:
        print("mmdc introuvable : seul docs/graph.mmd a été produit.")
        return
    subprocess.run([mmdc, "-i", str(DOCS / "graph.mmd"), "-o", str(png), "-w", "1400", "-b", "white", "-s", "2"],
                   check=True)
    print("PNG généré via mmdc ->", png)


if __name__ == "__main__":
    main()
