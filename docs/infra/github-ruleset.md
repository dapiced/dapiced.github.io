# Règle de branche sur `main`

`main` est ce que GitHub Pages publie. La règle ci-dessous empêche d'y arriver
autrement que par une pull request dont les vérifications sont vertes. Elle
aurait arrêté l'incident de la PR #124 (une mise à jour Dependabot fusionnée
alors que la CI était rouge).

Le fichier importable est [`ruleset-main.json`](ruleset-main.json).

## Ce que la règle impose

| Règle | Effet |
|---|---|
| Pull request obligatoire | Plus de push direct sur `main`. Aucune approbation exigée : tu es seul mainteneur. |
| Vérifications requises | `Jekyll build`, `Cosmic Daily tests` et `Secret scan` (job du workflow CI) doivent être vertes. |
| Pas de suppression, pas de force-push | L'historique de `main` ne peut pas être réécrit. |
| Contournement | Réservé au rôle Admin, et seulement au moment de fusionner une PR (case « bypass » à cocher volontairement). Une soupape pour une urgence, pas une habitude. |

`Deploy preview` n'est **pas** requis : une panne de Cloudflare ne doit pas
bloquer une correction du site. CodeQL n'est pas requis non plus pour l'instant :
il ne s'exécute pas sur les PR ouvertes par les automatisations.

## Les automatisations restent compatibles

- **Cosmic Daily** lance lui-même la CI sur sa PR puis la fusionne : les trois
  vérifications sont présentes au moment de la fusion.
- **Repo data** lance aussi la CI sur sa PR (`repo-data.yml`, dernière étape).
- **Dependabot** déclenche la CI normalement sur ses PR.

### Approbation des changements non attribués

GitHub ajoute à la règle « Pull request » un paramètre
`require_extra_approval_for_unattributed_changes`, activé par défaut quand le
fichier importé ne le mentionne pas. Il exige alors l'approbation d'une
personne sur toute PR dont les commits viennent d'un robot
(`github-actions[bot]`). C'est ce qui a bloqué la fusion automatique de
Cosmic Daily le 14 octobre 2026 (PR #137), alors que les trois vérifications
étaient vertes. Le fichier le met maintenant explicitement à `false`, et
`tests/test_ruleset.py` le vérifie.

Pour corriger une règle déjà importée : supprimer le ruleset
`main: green checks before merge` puis réimporter `ruleset-main.json`
(étapes ci-dessous). Vérification :
`curl -s https://api.github.com/repos/dapiced/dapiced.github.io/rules/branches/main`
doit afficher `"require_extra_approval_for_unattributed_changes": false`.

## Activer la règle (2 minutes, une fois)

1. GitHub → dépôt → **Settings** → **Rules** → **Rulesets**.
2. **New ruleset** → **Import a ruleset** → choisir `docs/infra/ruleset-main.json`
   (à télécharger depuis le dépôt).
3. Vérifier l'aperçu : cible `Default branch`, **Enforcement status : Active**.
4. **Create**.

## Vérifier

Ouvrir une PR quelconque : le bouton **Merge** reste gris tant que les trois
vérifications ne sont pas vertes, avec la mention « Required ».
