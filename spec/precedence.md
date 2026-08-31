# COMMAND OS CORE v2 — Règles de précédence

## Ordre de priorité

1. Règles système, sécurité, conformité et politiques.
2. Séquencement explicite `>>`.
3. Intention explicite de l’utilisateur.
4. Commandes principales.
5. Méthodes et modificateurs.
6. Format de présentation.

## Normalisation des commandes non strictes

Sans `>>`, le runtime peut réordonner les commandes à l’intérieur d’un même segment
selon les phases suivantes :

1. ROLE — `/expert`, `/council`
2. ACQUIRE — `/research`, `/verify`, `/benchmark`, `/data`
3. REASON — `/deepthink`, `/challenge`
4. ANALYZE/DESIGN — `/audit`, `/debug`, `/risk`, `/spec`, `/compare`, `/architect`, etc.
5. PRIORITIZE — `/prioritize`
6. DECIDE — `/decision`
7. PLAN — `/plan`
8. EXECUTE — `/build`, `/automate`
9. TEST — `/test`
10. PRESENT — `/write`, `/copywriter`, `/summarize`, `/teach`
11. CONTINUITY — `/continue`, `/next`, etc.

Le runtime ne doit jamais modifier silencieusement l’objectif utilisateur.

## Profondeur

`--fast`, `--standard`, `--deep`, `--forensic` sont mutuellement exclusifs.
Si plusieurs sont fournis, la dernière valeur explicite gagne et un avertissement
de normalisation est émis.

## Ordre strict

`A >> B` signifie que B consomme conceptuellement la sortie de A.
Le runtime ne doit pas inverser les deux étapes.
