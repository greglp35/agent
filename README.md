# COMMAND OS CORE v2.0 — Expert Council Runtime

COMMAND OS est un langage d’orchestration pour piloter une IA par intentions stables,
méthodes de raisonnement, expertises spécialisées, contrôles qualité et contrats de sortie.

## Principe

INTENTION → COMMANDE → MÉTHODE → CONTRÔLES → LIVRABLE → ACTION SUIVANTE

Exemple :

```text
/council /audit /decision mon application --forensic --security --terrain
```

Le système doit :
1. identifier le sujet et le domaine ;
2. sélectionner les expertises pertinentes ;
3. construire un pipeline cohérent ;
4. exécuter les méthodes exigées ;
5. challenger les conclusions ;
6. produire un résultat exploitable ;
7. signaler les limites, incertitudes et actions non exécutées.

## Contenu de cette version

- `kernel/kernel-full.md` : noyau portable de COMMAND OS.
- `spec/grammar.ebnf` : grammaire normative.
- `registry/commands.json` : registre machine des commandes.
- `registry/methods.json` : méthodes de raisonnement.
- `registry/modifiers.json` : modificateurs universels.
- `registry/macros.json` : pipelines prédéfinis.
- `experts/expert-registry.json` : premier registre d’experts.
- `tests/compliance-tests.json` : tests de conformité initiaux.

## Statut

Version actuelle : `2.0.0-alpha.5`

Le projet dispose maintenant d’un parser/runtime, d’un routeur d’experts, d’un Capability Resolver, d’un moteur sémantique host-neutral et d’une couche d’intégration production avec résilience, budgets, approval gates et adapters fournisseurs.

## Alpha.2 — Parser Runtime

Cette version ajoute un prototype exécutable :

- parsing des slash commands ;
- séparation stricte avec `>>` ;
- normalisation des pipelines non stricts ;
- expansion des macros ;
- résolution des profondeurs conflictuelles ;
- reconnaissance des méthodes avancées ;
- frontières commande/donnée ;
- routage automatique d’experts ;
- génération d’un plan d’exécution ;
- Quality Gate ;
- diagnostics structurés ;
- CLI locale.

### Test rapide

```bash
cd COMMAND_OS_CORE_v2
python -m runtime.cli /expert /audit "application de gestion de stock" --forensic --security
```

Ou :

```bash
./command-os /council /audit /decision "mon application" --forensic --security --terrain
```

## Alpha.3 — Execution Contract & Capability Resolver

Cette version ajoute :
- manifeste de capacités ;
- séparation intention/capacité ;
- `run_command()` ;
- adapters d’exécution plug-in ;
- statuts d’exécution explicites ;
- état de travail JSON ;
- trace JSONL ;
- Quality Gate structurel.

## Alpha.4 — Host Adapters + Semantic Runtime

Alpha.4 transforme le runtime de planification en moteur sémantique **host-neutral** :

- contrat `LLMAdapter` indépendant du fournisseur ;
- contrat `ToolAdapter` pour capacités externes réelles ;
- `run_semantic()` et `SemanticRuntime` ;
- injection structurée des Expert Packs dans chaque étape ;
- chaînage des sorties entre commandes ;
- `/council` avec avis indépendants, désaccords et arbitrage séparé ;
- parallélisation contrôlée du conseil ;
- Quality Gates sémantiques ;
- continuité state-aware.

Voir `docs/HOST_ADAPTERS.md`.

## Alpha.5 — Production Host Integrations

Alpha.5 ajoute la couche nécessaire pour brancher COMMAND OS sur de vrais fournisseurs et outils sans perdre la vérité d’exécution :

- `OpenAIResponsesAdapter` pour la Responses API ;
- `AnthropicMessagesAdapter` pour la Messages API ;
- transport HTTP JSON injectable, donc testable sans réseau ;
- `ResilientLLMAdapter` avec retry exponentiel, circuit breaker et budgets ;
- budgets requêtes, tokens, coût et latence ;
- `GuardedToolAdapter` avec classification des effets externes ;
- approval gate obligatoire par défaut pour écriture, effet externe, destruction et déploiement production ;
- `ExecutionJournal` persistant avec redaction des secrets ;
- `tool_requests` explicites : le modèle peut demander une action, mais seul l’adapter réel peut l’exécuter ;
- `EvaluationHarness` et corpus d’évaluation ;
- aucune clé API stockée dans le dépôt.

Voir `docs/production-runtime.md`.
