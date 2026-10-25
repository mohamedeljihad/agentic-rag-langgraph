# Synthèse de l'évaluation

Modèle : Qwen/Qwen2.5-1.5B-Instruct (int8 gate/up) — embeddings : intfloat/multilingual-e5-small

| Groupe | n | Latence moy. (s) | Hit@k | Rappel@k | MRR | Précision pert. | Couverture faits | Citation | Citation native | Score qualité |
|---|---|---|---|---|---|---|---|---|---|---|
| simple | 10 | 38.1 | 1 | 0.95 | 1.0 | 1.0 | 1.0 | 1 | 0.8 | 1.0 |
| complexe | 10 | 84.3 | 1 | 0.917 | 1.0 | 0.817 | 0.65 | 1 | 0.9 | 0.755 |
| global | 20 | 61.2 | 1 | 0.933 | 1.0 | 0.904 | 0.825 | 1 | 0.85 | 0.878 |

| ID | Latence (s) | Route | Réécr. | Docs récupérés (ordre) | Cités | Rappel | Faits | Qualité | Jugement manuel |
|---|---|---|---|---|---|---|---|---|---|
| S01 | 50.99 | recherche | 0 | D06 | D06 | 1.0 | 1.0 | 1.0 | correct |
| S02 | 72.53 | recherche | 0 | D04 | D04 | 1.0 | 1.0 | 1.0 | correct |
| S03 | 29.23 | recherche | 0 | D07, D08 | D07 | 1.0 | 1.0 | 1.0 | correct |
| S04 | 81.0 | recherche | 0 | D11, D09 | D11 | 1.0 | 1.0 | 1.0 | correct |
| S05 | 43.33 | recherche | 0 | D10, D09 | D10 | 1.0 | 1.0 | 1.0 | correct |
| S06 | 17.99 | recherche | 0 | D01, D10 | D01 | 1.0 | 1.0 | 1.0 | correct |
| S07 | 29.07 | recherche | 0 | D15 | D15 | 1.0 | 1.0 | 1.0 | correct |
| S08 | 20.48 | recherche | 0 | D13, D04 | D13 | 1.0 | 1.0 | 1.0 | correct |
| S09 | 36.38 | recherche | 0 | D14, D01, D02 | D14 | 1.0 | 1.0 | 1.0 | correct |
| S10 | 0.01 | glossaire | 0 | GLOSSAIRE | GLOSSAIRE | 0.5 | 1.0 | 1.0 | correct |
| C01 | 102.43 | recherche | 0 | D09, D06, D05 | D09, D06, D05 | 1.0 | 0.333 | 0.533 | partiel |
| C02 | 54.55 | recherche | 0 | D06, D09, D05 | D06 | 1.0 | 0.5 | 0.65 | correct |
| C03 | 55.14 | recherche | 0 | D09, D06 | D09 | 1.0 | 0.5 | 0.65 | correct |
| C04 | 95.38 | recherche | 0 | D02, D11, D04 | D02 | 1.0 | 1.0 | 1.0 | correct |
| C05 | 81.99 | recherche | 0 | D07, D08 | D07 | 1.0 | 0.5 | 0.65 | partiel |
| C06 | 105.77 | recherche | 0 | D13, D03, D04 | D03, D13 | 0.667 | 0.667 | 0.767 | correct |
| C07 | 74.04 | recherche | 0 | D15 | D15 | 0.5 | 1.0 | 1.0 | partiel |
| C08 | 65.91 | recherche | 0 | D12, D06, D05 | D06 | 1.0 | 1.0 | 1.0 | partiel |
| C09 | 90.58 | recherche | 0 | D09, D11, D02 | D09, D02 | 1.0 | 0.5 | 0.65 | partiel |
| C10 | 117.48 | recherche | 0 | D04, D10, D05, D11 | D04 | 1.0 | 0.5 | 0.65 | incorrect |
