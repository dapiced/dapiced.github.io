---
layout: portfolio
title: "Titanic sur Kaggle - Quand une meilleure validation locale ne donne pas un meilleur score"
date: 2026-08-20 07:00:00 -0400
lang: fr
tags: [machine-learning, kaggle, data-science, validation, testing]
description: >-
  Une plongée solo dans la compétition Kaggle Titanic, poussée au-delà du notebook
  habituel : feature engineering encadré par des tests, validation groupée par ticket,
  quatre familles de modèles comparées - et un Gradient Boosting à 0.8440 en local mais
  0.75358 sur Kaggle. Pourquoi je me suis arrêté à un honnête 0.78947 plutôt que de
  courir après le leaderboard.
translation_url: /portfolio/titanic-kaggle-robust-submission/
translation_label: "🇬🇧 Read this article in English"
---

La compétition Titanic est le « hello world » de Kaggle - et c'est exactement pour ça que je l'ai choisie. Le problème de modélisation étant bien balisé, je pouvais me concentrer sur une question plus difficile, qui vous suit dans tout projet ML réel : **que faire quand la validation locale dit que vous progressez et que le leaderboard dit le contraire ?**

Mon score final et légitime est **0.78947** (330 prédictions correctes sur 418), obtenu sans jamais utiliser la survie connue d'un membre de la famille ou d'un compagnon de billet pour prédire le sort d'un passager. Le chiffre compte moins que le chemin - et que l'endroit où j'ai choisi de m'arrêter.

## Ce que j'ai construit

Le projet va au-delà d'un simple notebook : un parcours exploratoire, plus un ensemble de petits scripts Python testés.

- Exploration et nettoyage des données avec pandas ;
- Feature engineering autour du titre, de la famille, du billet et du tarif ;
- Comparaison de régression logistique, Random Forest, Gradient Boosting et CatBoost ;
- Validation croisée stratifiée d'abord, puis **validation groupée par ticket** pour que les membres d'un même groupe de voyage ne soient jamais répartis entre les plis ;
- Blends, ajustement de seuil et analyse des « flips » qui aligne chaque soumission sur `PassengerId` pour voir exactement quels passagers chaque changement affecte ;
- **Tests unitaires** qui verrouillent le schéma des features et prouvent que les features dites « sûres » n'ont aucune dépendance directe à la cible `Survived`.

## Le constat : 0.8440 en OOF, 0.75358 sur Kaggle

Le résultat le plus intéressant du projet est une divergence. Mon meilleur Gradient Boosting atteignait **0.8440 en out-of-fold** - le meilleur score local de toute la série - puis **0.75358 sur Kaggle**, le *pire* de mes expériences décisives. Choisir le modèle uniquement sur l'OOF m'aurait mené exactement dans la mauvaise direction.

| Approche | Accuracy OOF | Score Kaggle | Flips vs référence |
| --- | ---: | ---: | ---: |
| Features enrichies + logistique | 0.8238 / 0.8249 groupée | 0.75837 | 37 |
| Gradient Boosting + features enrichies | **0.8440** | 0.75358 | 39 |
| Blend logistique/RF/GB, seuil OOF groupé | 0.8384 groupée | 0.76315 | 27 |
| Méta-stack prudent, seuil 0.5 | 0.8305 | 0.78468 | 2 |
| Référence group-corrected | - | **0.78947** | 0 |

Trois limites expliquent l'écart :

1. **Le test public est minuscule.** Une prédiction retournée déplace le score d'environ `0.002392` - une différence de `k` prédictions borne le nouveau score à `± k/418` de l'ancien.
2. **La pression de sélection amplifie le bruit.** Comparer beaucoup de variantes et retenir les meilleurs résultats OOF est un bon moyen de sélectionner du bruit propre aux plis plutôt que du signal.
3. **Les plis ne reproduisent pas le test.** Même groupés par ticket, les plis de validation croisée ne reproduisent ni la composition des 418 passagers de Kaggle ni toutes leurs corrélations familiales.

## La limite que je me suis fixée

Des astuces bien connues sur Titanic utilisent la *survie connue* d'un proche ou d'un compagnon de billet pour prédire le sort d'un passager. Même avec du cross-fitting soigné, ces règles exploitent les cibles de lignes apparentées - une forme de fuite que je ne voulais pas dans la solution présentée. J'ai gardé les variables relationnelles calculées **sans la cible** - taille de famille, fréquence du nom, préfixe du ticket, taille du groupe de billet - et écarté le reste.

## Une conclusion reproductible

Le livrable n'est pas seulement un score, c'est un score vérifiable : un fichier de soumission canonique, une copie figée identique à l'octet près avec son **SHA-256 consigné**, un script qui compare deux soumissions passager par passager, et une suite de tests (`unittest`) qui garde les contrats des features. Chaque expérience qui a pesé sur la décision finale est résumée avec ses chiffres dans le `EXPERIMENTS.md` du dépôt.

## Ce que j'en retiens

**Un code correct, une validation locale convaincante et une vraie généralisation sont trois choses différentes.** Les tests unitaires protègent la première, les comparaisons OOF éclairent la deuxième, et rien d'autre que des données réellement mises de côté ne garantit la troisième.

**Un petit leaderboard public est une mesure bruitée, pas une cible.** Après des échecs cohérents en logistique, boosting, blending et stacking, j'ai cessé de traiter l'OOF comme une promesse de score pour l'utiliser comme outil de diagnostic.

**Savoir s'arrêter fait partie de la méthode.** J'ai arrêté les soumissions à 0.78947. Je rouvrirais le projet à deux conditions : une évaluation indépendante qui n'a joué aucun rôle dans le développement, et une hypothèse sans fuite montrant un gain stable. Sans cela, conserver le résultat actuel *est* la conclusion la plus solide.

## Projet Github titanic complet

[Titanic](https://github.com/dapiced/titanic)
