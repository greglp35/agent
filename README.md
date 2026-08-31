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

Version actuelle : `2.0.0-beta.1`

Le projet est désormais doté d’un parser/runtime, d’un routeur d’experts, d’un Capability Resolver et d’un contrat d’exécution explicite.

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

### Limite volontaire

Le runtime alpha.2 **compile et planifie** les commandes. Il ne branche pas encore
les outils réels (web, fichiers, GitHub, déploiement, etc.). Cela vient dans le
sprint suivant : `Execution Engine + Capability Resolver`.

## Alpha.3 — Execution Contract & Capability Resolver

Cette version ajoute :
- manifeste de capacités ;
- séparation intention/capacité ;
- `run_command()` ;
- adapters d’exécution plug-in ;
- statuts d’exécution explicites ;
- état de travail JSON ;
- trace JSONL ;
- Quality Gate structurel ;
- nouveaux tests runtime.

Le runtime alpha.3 ne prétend jamais avoir exécuté un outil non branché.

## Alpha.4 — Host Adapters + Semantic Runtime

Alpha.4 transforme le runtime de planification en moteur sémantique **host-neutral** :

- contrat `LLMAdapter` indépendant du fournisseur ;
- contrat `ToolAdapter` pour capacités externes réelles ;
- `run_semantic()` et `SemanticRuntime` ;
- injection structurée des Expert Packs dans chaque étape ;
- chaînage des sorties entre commandes ;
- `/council` avec avis indépendants, désaccords et arbitrage séparé ;
- parallélisation du conseil uniquement pour les hosts déclarés thread-safe ;
- exécution explicite de `web.search` via adapter avant injection au modèle ;
- résolution state-aware de `/next`, `/continue`, `/fix`, `/deeper`, `/redo`, `/focus`, `/final` ;
- Quality Gates sémantiques ;
- adapter déterministe et adapter callable pour intégration/test ;
- suite de tests portée au-delà de 100 contrôles exécutables.

Voir `docs/HOST_ADAPTERS.md` et `examples/semantic-demo.py`.

## Alpha.5 — Production Host Integrations

- adapters concrets OpenAI Responses et Anthropic Messages ;
- wrapper de résilience : retries, circuit breaker, budgets et journal ;
- approval gates pour effets externes ;
- Tool Adapters gardés et `tool_requests` explicites ;
- redaction des secrets ;
- `--tool=<capability>` ;
- Evaluation Harness et corpus de régression.

Aucune clé API n'est stockée dans le repo. Les adapters lisent les variables d'environnement ou reçoivent la clé explicitement au runtime.

## Beta.1 — API Service + Policy Packs

Beta.1 expose COMMAND OS comme service HTTP et ajoute : RBAC deny-by-default, approval gates avec séparation des tâches, policy packs, registry fournisseurs sans modèle figé, observabilité Prometheus, baseline cross-provider et packaging CLI/API. Voir `docs/BETA1_SERVICE.md`.
