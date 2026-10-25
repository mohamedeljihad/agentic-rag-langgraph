---
id: D15
titre: Gestion des vulnérabilités et score CVSS
categorie: operations
---
# Gestion des vulnérabilités et score CVSS

Une vulnérabilité est une faiblesse d'un logiciel, d'un matériel ou d'une configuration qui peut être exploitée par un attaquant. Les vulnérabilités publiques reçoivent un identifiant CVE (Common Vulnerabilities and Exposures), par exemple CVE-2021-44228 pour la faille Log4Shell.

## Le score CVSS
Le Common Vulnerability Scoring System (CVSS) attribue à chaque vulnérabilité un score de 0 à 10 selon sa gravité. Dans la version 3.1, les niveaux de sévérité sont : aucune (0,0), faible (0,1 à 3,9), moyenne (4,0 à 6,9), élevée (7,0 à 8,9) et critique (9,0 à 10,0). Le score de base prend en compte le vecteur d'attaque, la complexité, les privilèges requis, l'interaction utilisateur et l'impact sur la confidentialité, l'intégrité et la disponibilité. La version 4.0 du CVSS a été publiée en 2023.

## Processus de gestion des vulnérabilités
Le processus comprend l'inventaire des actifs, la détection des vulnérabilités (scanners, veille, bulletins des éditeurs et des CERT), l'évaluation et la priorisation selon la sévérité, l'exposition et l'exploitation active, puis la correction par l'application de correctifs (patchs) ou des mesures de contournement, et enfin la vérification.

## Priorisation
Les vulnérabilités critiques ou élevées affectant des systèmes exposés sur Internet, et celles activement exploitées, doivent être corrigées en priorité, dans des délais courts fixés par la politique de sécurité. Lorsque le correctif n'est pas disponible, des mesures compensatoires (filtrage, désactivation du service, WAF) réduisent le risque en attendant.
