# COMMAND OS Alpha.4 — Host Adapters

COMMAND OS ne dépend d'aucun fournisseur de modèle. Le runtime alpha.4 définit deux contrats simples.

## LLMAdapter

Un hôte implémente :

```python
class MyHost:
    name = "my-host"
    thread_safe = False

    def complete(self, request: LLMRequest) -> LLMResponse:
        ...
```

`LLMRequest` contient :

- `purpose` : exécution de commande, avis de conseil, arbitrage ;
- `system` : règles COMMAND OS ;
- `user` : charge utile structurée ;
- `metadata` : commande, profondeur, expert ;
- `response_contract` : champs attendus.

La réponse normalisée contient un dictionnaire `content`.

## ToolAdapter

Un outil externe expose une capacité explicite :

```python
class WebSearchAdapter:
    capability = "web.search"

    def invoke(self, arguments):
        return {"results": [...]}
```

L'outil est invoqué **hors du modèle** puis son résultat est injecté comme `tool_context`.
Cela évite qu'un modèle puisse prétendre avoir appelé un outil qui n'a pas été exécuté.

## Council

`/council` suit trois invariants :

1. avis experts indépendants ;
2. aucun expert ne voit les réponses des autres pendant sa première analyse ;
3. un arbitrage distinct reçoit ensuite tous les avis et expose les désaccords.

Le mode parallèle n'est activé que si l'adapter déclare `thread_safe = True`.

## Continuité

`/next`, `/continue`, `/fix`, `/deeper`, `/redo`, `/focus`, `/final` peuvent être résolus à partir d'un état :

```json
{
  "active_project": "command-os",
  "current_task": "semantic runtime",
  "current_stage": "alpha.4",
  "last_artifact": "runtime/semantic.py",
  "next_action": "run integration tests"
}
```

## Frontière de sécurité

Les adapters restent responsables des politiques de l'hôte. COMMAND OS ne contourne jamais :

- confirmations nécessaires ;
- permissions ;
- politiques sécurité ;
- restrictions d'écriture ;
- disponibilité réelle des outils.
