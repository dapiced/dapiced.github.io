# Cartes de partage (Open Graph)

Une carte 1200×630 par billet et par entrée du portfolio, pour que LinkedIn, Bluesky ou
Slack affichent un aperçu lisible : série et date, titre, auteur, et la photo de
l'article à droite quand il en a une.

```bash
python tools/og-cards/og_cards.py          # génère les cartes manquantes ou périmées
python tools/og-cards/og_cards.py --check  # échoue si une carte manque ou est périmée
```

Les cartes sont versionnées dans `assets/img/og/` avec un `manifest.json` (empreinte des
entrées). La CI (`tests/test_og_cards.py`) vérifie seulement l'empreinte, pas les pixels :
le résultat ne dépend donc pas de la version de Pillow installée sur le runner.
`_plugins/og_cards.rb` fait pointer `og:image` et `twitter:image` vers la carte.

## Règles

| Cas | Résultat |
|---|---|
| Pas d'`image:` | carte sans photo |
| `image:` en JPEG ou WebP | photo recadrée à droite |
| `image:` en PNG (capture, schéma) | carte sans photo : une capture recadrée en bande devient illisible |
| `image:` déjà au format 1200×630 | conservée telle quelle (Prophet, Long Dash, Tree) |
| `og_card: false` | aucune carte |

Front matter optionnel :

- `og_photo_focus: 0.15` : partie de la photo gardée (0 = bord gauche, 1 = bord droit).
- `og_accent: vincenzo` : accent doré. Comme dans le CSS, l'or est réservé à Vincenzo ;
  un test le vérifie.

Après une modification du titre, de la date ou de la photo d'un article, relancer la
commande et committer les fichiers de `assets/img/og/`.
