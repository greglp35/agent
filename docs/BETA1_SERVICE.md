# COMMAND OS Beta.1 — API Service + Policy Packs

Beta.1 ajoute un service HTTP standard-library et une politique RBAC deny-by-default.

## Endpoints

- `GET /health` — public.
- `GET /metrics` — métriques Prometheus text.
- `POST /v1/compile` — nécessite `local.compile`.
- `POST /v1/run` — nécessite `llm.reason`; les outils sont ensuite filtrés par RBAC et approval gate.
- `POST /v1/evaluate` — baseline cross-provider.

## Authentification

Le service reçoit un mapping de tokens injecté par l’hôte (`COMMAND_OS_API_TOKENS_JSON`). Aucun secret n’est versionné.

## Policy Packs

`policies/default.json` fournit `viewer`, `analyst`, `operator`, `administrator`. Les permissions sont additives via héritage. Tout ce qui n’est pas explicitement autorisé est refusé.

Les effets `write`, `external_side_effect`, `destructive` et `production_deploy` exigent une approbation. Les effets destructifs et les déploiements production exigent en plus un approbateur distinct.

## Fournisseurs

`registry/providers.json` ne fixe aucun nom de modèle. Le modèle est injecté par variable d’environnement (`COMMAND_OS_OPENAI_MODEL`, `COMMAND_OS_ANTHROPIC_MODEL`) afin d’éviter de figer le core sur une version fournisseur.

## Lancement

```bash
command-os-api --host 127.0.0.1 --port 8787
```
