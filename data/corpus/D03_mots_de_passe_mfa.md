---
id: D03
titre: Mots de passe et authentification multifacteur (MFA)
categorie: bonnes-pratiques
---
# Mots de passe et authentification multifacteur

## Mots de passe robustes
Un mot de passe robuste est long et imprévisible. Une recommandation courante est d'utiliser au moins 12 caractères mêlant majuscules, minuscules, chiffres et caractères spéciaux, ou une phrase de passe composée de plusieurs mots aléatoires. Chaque compte doit avoir un mot de passe unique afin d'éviter le « credential stuffing », c'est-à-dire la réutilisation automatisée d'identifiants volés sur d'autres services. Un gestionnaire de mots de passe facilite cette pratique.

Côté serveur, les mots de passe ne doivent jamais être stockés en clair : ils sont conservés sous forme d'empreinte calculée avec une fonction de hachage lente et salée comme bcrypt, scrypt ou Argon2.

## Authentification multifacteur
L'authentification multifacteur (MFA) exige au moins deux facteurs de nature différente : un facteur de connaissance (ce que l'on sait, comme un mot de passe ou un code PIN), un facteur de possession (ce que l'on possède, comme un téléphone, une application d'authentification ou une clé de sécurité physique) et un facteur d'inhérence (ce que l'on est, comme une empreinte digitale).

La MFA réduit fortement le risque de compromission de compte, même lorsqu'un mot de passe a été volé par hameçonnage. Les méthodes résistantes à l'hameçonnage, comme les clés FIDO2/WebAuthn, sont préférables aux codes envoyés par SMS, qui peuvent être interceptés ou détournés par échange de carte SIM. La MFA doit être activée en priorité sur la messagerie, les accès distants (VPN) et les comptes administrateurs.
