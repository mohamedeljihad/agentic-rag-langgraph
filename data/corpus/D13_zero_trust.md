---
id: D13
titre: Modèle Zero Trust
categorie: architecture
---
# Modèle Zero Trust

Le modèle Zero Trust (confiance zéro) repose sur le principe « ne jamais faire confiance, toujours vérifier ». Contrairement au modèle périmétrique traditionnel, où tout ce qui se trouve à l'intérieur du réseau de l'entreprise est considéré comme fiable, Zero Trust considère qu'aucun utilisateur, appareil ou flux n'est digne de confiance par défaut, qu'il soit interne ou externe. Le cadre de référence est notamment décrit dans la publication NIST SP 800-207.

## Principes clés
- Vérification explicite de chaque demande d'accès, en tenant compte de l'identité, de l'état de l'appareil, de la localisation et du contexte.
- Principe du moindre privilège : chaque utilisateur ne reçoit que les droits strictement nécessaires, pour une durée limitée.
- Hypothèse de compromission : on considère qu'un attaquant peut déjà être présent et l'on limite les mouvements latéraux par la micro-segmentation du réseau.
- Authentification forte et continue, en particulier l'authentification multifacteur.
- Journalisation et supervision de tous les accès.

## Mise en œuvre
La mise en œuvre passe par une gestion centralisée des identités, l'accès réseau Zero Trust (ZTNA) qui remplace progressivement le VPN classique en donnant accès à des applications précises plutôt qu'à tout le réseau, et des politiques d'accès dynamiques. Ainsi, même si des identifiants sont volés, l'attaquant reste limité aux ressources autorisées et ses accès inhabituels peuvent être détectés.
