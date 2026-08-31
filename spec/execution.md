# COMMAND OS CORE v2 — Contrat d’exécution

Le runtime sépare toujours **intention** et **capacité**.

Statuts :
- EXECUTED
- PARTIALLY_EXECUTED
- SIMULATED
- BLOCKED
- NOT_AVAILABLE

Une action ne peut être marquée EXECUTED que si un adapter réel confirme son exécution.

Les Quality Gates structurels peuvent être vérifiés localement.
Les Quality Gates sémantiques exigent l’hôte LLM/outils.
