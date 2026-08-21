---
layout: portfolio
title: "LabML - Le ML dans votre navigateur : un laboratoire complet, sans backend"
date: 2026-08-21 01:00:00 -0400
lang: fr
tags: [machine-learning, typescript, privacy, web-workers, react, pwa]
description: >-
  LabML est une plateforme ML tabulaire complète - qualité des données, entraînement,
  évaluation, explication, réutilisation de modèles - qui tourne entièrement dans le
  navigateur : algorithmes écrits à la main et seedés dans des Web Workers, sans backend,
  sans compte, sans upload. En ligne sur app.dominicdapice.com : un ML Lab, un Data Studio
  et un terrain de jeu IA.
translation_url: /portfolio/labml-ml-in-your-browser/
translation_label: "🇬🇧 Read this article in English"
image: /assets/img/labml/v20-uncertainty-fr.png
---

La plupart des démos « du ML dans le navigateur » sont une interface mince devant une API :
votre CSV part quelque part, un serveur fait le travail, et vous faites confiance à ce qui
revient. **LabML** fait le pari inverse : une plateforme de machine learning *complète* -
audit des données, entraînement, évaluation, explication, réutilisation de modèles - où
**chaque calcul s'exécute sur votre propre machine**. Pas de backend, pas de compte, pas
d'upload. Ouvrez l'onglet Réseau pendant qu'elle entraîne huit modèles : rien ne sort.

Elle est en ligne sur **[app.dominicdapice.com](https://app.dominicdapice.com)**,
installable en PWA hors-ligne, bilingue (FR/EN), et organisée en trois sections.

## Le ML Lab - `/ml`

La boucle centrale : déposez un CSV (ou un fichier Excel, ou choisissez une démo comme
titanic), désignez la colonne à prédire, et le labo profile chaque colonne, détecte la
tâche (binaire, multi-classes, régression), écarte identifiants et constantes, signale les
**fuites de cible**, puis entraîne un zoo de modèles dans un Web Worker : baseline naïve,
régression linéaire/logistique, k-NN, Naive Bayes gaussien, arbre de décision, forêt
aléatoire - plus un **gradient boosting histogramme écrit à la main** (bins de quantiles
façon LightGBM, gains du second ordre, feuilles de Newton) et un **MLP maison** (init He
seedée, Adam full-batch).

<figure style="margin: 2rem 0; text-align: center;">
  <img src="/assets/img/labml/ml-import-fr.png" alt="Écran d'entrée du ML Lab de LabML : zone de glisser-déposer pour fichiers CSV ou Excel, lus localement sans téléversement, à côté de cinq jeux de démonstration en un clic" width="1280" height="860" loading="lazy" style="width: 100%; height: auto; border-radius: 12px;" />
  <figcaption style="font-size: 0.85rem; color: var(--faint); margin-top: 0.6rem;">Zéro friction à l'entrée : déposez un CSV ou un fichier Excel — lu directement dans le navigateur, rien n'est téléversé — ou lancez un jeu de démonstration en un clic.</figcaption>
</figure>

Le leaderboard n'est que le début. Ce que je voulais vraiment construire, c'est la partie
que les démos sautent : *l'évaluation honnête*.

<figure style="margin: 2rem 0; text-align: center;">
  <img src="/assets/img/labml/ml-leaderboard-fr.png" alt="Leaderboard de LabML sur titanic : huit modèles classés par accuracy avec l'écart vs la baseline naïve, F1, ROC-AUC, log-loss, temps d'entraînement et latence d'inférence p50" width="1054" height="366" loading="lazy" style="width: 100%; height: auto; border-radius: 12px;" />
  <figcaption style="font-size: 0.85rem; color: var(--faint); margin-top: 0.6rem;">Trente secondes après le chargement de titanic : huit modèles classés contre la baseline naïve, avec temps d'entraînement et latence d'inférence p50 pour chacun — l'observabilité de run incluse.</figcaption>
</figure>

<figure style="margin: 2rem 0; text-align: center;">
  <img src="/assets/img/labml/v20-uncertainty-fr.png" alt="Panneau d'incertitude de LabML : intervalles à 95 % en points-moustaches pour l'accuracy de chaque modèle, avec un verdict apparié indiquant que le gagnant bat la baseline dans 100 % des rééchantillonnages" width="1054" height="407" loading="lazy" style="width: 100%; height: auto; border-radius: 12px;" />
  <figcaption style="font-size: 0.85rem; color: var(--faint); margin-top: 0.6rem;">« 0,967 sur 30 lignes de test n'est pas 0,967. » Chaque métrique porte son intervalle bootstrap à 95 %, et l'écart gagnant-baseline reçoit un verdict apparié en clair.</figcaption>
</figure>

- Chaque run est mesuré contre une **baseline naïve** sur un jeu de test mis de côté
  (split seedé et stratifié - le même seed reproduit exactement le même run).
- Chaque métrique du leaderboard porte un **intervalle bootstrap à 95 %** (1 000
  rééchantillonnages seedés, partagés entre modèles pour des comparaisons appariées),
  avec un verdict qui dit si l'avance du gagnant est « probablement réelle » ou
  « peut-être du bruit ».
- Une **analyse par segments** répond à « où mon modèle échoue-t-il ? » en re-mesurant le
  jeu de test sur chaque tranche catégorielle - y compris les colonnes *exclues* de
  l'entraînement, là où se cachent les effets de proxy. Sur titanic, elle pointe
  directement le pont C et les passagers de Cherbourg.
- Sur données déséquilibrées, **courbe précision-rappel, courbe de calibration et seuil
  de décision chiffré par une matrice de coûts** montrent ce que l'accuracy cache - une
  probabilité n'est pas une décision ; le seuil appartient à vos coûts.

<figure style="margin: 2rem 0; text-align: center;">
  <img src="/assets/img/labml/v18-segments-fr.png" alt="Analyse par segments de LabML sur titanic : accuracy recalculée par pont, port d'embarquement, classe et sexe, pires écarts d'abord, avec la colonne alive découpée bien qu'exclue des variables" width="1054" height="643" loading="lazy" style="width: 100%; height: auto; border-radius: 12px;" />
  <figcaption style="font-size: 0.85rem; color: var(--faint); margin-top: 0.6rem;">« Où le modèle échoue » - le jeu de test découpé par chaque colonne catégorielle, pires écarts d'abord. Un écart est une piste à creuser, pas un verdict.</figcaption>
</figure>

Les outils de compréhension complètent le tableau : importance par permutation, dépendance
partielle, prédictions what-if en direct avec **explications de Shapley exactes** (les
barres somment à prédiction moins baseline), et une lecture en langage clair générée par
règles - aucun LLM.

<figure style="margin: 2rem 0; text-align: center;">
  <img src="/assets/img/labml/ml-insights-fr.png" alt="Graphiques d'insight de LabML pour le meilleur modèle : matrice de confusion interactive, courbe ROC avec AUC, importance par permutation et dépendance partielle" width="1054" height="646" loading="lazy" style="width: 100%; height: auto; border-radius: 12px;" />
  <figcaption style="font-size: 0.85rem; color: var(--faint); margin-top: 0.6rem;">Comprendre le gagnant : matrice de confusion, courbe ROC, importance par permutation, dépendance partielle — chaque graphique calculé from scratch dans le navigateur.</figcaption>
</figure>

Le labo ferme aussi les boucles d'un vrai workflow : **scorer un nouveau lot** avec une
comparaison honnête test vs lot, **comparer deux runs côte à côte** (« mon nettoyage
a-t-il servi ? » - avec verdicts d'incertitude croisés), **recherche d'hyperparamètres**
par random search seedée en validation croisée propre, et **exporter un modèle en JSON
puis le réimporter plus tard** - LabML reconstruit le prédicteur exact (prédictions
identiques à l'octet près) et score n'importe quel CSV sans réentraîner. Pas de colonne
cible ? Un **mode exploration** k-means + ACP seedé décrit les groupes qu'il trouve ; une
colonne de dates déverrouille des **prévisions Holt-Winters** validées par backtest à
origine glissante. Les runs persistent localement (IndexedDB) avec tous leurs artefacts,
et un dataset peut être conservé sur consentement, sous un budget explicite de 50 Mo.

## Le Data Studio - `/data`

Les vrais jeux de données sont sales, alors le labo a son atelier de réparation. Le Data
Studio audite un fichier sans l'uploader - cellules manquantes, doublons, variantes de
casse et d'espaces, valeurs aberrantes (clôtures de Tukey), colonnes constantes ou
identifiantes, le tout résumé en un score déterministe sur 100 - et le répare via une
**recette de nettoyage rejouable** : trim, fusion de variantes, dédoublonnage, imputation,
écrêtage, types forcés, dérivation de dates, et suppression des anomalies multivariées
détectées par un **isolation forest maison seedé**. La recette s'exporte en JSON et se
rejoue sur le fichier du mois prochain.

<figure style="margin: 2rem 0; text-align: center;">
  <img src="/assets/img/labml/data-studio-fr.png" alt="Data Studio de LabML sur le fichier démo sale : score de qualité passant de 48 à 92 sur 100 après la recette de nettoyage, avec un panneau de jointure pour enrichir le dataset depuis un second fichier" width="1280" height="900" loading="lazy" style="width: 100%; height: auto; border-radius: 12px;" />
  <figcaption style="font-size: 0.85rem; color: var(--faint); margin-top: 0.6rem;">Le fichier démo sale passe de 48/100 à 92/100 via la recette rejouable — et un second fichier est à un clic d'une jointure gauche sur clé commune.</figcaption>
</figure>

Il couvre aussi les deux gestes quotidiens que la plupart des outils sautent : la
**jointure gauche d'un second fichier** sur une clé commune (taux de correspondance,
doublons et orphelines sont *nommés*, jamais silencieux) et un **contrôle de dérive** qui
compare un nouveau lot à la référence - diff de schéma, PSI par colonne, catégories
nouvelles et disparues, verdict de sévérité. Un clic passe le résultat nettoyé au ML Lab.

## Le terrain de jeu IA - `/ai`

Deux expériences d'IA sur l'appareil, mêmes règles de confidentialité :

- **Vision** : classification d'images locale via ONNX Runtime Web (WebAssembly) -
  déposez une photo ou utilisez la webcam ; le modèle (SqueezeNet, auto-hébergé) répond
  avec ses 1 000 classes ImageNet et l'interface dit honnêtement ce qu'il ne sait pas.
- **Assistant de données** : posez des questions en français ou en anglais sur votre
  dataset chargé - moyennes, comptages sous condition, top N, corrélations - via un
  interpréteur local déterministe, clairement étiqueté comme n'étant *pas* un modèle de
  langue. Quand il ne comprend pas, il le dit au lieu de deviner.

<figure style="margin: 2rem 0; text-align: center;">
  <img src="/assets/img/labml/ai-vision-fr.png" alt="Page Vision de LabML : un chat dessiné classifié localement par SqueezeNet, avec le top 5 des prédictions et une note honnête indiquant que le modèle ImageNet de 2012 ne connaît ni visages ni documents" width="1280" height="900" loading="lazy" style="width: 100%; height: auto; border-radius: 12px;" />
  <figcaption style="font-size: 0.85rem; color: var(--faint); margin-top: 0.6rem;">SqueezeNet, en WebAssembly, fait de son mieux sur un chat dessiné à la main — et le panneau dit clairement ce qu'un modèle 2012 à 1 000 classes peut et ne peut pas savoir. L'honnêteté plutôt que le théâtre.</figcaption>
</figure>

<figure style="margin: 2rem 0; text-align: center;">
  <img src="/assets/img/labml/ai-chat-fr.png" alt="Assistant de données de LabML répondant à des questions en langage courant sur titanic : comptage des lignes où sex = female et moyenne d'âge par classe, calculés par un interpréteur local déterministe" width="1280" height="950" loading="lazy" style="width: 100%; height: auto; border-radius: 12px;" />
  <figcaption style="font-size: 0.85rem; color: var(--faint); margin-top: 0.6rem;">« Combien de lignes où sex est female ? » — 314, comptées localement par un interpréteur déterministe, honnêtement étiqueté comme n'étant pas un modèle de langue.</figcaption>
</figure>

## Sous le capot

La contrainte d'ingénierie qui a tout façonné : **si ça calcule, c'est écrit à la main et
c'est déterministe**. Gradient boosting, MLP, k-means++, ACP par itération de puissance,
Holt-Winters, isolation forest, PSI, valeurs de Shapley, intervalles bootstrap, courbes
PR/ROC et de calibration - tout est implémenté from scratch en TypeScript, seedé de bout
en bout, et testé unitairement contre des résultats connus. Tout ce qui est lourd tourne
dans des Web Workers derrière des protocoles de messages typés : l'interface ne bloque
jamais.

La barre de qualité est tenue en CI : 237 tests unitaires, 49 tests bout-en-bout
Playwright (dont un test PWA hors-ligne, un test webcam factice et des vérifications
d'accessibilité WCAG par axe-core), TypeScript strict et budgets Lighthouse - la page
`/ml` atteint ≈ 0,99 sur mobile en throttling réel grâce à des coquilles statiques
prérendues qui peignent avant l'arrivée du JavaScript.

Et la promesse de confidentialité est architecturale, pas déclarative : une
Content-Security-Policy stricte n'autorise aucun appel tiers, les liens de partage portent
les métriques dans le *fragment* d'URL (que les navigateurs n'envoient jamais aux
serveurs), et toute l'application - démos et modèle de vision compris - continue de
fonctionner câble réseau débranché.

**Essayez : [app.dominicdapice.com](https://app.dominicdapice.com)** - chargez la démo
titanic, entraînez, et faites défiler : le leaderboard, les intervalles, l'analyse par
segments et les outils de seuil racontent l'histoire honnête d'un modèle en une trentaine
de secondes.
