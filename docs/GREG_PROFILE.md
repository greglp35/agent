# Profil `/greg`

Le profil `/greg` est un raccourci personnel qui applique automatiquement des préférences COMMAND OS sans transformer chaque besoin en macro géante.

## Utilisation

```text
/greg /audit mon application
```

équivaut conceptuellement à activer `--profile=greg`, puis à appliquer les règles adaptées à `/audit`.

Autres exemples :

```text
/greg /decision faut-il migrer ?
/greg /debug mon import Excel
/greg /architect mon application
/greg /council /decision mon choix
```

Les options explicites restent prioritaires :

```text
/greg /audit mon projet --fast
```

reste en mode FAST, même si le profil préfère DEEP pour `/audit`.

## Comportement par défaut

- français ;
- réponse professionnelle, compacte et exploitable ;
- contradiction constructive plutôt qu'approbation automatique ;
- priorité aux faits, preuves, risques, contraintes et actions ;
- clarification uniquement si réellement bloquante ;
- vérité d'exécution stricte ;
- `actions`, `no-fluff` et `confidence` activés par défaut.

Le profil n'active pas systématiquement tous les experts ou toutes les méthodes. Il applique des règles selon la commande : décision, audit, architecture, debug, risque, stratégie, etc.

## Forme canonique

Ces deux formes sont équivalentes :

```text
/greg /decision mon choix
--profile=greg /decision mon choix
```

Le profil est une couche de préférences. Il ne remplace ni les commandes, ni les méthodes, ni les Policy Packs de sécurité.
