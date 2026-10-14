# Règle de branche sur `main`

`main` est ce que GitHub Pages publie. La règle ci-dessous empêche d'y arriver
autrement que par une pull request, et protège son historique.

Le fichier importable est [`ruleset-main.json`](ruleset-main.json).

## Ce que la règle impose

| Règle | Effet |
|---|---|
| Pull request obligatoire | Plus de push direct sur `main`. Aucune approbation exigée : tu es seul mainteneur. |
| Pas de suppression, pas de force-push | L'historique de `main` ne peut pas être réécrit. |
| Contournement | Réservé au rôle Admin, et seulement au moment de fusionner une PR (case « bypass » à cocher volontairement). |

## Pourquoi aucune vérification n'est requise

La première version exigeait `Jekyll build`, `Cosmic Daily tests` et
`Secret scan`. Elle a bloqué la fusion automatique de Cosmic Daily le
14 octobre 2026 (PR #137) :

- une PR ouverte avec le `GITHUB_TOKEN` ne déclenche pas la CI. Cosmic Daily
  la lance donc par `workflow_dispatch` ;
- ces vérifications passent au vert sur le bon commit, mais GitHub ne les
  rattache pas à la PR : le bouton de fusion affiche « Waiting for status to
  be reported » indéfiniment ;
- GitHub refuse l'application GitHub Actions comme acteur de contournement
  (« contains an invalid actor »).

Choix retenu : pas de vérifications requises. Cosmic Daily garde son propre
contrôle, puisqu'il attend sa CI (`gh run watch --exit-status`) et s'arrête
avant la fusion si elle est rouge.

Risque accepté : une PR humaine ou Dependabot peut être fusionnée alors que sa
CI est rouge (incident de la PR #124). Avant de fusionner, vérifier que les
coches sont vertes. Si ce risque devient gênant, la solution durable est une
application GitHub dédiée : ses PR déclenchent la vraie CI, les vérifications
s'attachent à la PR, et on peut de nouveau les exiger.

## Approbation des changements non attribués

GitHub ajoute à la règle « Pull request » un paramètre
`require_extra_approval_for_unattributed_changes`, activé par défaut quand le
fichier importé ne le mentionne pas. Il exige alors l'approbation d'une
personne sur toute PR dont les commits viennent d'un robot
(`github-actions[bot]`), ce qui bloquerait aussi Cosmic Daily. Le fichier le
met explicitement à `false`, et `tests/test_ruleset.py` le vérifie.

## Activer la règle (2 minutes)

1. GitHub → dépôt → **Settings** → **Rules** → **Rulesets**.
2. Supprimer l'ancien ruleset s'il existe.
3. **New ruleset** → **Import a ruleset** → choisir `docs/infra/ruleset-main.json`
   (à télécharger depuis le dépôt).
4. Vérifier l'aperçu : cible `Default branch`, **Enforcement status : Active**.
5. **Create**.

## Vérifier

`curl -s https://api.github.com/repos/dapiced/dapiced.github.io/rules/branches/main`
doit lister `deletion`, `non_fast_forward` et `pull_request`, avec
`"require_extra_approval_for_unattributed_changes": false`.
