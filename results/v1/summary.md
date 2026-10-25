# Synthèse de l'évaluation

Modèle : Qwen/Qwen2.5-1.5B-Instruct (int8 gate/up) — embeddings : intfloat/multilingual-e5-small

| Groupe | n | Latence moy. (s) | Hit@k | Rappel@k | MRR | Précision pert. | Couverture faits | Citation | Citation native | Score qualité |
|---|---|---|---|---|---|---|---|---|---|---|
| simple | 10 | 34.5 | 1 | 0.95 | 1.0 | 1.0 | 0.925 | 1 | 1 | 0.948 |
| complexe | 10 | 87.1 | 1 | 0.917 | 1.0 | 0.817 | 0.608 | 1 | 0.9 | 0.726 |
| global | 20 | 60.8 | 1 | 0.933 | 1.0 | 0.904 | 0.767 | 1 | 0.95 | 0.837 |

| ID | Latence (s) | Route | Réécr. | Docs récupérés (ordre) | Cités | Rappel | Faits | Qualité |
|---|---|---|---|---|---|---|---|---|
| S01 | 56.53 | recherche | 0 | D06 | D06 | 1.0 | 1.0 | 1.0 |
| S02 | 49.57 | recherche | 0 | D04 | D04 | 1.0 | 1.0 | 1.0 |
| S03 | 29.99 | recherche | 0 | D07, D08 | D07 | 1.0 | 1.0 | 1.0 |
| S04 | 36.56 | recherche | 0 | D11, D09 | D11 | 1.0 | 0.25 | 0.475 |
| S05 | 69.02 | recherche | 0 | D10, D09 | D10 | 1.0 | 1.0 | 1.0 |
| S06 | 16.62 | recherche | 0 | D01, D10 | D01 | 1.0 | 1.0 | 1.0 |
| S07 | 31.69 | recherche | 0 | D15 | D15 | 1.0 | 1.0 | 1.0 |
| S08 | 20.26 | recherche | 0 | D13, D04 | D13 | 1.0 | 1.0 | 1.0 |
| S09 | 35.01 | recherche | 0 | D14, D01, D02 | D14 | 1.0 | 1.0 | 1.0 |
| S10 | 0.01 | glossaire | 0 | GLOSSAIRE | GLOSSAIRE | 0.5 | 1.0 | 1.0 |
| C01 | 102.89 | recherche | 0 | D09, D06, D05 | D09, D06, D05 | 1.0 | 0.333 | 0.533 |
| C02 | 71.59 | recherche | 0 | D06, D09, D05 | D06 | 1.0 | 1.0 | 1.0 |
| C03 | 55.78 | recherche | 0 | D09, D06 | D09 | 1.0 | 0.5 | 0.65 |
| C04 | 100.5 | recherche | 0 | D02, D11, D04 | D02 | 1.0 | 0.75 | 0.825 |
| C05 | 92.09 | recherche | 0 | D07, D08 | D07, D08 | 1.0 | 1.0 | 1.0 |
| C06 | 117.97 | recherche | 2 | D13, D03, D04 | D03, D13 | 0.667 | 0.667 | 0.767 |
| C07 | 91.13 | recherche | 2 | D15 | D15 | 0.5 | 0.667 | 0.767 |
| C08 | 63.22 | recherche | 0 | D12, D06, D05 | D06 | 1.0 | 0.667 | 0.767 |
| C09 | 90.56 | recherche | 0 | D09, D11, D02 | D02 | 1.0 | 0.5 | 0.65 |
| C10 | 85.74 | recherche | 0 | D04, D10, D05, D11 | D04 | 1.0 | 0.0 | 0.3 |
