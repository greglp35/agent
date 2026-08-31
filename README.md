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

Version actuelle : `2.0.0-alpha.3`

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
