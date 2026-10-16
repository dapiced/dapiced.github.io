# Nouveau billet

Crée un billet, ou une paire EN/FR, prêt à rédiger. L'outil s'occupe de la partie
mécanique, celle qui casse en silence :

| Piège | Ce que fait l'outil |
|---|---|
| Deux fichiers qui doivent pointer l'un vers l'autre | `lang`, `translation_url` et `translation_label` écrits des deux côtés |
| Date dans le futur : Jekyll saute le billet sans prévenir (billets Prophet, septembre 2026) | Date à l'heure de Montréal, quelques minutes dans le passé ; `--date` refuse une date future |
| Tags inventés au fil de l'eau | Seuls les tags déjà utilisés sont acceptés, sauf `--new-tag` |
| Slug déjà pris | Refus avec le nom du billet en conflit |
| Texte provisoire publié par erreur | Le billet démarre avec `published: false`, et la CI refuse un billet publié qui contient encore `✍️ TODO` |

```bash
# Paire bilingue
python tools/new-post/new_post.py \
  --title-en "What I learned about XGBoost" \
  --title-fr "Ce que j'ai appris sur XGBoost" \
  --tags machine-learning,kaggle

# Une seule langue, aperçu sans rien écrire
python tools/new-post/new_post.py --title-fr "Notes de terrain" --tags meta --dry-run
```

Options utiles : `--description-en` / `--description-fr` (160 caractères au plus),
`--image /assets/img/…/cover.jpg`, `--slug-fr` pour choisir l'URL, `--date "2026-10-16 20:00"`,
`--ready` pour ne pas ajouter `published: false`.

## L'encadré « En bref »

Chaque billet commence par trois puces :

```markdown
> **En bref**
> - Premier point à retenir.
> - Deuxième point.
> - Troisième point.
{: .in-brief }
```

Elles résument le billet pour le lecteur pressé et servent telles quelles de post
LinkedIn. Le style (`.in-brief` dans `assets/css/style.css`) suit les thèmes Nuit et Aube.

## Publier

1. Remplacer chaque `✍️ TODO`.
2. Supprimer la ligne `published: false` dans les deux fichiers.
3. Si la publication a lieu un autre jour, ajuster `date:` **et** le nom des fichiers,
   puis `translation_url` si le mois a changé (le test de réciprocité le signale).
4. `python tools/og-cards/og_cards.py`, puis committer les cartes de `assets/img/og/`.

`tests/test_posts.py` vérifie les traductions dans les deux sens, l'absence de date future
et de texte provisoire dans les billets publiés.
