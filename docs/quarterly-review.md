# Revue trimestrielle

Le premier jour de chaque trimestre (janvier, avril, juillet, octobre, 13 h 23 UTC),
`.github/workflows/quarterly-review.yml` ouvre une issue « Quarterly review AAAA-Qn »
qui fait le point sur le trimestre écoulé. Une seule issue par trimestre, même si on
relance le workflow.

| Section | Source | Ce qu'on y lit |
|---|---|---|
| Contenu | `_posts/`, `_apod/` | Billets publiés par langue, face à la cible de deux par mois ; images du jour ; billets EN encore sans version française |
| Qualité | API GitHub (jeton du workflow) | Exécutions planifiées de la santé de la production, des liens externes et de Cosmic Daily : réussites et échecs |
| Audience | API GoatCounter (facultatif) | Visiteurs, part venue de LinkedIn (cible du plan : 35 %), pages les plus lues, principales sources |
| Search Console | lien | Case à cocher : pas d'API branchée, pour éviter un compte de service Google |
| À remplir | vous | Ce qui a marché, quoi arrêter, prochain sujet |

Une source absente devient une ligne qui le dit, jamais un échec.

## Activer la section Audience (facultatif, 2 minutes)

Sans jeton, la revue fonctionne et saute cette section.

1. GoatCounter → menu de votre nom d'utilisateur → **API** → nouvelle clé, avec la
   seule permission de **lecture des statistiques**.
2. GitHub → dépôt → **Settings** → **Secrets and variables** → **Actions** →
   **New repository secret** : nom `GOATCOUNTER_API_TOKEN`, valeur la clé.

La clé ne passe ni par le dépôt ni par une conversation : elle va directement de
GoatCounter aux secrets GitHub. Elle ne permet que de lire des statistiques agrégées.

## Lancer à la main

Actions → **Quarterly review** → **Run workflow**, avec un trimestre (`2026-Q4`) ou vide
pour le trimestre qui vient de se terminer. En local :

```bash
GITHUB_REPOSITORY=dapiced/dapiced.github.io python tools/site-checks/quarterly_review.py --quarter 2026-Q3
```
