---
id: D12
titre: Chiffrement et cryptographie
categorie: technique
---
# Chiffrement et cryptographie

Le chiffrement transforme des données lisibles en données incompréhensibles pour toute personne qui ne possède pas la clé. Il protège la confidentialité des données au repos (disques, bases de données, sauvegardes) et en transit (réseau).

## Chiffrement symétrique et asymétrique
Le chiffrement symétrique utilise la même clé pour chiffrer et déchiffrer ; l'algorithme de référence est AES, avec des clés de 128, 192 ou 256 bits. Le chiffrement asymétrique utilise une paire de clés publique et privée ; il sert à l'échange de clés et à la signature numérique, avec des algorithmes comme RSA (clés d'au moins 2048 bits) ou les courbes elliptiques.

## Hachage
Une fonction de hachage produit une empreinte de taille fixe permettant de vérifier l'intégrité des données. SHA-256 est recommandé, tandis que MD5 et SHA-1 sont considérés comme obsolètes.

## TLS
Le protocole TLS chiffre les communications sur Internet (HTTPS). Les versions TLS 1.2 et TLS 1.3 doivent être privilégiées ; les versions SSL et TLS 1.0 et 1.1 sont dépréciées.

## Gestion des clés et conformité
La sécurité du chiffrement dépend de la gestion des clés : génération, stockage protégé (par exemple dans un module matériel HSM), rotation et révocation. Le chiffrement est cité par le RGPD comme mesure de sécurité appropriée au titre de l'obligation d'intégrité et de confidentialité ; en cas de violation portant sur des données correctement chiffrées, le risque pour les personnes est fortement réduit.
