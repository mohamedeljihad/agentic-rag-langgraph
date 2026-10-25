# Synthèse de l'évaluation

Modèle : Qwen/Qwen2.5-1.5B-Instruct (int8 gate/up) — embeddings : intfloat/multilingual-e5-small

| Groupe | n | Latence moy. (s) | Hit@k | Rappel@k | MRR | Précision pert. | Couverture faits | Citation | Citation native | Score qualité |
|---|---|---|---|---|---|---|---|---|---|---|
| simple | 10 | 41.5 | 1 | 0.95 | 1.0 | 1.0 | 1.0 | 1 | 0.8 | 1.0 |
| complexe | 10 | 94.7 | 1 | 0.917 | 1.0 | 0.817 | 0.65 | 1 | 0.9 | 0.755 |
| global | 20 | 68.1 | 1 | 0.933 | 1.0 | 0.904 | 0.825 | 1 | 0.85 | 0.878 |

| ID | Latence (s) | Route | Réécr. | Docs récupérés (ordre) | Cités | Rappel | Faits | Qualité |
|---|---|---|---|---|---|---|---|---|
| S01 | 49.9 | recherche | 0 | D06 | D06 | 1.0 | 1.0 | 1.0 |
| S02 | 73.93 | recherche | 0 | D04 | D04 | 1.0 | 1.0 | 1.0 |
| S03 | 28.87 | recherche | 0 | D07, D08 | D07 | 1.0 | 1.0 | 1.0 |
| S04 | 84.57 | recherche | 0 | D11, D09 | D11 | 1.0 | 1.0 | 1.0 |
| S05 | 71.5 | recherche | 0 | D10, D09 | D10 | 1.0 | 1.0 | 1.0 |
| S06 | 17.15 | recherche | 0 | D01, D10 | D01 | 1.0 | 1.0 | 1.0 |
| S07 | 29.27 | recherche | 0 | D15 | D15 | 1.0 | 1.0 | 1.0 |
| S08 | 21.8 | recherche | 0 | D13, D04 | D13 | 1.0 | 1.0 | 1.0 |
| S09 | 38.29 | recherche | 0 | D14, D01, D02 | D14 | 1.0 | 1.0 | 1.0 |
| S10 | 0.01 | glossaire | 0 | GLOSSAIRE | GLOSSAIRE | 0.5 | 1.0 | 1.0 |
| C01 | 105.4 | recherche | 0 | D09, D06, D05 | D09, D06, D05 | 1.0 | 0.333 | 0.533 |
| C02 | 60.0 | recherche | 0 | D06, D09, D05 | D06 | 1.0 | 0.5 | 0.65 |
| C03 | 58.78 | recherche | 0 | D09, D06 | D09 | 1.0 | 0.5 | 0.65 |
| C04 | 98.74 | recherche | 0 | D02, D11, D04 | D02 | 1.0 | 1.0 | 1.0 |
| C05 | 89.58 | recherche | 0 | D07, D08 | D07 | 1.0 | 0.5 | 0.65 |
| C06 | 144.07 | recherche | 2 | D13, D03, D04 | D03, D13 | 0.667 | 0.667 | 0.767 |
| C07 | 101.46 | recherche | 2 | D15 | D15 | 0.5 | 1.0 | 1.0 |
| C08 | 72.7 | recherche | 0 | D12, D06, D05 | D06 | 1.0 | 1.0 | 1.0 |
| C09 | 95.55 | recherche | 0 | D09, D11, D02 | D09, D02 | 1.0 | 0.5 | 0.65 |
| C10 | 120.37 | recherche | 0 | D04, D10, D05, D11 | D04 | 1.0 | 0.5 | 0.65 |
