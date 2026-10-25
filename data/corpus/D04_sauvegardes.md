---
id: D04
titre: Sauvegardes et continuité d'activité
categorie: bonnes-pratiques
---
# Sauvegardes et continuité d'activité

## La règle 3-2-1
La règle de sauvegarde 3-2-1 recommande de conserver au moins trois copies des données (l'original et deux sauvegardes), sur deux supports de stockage différents, dont une copie hors site, c'est-à-dire stockée dans un autre lieu géographique. La variante 3-2-1-1-0 ajoute une copie hors ligne ou immuable, protégée contre les rançongiciels, et zéro erreur constatée lors des tests de restauration.

## Types de sauvegarde
Une sauvegarde complète copie l'intégralité des données. Une sauvegarde incrémentale ne copie que les données modifiées depuis la dernière sauvegarde, quelle qu'elle soit, tandis qu'une sauvegarde différentielle copie les données modifiées depuis la dernière sauvegarde complète.

## RPO et RTO
Le RPO (Recovery Point Objective) est la perte de données maximale admissible, exprimée en durée : avec un RPO de 24 heures, il faut au moins une sauvegarde par jour. Le RTO (Recovery Time Objective) est la durée maximale admissible d'interruption avant le rétablissement du service.

## Bonnes pratiques
Les sauvegardes doivent être chiffrées, isolées du réseau de production et testées régulièrement par des exercices de restauration : une sauvegarde jamais testée ne garantit pas la reprise. Le plan de continuité d'activité (PCA) et le plan de reprise d'activité (PRA) décrivent l'organisation à mettre en place pour maintenir ou rétablir les activités critiques après un sinistre.
