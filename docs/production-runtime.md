# Alpha.5 — Production Host Integrations

## Objectif

Alpha.5 transforme le runtime sémantique en couche exploitable en production sans enfermer COMMAND OS dans un fournisseur.

## Fournisseurs LLM

- `OpenAIResponsesAdapter` : Responses API, clé via `OPENAI_API_KEY`, `store=False` par défaut.
- `AnthropicMessagesAdapter` : Messages API, clé via `ANTHROPIC_API_KEY`.

Les deux adapters utilisent un transport HTTP injectable : les tests n’ont donc aucun appel réseau.

## Résilience

`ResilientLLMAdapter` ajoute : retry exponentiel, circuit breaker, budgets requêtes/tokens/coût/latence et journalisation.

## Effets externes

`GuardedToolAdapter` classe chaque capability : `read`, `write`, `external_side_effect`, `destructive`, `production_deploy`. Les effets sensibles exigent une approbation explicite.

## Secrets

`ExecutionJournal` masque les clés, tokens, mots de passe et entêtes Authorization avant persistance.

## Évaluations

`EvaluationHarness` exécute un corpus JSON de cas de compilation et d’exécution sémantique.
