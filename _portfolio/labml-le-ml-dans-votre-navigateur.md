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
  avec SQL analytique dans le navigateur, et un terrain de jeu IA avec vision sur
  l'appareil et modèle de langue local.
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

Trois vagues ultérieures l'ont poussé au-delà de l'échelle démo. Les **colonnes de texte
libre** ne sont plus sautées : elles entrent dans le pipeline via un TF-IDF bilingue écrit
à la main, ajusté sur le seul split d'entraînement, et les explications parlent en mots -
sur le fichier démo d'avis clients, *fast* et *excellent* poussent la prédiction vers le
haut, *refund* la tire vers le bas. L'**échelle** a été mesurée avant d'être construite :
un fichier d'un million de lignes entraîne tout le zoo en environ 130 secondes, et
au-delà de 100 000 lignes utilisables un échantillon seedé et stratifié prend le relais -
annoncé sur le leaderboard, jamais silencieux, chaque modèle plafonné restant mesuré sur
le même jeu de test complet. Et une **courbe d'apprentissage** répond à la question
budgétaire classique - « est-ce que plus de données aideraient ce modèle ? » - en le
réentraînant sur des fractions seedées croissantes du split d'entraînement, avec bande de
confiance et verdict en clair : la courbe grimpe encore, ou elle a plafonné - travaillez
plutôt les variables.

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

Le studio embarque désormais un vrai moteur analytique : du **SQL dans le navigateur**,
via DuckDB compilé en WebAssembly - jointures, fonctions de fenêtrage, agrégations sur le
fichier que vous venez de déposer, plus tout CSV, **Parquet** ou JSON attaché dans la
même session, chacun exposé comme une vue nommée d'après le fichier. Le fichier est
interrogé tel que déposé, *avant* la recette de nettoyage, pour que chaque résultat reste
traçable vers un fichier qu'on peut rouvrir ; un résultat s'exporte en CSV ou passe au
ML Lab en un clic, et les erreurs SQL affichent le message de DuckDB lui-même, qui nomme
la ligne et le symbole fautifs. Aucun serveur : le moteur lui-même est auto-hébergé et
tourne dans l'onglet.

## Le terrain de jeu IA - `/ai`

Deux expériences d'IA sur l'appareil, mêmes règles de confidentialité :

- **Vision** : analyse d'images locale via ONNX Runtime Web (WebAssembly) - déposez une
  photo ou utilisez la webcam et trois réseaux auto-hébergés la lisent : un classificateur
  EfficientNet-Lite4 nomme le sujet principal (1 000 classes ImageNet, 77,6 % top-1),
  YOLOX-Nano dessine des boîtes autour des objets qu'il trouve (80 classes du quotidien)
  et UltraFace localise les visages - « 1 visage détecté », compté en clair. Le calcul
  des boîtes (décodage de grilles, IoU, suppression non maximale) est écrit à la main et
  testé, et l'interface dit toujours honnêtement ce que les modèles ne peuvent pas
  savoir : la détection dit où, pas qui.
- **Assistant de données** : posez des questions en français ou en anglais sur votre
  dataset chargé - moyennes, comptages sous condition, top N, corrélations. Un
  interpréteur local déterministe lit chaque question en premier : il ne peut nommer
  qu'une colonne qui existe et une valeur qui s'y trouve vraiment, et quand il ne
  comprend pas, il le dit au lieu de deviner. Sur consentement explicite, un **vrai
  modèle de langue** - Qwen3-0.6B, 355 Mo, Apache-2.0, auto-hébergé, exécuté localement
  sur WebGPU - prend le relais pour les formulations que l'interpréteur abandonne. Il ne
  calcule jamais : il traduit seulement la question vers une grammaire de requêtes
  fermée, le moteur déterministe produit chaque chiffre, et un badge sous chaque réponse
  nomme le moteur qui a fait la lecture. Mesuré sur six questions de référence sur
  titanic, le duo en réussit maintenant cinq - et le sixième échec est consigné au plan
  comme une limite d'un modèle de 0,6 milliard de paramètres, pas maquillé.

<figure style="margin: 2rem 0; text-align: center;">
  <img src="/assets/img/labml/v23-detection-fr.jpg" alt="Vision 2 de LabML sur un portrait d'équipage NASA : boîtes sarcelle étiquetées personne autour de cinq astronautes, boîtes cuivre pointillées sur leurs visages, comptes indiquant 6 objets détectés et 5 visages détectés, le top 5 ImageNet et deux notes d'honnêteté" width="552" height="965" loading="lazy" style="width: 100%; height: auto; border-radius: 12px;" />
  <figcaption style="font-size: 0.85rem; color: var(--faint); margin-top: 0.6rem;">Une photo d'équipage de la NASA, lue par trois réseaux dans le navigateur : une boîte par personne, une boîte pointillée par visage — « 6 objets · 5 visages détectés ». Le classificateur à étiquette unique peine sur une scène entière (« sewing machine » ?) et le panneau le dit : l'honnêteté plutôt que le théâtre, la détection dit où, pas qui.</figcaption>
</figure>

<figure style="margin: 2rem 0; text-align: center;">
  <img src="/assets/img/labml/ai-chat-fr.png" alt="Assistant de données de LabML répondant à des questions en langage courant sur titanic : comptage des lignes où sex = female et moyenne d'âge par classe, calculés par un interpréteur local déterministe" width="1280" height="950" loading="lazy" style="width: 100%; height: auto; border-radius: 12px;" />
  <figcaption style="font-size: 0.85rem; color: var(--faint); margin-top: 0.6rem;">« Combien de lignes où sex est female ? » — 314, comptées localement par l'interpréteur déterministe qui lit chaque question en premier ; un modèle de langue local peut être activé, sur consentement explicite, pour rattraper les formulations qu'il abandonne.</figcaption>
</figure>

## Sous le capot

La contrainte d'ingénierie qui a tout façonné : **si ça calcule, c'est écrit à la main et
c'est déterministe**. Gradient boosting, MLP, k-means++, ACP par itération de puissance,
Holt-Winters, isolation forest, PSI, valeurs de Shapley, intervalles bootstrap, courbes
PR/ROC et de calibration, décodage des boîtes de détection (grilles, IoU, suppression
non maximale) - tout est implémenté from scratch en TypeScript, seedé de bout en bout,
et testé unitairement contre des résultats connus. Tout ce qui est lourd tourne
dans des Web Workers derrière des protocoles de messages typés : l'interface ne bloque
jamais.

Certaines contraintes sont venues de l'hébergeur, pas des maths. La cible de déploiement
refuse tout fichier de plus de 25 Mio - alors le modèle de langue de 355 Mo est récupéré
au moment du déploiement et découpé en morceaux de 24 Mio que le navigateur recolle,
chaque morceau vérifié contre des tailles d'octets épinglées (un écart fait échouer le
build, jamais le visiteur), et DuckDB est épinglé à la dernière version dont le
WebAssembly passe encore sous la limite. Mesuré, et consigné au plan, pour que la
prochaine mise à niveau re-mesure au lieu de redécouvrir.

La barre de qualité est tenue en CI : 352 tests unitaires, 61 tests bout-en-bout
Playwright (dont un test PWA hors-ligne, un test webcam factice et des vérifications
d'accessibilité WCAG par axe-core), TypeScript strict et budgets Lighthouse - la page
`/ml` atteint ≈ 0,99 sur mobile en throttling réel grâce à des coquilles statiques
prérendues qui peignent avant l'arrivée du JavaScript.

Et la promesse de confidentialité est architecturale, pas déclarative : une
Content-Security-Policy stricte n'autorise aucun appel tiers, les liens de partage portent
les métriques dans le *fragment* d'URL (que les navigateurs n'envoient jamais aux
serveurs), et toute l'application - démos et modèles de vision compris - continue de
fonctionner câble réseau débranché. Une page
**[/privacy](https://app.dominicdapice.com/privacy)** dédiée va un cran plus loin et
tend au lecteur un protocole DevTools en quatre étapes pour tout vérifier sans croire un
mot de la promesse - et la politique qu'elle cite est épinglée à l'en-tête réellement
servi par un test unitaire : la page ne peut pas revendiquer une protection que le site
aurait abandonnée en silence.

**Essayez : [app.dominicdapice.com](https://app.dominicdapice.com)** - chargez la démo
titanic, entraînez, et faites défiler : le leaderboard, les intervalles, l'analyse par
segments et les outils de seuil racontent l'histoire honnête d'un modèle en une trentaine
de secondes.

**Code source : [github.com/dapiced/LabML](https://github.com/dapiced/LabML)**
