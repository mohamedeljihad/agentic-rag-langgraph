---
id: D14
titre: Sécurité des applications web (OWASP Top 10) et attaques DDoS
categorie: technique
---
# Sécurité des applications web et attaques DDoS

## OWASP Top 10
L'OWASP Top 10 est une liste de référence des risques de sécurité les plus critiques pour les applications web. L'édition 2021 comprend : le contrôle d'accès défaillant (A01), les défaillances cryptographiques (A02), les injections (A03), la conception non sécurisée (A04), la mauvaise configuration de sécurité (A05), les composants vulnérables et obsolètes (A06), les défaillances d'identification et d'authentification (A07), les défaillances d'intégrité des logiciels et des données (A08), les défaillances de journalisation et de surveillance (A09) et la falsification de requêtes côté serveur, SSRF (A10).

## Injection SQL et XSS
L'injection SQL consiste à insérer du code SQL dans une entrée utilisateur pour manipuler la base de données. La meilleure protection est l'utilisation de requêtes préparées (requêtes paramétrées), complétée par la validation des entrées et le principe du moindre privilège pour le compte d'accès à la base. Le cross-site scripting (XSS) injecte du script dans les pages vues par d'autres utilisateurs ; il se prévient par l'encodage des sorties et une politique de sécurité du contenu (CSP).

## Attaques par déni de service distribué (DDoS)
Une attaque DDoS vise à rendre un service indisponible en le saturant de requêtes provenant de nombreuses machines, souvent un réseau de machines compromises (botnet). On distingue les attaques volumétriques, les attaques sur les protocoles et les attaques applicatives. Les protections incluent les réseaux de diffusion de contenu (CDN), les services de filtrage (scrubbing), la limitation du débit et un pare-feu applicatif web (WAF).

## Bonnes pratiques
Une application exposée doit être maintenue à jour, testée régulièrement (tests d'intrusion, analyse de code) et protégée par un WAF.
