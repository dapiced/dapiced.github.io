---
layout: portfolio
title: "LabML - ML in Your Browser: a Complete Machine Learning Lab With No Backend"
date: 2026-08-21 01:00:00 -0400
lang: en
tags: [machine-learning, typescript, privacy, web-workers, react, pwa]
description: >-
  LabML is a full tabular ML platform - data quality, training, evaluation, explanation,
  model reuse - that runs entirely in the browser: hand-written, seeded algorithms in Web
  Workers, no backend, no accounts, no uploads. Live at app.dominicdapice.com, with an ML
  Lab, a Data Studio and an AI playground.
translation_url: /portfolio/labml-le-ml-dans-votre-navigateur/
translation_label: "🇫🇷 Lire cet article en français"
image: /assets/img/labml/v20-uncertainty-en.png
---

Most "try ML in your browser" demos are a thin UI over an API: your CSV is uploaded
somewhere, a server does the work, and you trust whatever comes back. **LabML** is the
opposite bet: a *complete* machine learning platform - data auditing, training, evaluation,
explanation, and model reuse - where **every single computation runs on your own machine**.
No backend, no accounts, no uploads. Open the network tab while it trains eight models:
nothing leaves.

It is live at **[app.dominicdapice.com](https://app.dominicdapice.com)**, installable as an
offline PWA, bilingual (EN/FR), and organized in three sections.

## The ML Lab - `/ml`

The core loop: drop a CSV (or Excel file, or pick a demo like titanic), choose the column to
predict, and the lab profiles every column, detects the task (binary, multi-class,
regression), flags identifiers, constants and **target leakage**, then trains a zoo of
models in a Web Worker: naive baseline, linear/logistic regression, k-NN, Gaussian Naive
Bayes, decision tree, random forest - plus a **hand-written histogram gradient boosting**
(LightGBM-style quantile bins, second-order gains, Newton leaves) and a **hand-written MLP**
(seeded He init, full-batch Adam).

<figure style="margin: 2rem 0; text-align: center;">
  <img src="/assets/img/labml/ml-import-en.png" alt="LabML's ML Lab entry screen: a drag-and-drop zone for CSV or Excel files, read locally with nothing uploaded, next to five one-click demo datasets" width="1280" height="860" loading="lazy" style="width: 100%; height: auto; border-radius: 12px;" />
  <figcaption style="font-size: 0.85rem; color: var(--faint); margin-top: 0.6rem;">Zero friction in: drop a CSV or Excel file — read right in the browser, nothing uploaded — or hit one of the demo datasets and go.</figcaption>
</figure>

The leaderboard is only the beginning. What I really wanted to build is the part most demos
skip: *honest evaluation*.

<figure style="margin: 2rem 0; text-align: center;">
  <img src="/assets/img/labml/ml-leaderboard-en.png" alt="LabML leaderboard on titanic: eight models ranked by accuracy with delta versus the naive baseline, F1, ROC-AUC, log-loss, training time and p50 inference latency" width="1054" height="366" loading="lazy" style="width: 100%; height: auto; border-radius: 12px;" />
  <figcaption style="font-size: 0.85rem; color: var(--faint); margin-top: 0.6rem;">Thirty seconds after loading titanic: eight models ranked against the naive baseline, with training time and p50 inference latency for each — run observability included.</figcaption>
</figure>

<figure style="margin: 2rem 0; text-align: center;">
  <img src="/assets/img/labml/v20-uncertainty-en.png" alt="LabML uncertainty panel: dot-and-whisker 95% intervals for each model's accuracy, with a paired verdict stating the winner beats the baseline in 100% of resamples" width="1054" height="387" loading="lazy" style="width: 100%; height: auto; border-radius: 12px;" />
  <figcaption style="font-size: 0.85rem; color: var(--faint); margin-top: 0.6rem;">"0.967 on 30 test rows is not 0.967." Every metric ships with a 95% bootstrap interval, and the winner-vs-baseline gap gets a paired verdict in plain language.</figcaption>
</figure>

- Every run is scored against a **naive baseline** on a held-out test split (seeded,
  stratified - the same seed always reproduces the same run).
- Every leaderboard metric carries a **95% bootstrap interval** (1,000 seeded resamples,
  shared across models so comparisons are paired), with a verdict that says whether the
  winner's lead is "probably real" or "possibly noise".
- A **per-segment analysis** answers "where does my model fail?" by re-scoring the test
  set on every categorical slice - including columns *excluded* from training, exactly
  where proxy effects hide. On titanic it points straight at deck C and Cherbourg
  passengers.
- On imbalanced data, a **precision-recall curve, a calibration curve and a cost-priced
  decision threshold** show what accuracy hides - a probability is not a decision; the
  threshold belongs to your costs.

<figure style="margin: 2rem 0; text-align: center;">
  <img src="/assets/img/labml/v18-segments-en.png" alt="LabML per-segment analysis on titanic: accuracy recomputed per deck, embarkation port, class and sex, worst gaps first, with the leaked alive column sliced despite being excluded from the features" width="1054" height="643" loading="lazy" style="width: 100%; height: auto; border-radius: 12px;" />
  <figcaption style="font-size: 0.85rem; color: var(--faint); margin-top: 0.6rem;">"Where does my model fail?" - the held-out test set sliced by every categorical column, worst gaps first. A gap is a finding to investigate, not a verdict.</figcaption>
</figure>

Understanding tools round it out: permutation importance, partial dependence, live what-if
predictions with **exact Shapley explanations** (the bars sum to prediction minus baseline),
and a rule-generated plain-language read of every run - no LLM involved.

<figure style="margin: 2rem 0; text-align: center;">
  <img src="/assets/img/labml/ml-insights-en.png" alt="LabML insight charts for the winning model: interactive confusion matrix, ROC curve with AUC, permutation-importance bars and partial dependence plots" width="1054" height="646" loading="lazy" style="width: 100%; height: auto; border-radius: 12px;" />
  <figcaption style="font-size: 0.85rem; color: var(--faint); margin-top: 0.6rem;">Understanding the winner: confusion matrix, ROC curve, permutation importance, partial dependence — every chart computed from scratch in the browser.</figcaption>
</figure>

The lab also closes the loops a real workflow needs: **score a new batch** with an honest
test-vs-batch comparison, **compare two runs side by side** ("did my cleaning help?" -
with cross-run uncertainty verdicts), **hyperparameter search** by seeded random search
with proper cross-validation, and **export a model as JSON, then re-import it later** -
LabML rebuilds the exact predictor (byte-identical predictions) and scores any CSV without
retraining. No target column? A seeded k-means + PCA **exploration mode** describes the
groups it finds; a date column unlocks **Holt-Winters forecasting** validated by a
rolling-origin backtest. Runs persist locally (IndexedDB) with all their artifacts, and a
dataset can opt in to persistence under an explicit 50 MB budget.

## The Data Studio - `/data`

Real datasets are messy, so the lab has a dedicated repair shop. The Data Studio audits a
file without uploading it - missing cells, duplicates, case/whitespace variants,
Tukey-fence outliers, constant and id columns, rolled into a deterministic 0-100 score -
and fixes it through a **replayable cleaning recipe**: trim, merge variants, deduplicate,
impute, clamp outliers, force column types, expand dates, and drop multivariate anomalies
found by a hand-written, seeded **isolation forest**. The recipe exports as JSON and
replays on next month's file.

<figure style="margin: 2rem 0; text-align: center;">
  <img src="/assets/img/labml/data-studio-en.png" alt="LabML Data Studio on the dirty demo file: quality score improving from 48 to 92 out of 100 after the cleaning recipe, with a join panel to enrich the dataset from a second file" width="1280" height="900" loading="lazy" style="width: 100%; height: auto; border-radius: 12px;" />
  <figcaption style="font-size: 0.85rem; color: var(--faint); margin-top: 0.6rem;">The dirty demo file goes from 48/100 to 92/100 through the replayable recipe — and a second file is one click away from a left join on a shared key.</figcaption>
</figure>

It also covers the two everyday data gestures most tools skip: **left-joining a second
file** on a shared key (match rate, duplicates and orphans are *named*, never silent) and
a **drift check** that compares a new batch against the reference - schema diff, PSI per
column, new and vanished categories, severity verdict. One click hands the cleaned result
to the ML Lab.

## The AI Playground - `/ai`

Two smaller experiments in on-device AI, same privacy rules:

- **Vision**: image analysis running locally through ONNX Runtime Web (WebAssembly) -
  drop a photo or use the webcam and three self-hosted networks read it: an
  EfficientNet-Lite4 classifier names the main subject (1,000 ImageNet classes, 77.6%
  top-1), YOLOX-Nano draws boxes around the objects it finds (80 everyday classes) and
  UltraFace locates faces - "1 face detected", counted in plain language. The box math
  (grid decode, IoU, non-maximum suppression) is hand-written and unit-tested, and the
  UI still says honestly what the models cannot know: detection says where, not who.
- **Data assistant**: ask plain English or French questions about your loaded dataset -
  averages, counts under a condition, top-N, correlations - answered by a deterministic
  local interpreter, clearly labeled as *not* a language model. When it does not
  understand, it says so instead of guessing.

<figure style="margin: 2rem 0; text-align: center;">
  <img src="/assets/img/labml/v23-vision-en.jpg" alt="LabML Vision 2 on a NASA crew portrait: teal boxes labeled person around five astronauts, dashed copper boxes on their faces, counts reading 6 objects detected and 5 faces detected, the ImageNet top-5 list and two honesty notes" width="552" height="949" loading="lazy" style="width: 100%; height: auto; border-radius: 12px;" />
  <figcaption style="font-size: 0.85rem; color: var(--faint); margin-top: 0.6rem;">A NASA crew photo, read by three networks in the browser: a box per person, a dashed box per face — "6 objects · 5 faces detected". The single-label classifier struggles with a whole scene ("sewing machine"?) and the panel says so: honesty over theater, detection says where, not who.</figcaption>
</figure>

<figure style="margin: 2rem 0; text-align: center;">
  <img src="/assets/img/labml/ai-chat-en.png" alt="LabML data assistant answering plain-language questions on titanic: a row count for sex = female and average age by passenger class, computed by a local deterministic interpreter" width="1280" height="950" loading="lazy" style="width: 100%; height: auto; border-radius: 12px;" />
  <figcaption style="font-size: 0.85rem; color: var(--faint); margin-top: 0.6rem;">"How many rows where sex is female?" — 314, counted locally by a deterministic interpreter that is honestly labeled as not a language model.</figcaption>
</figure>

## Under the hood

The engineering constraint that shaped everything: **if it computes, it was written by
hand and it is deterministic**. Gradient boosting, MLP, k-means++, power-iteration PCA,
Holt-Winters, isolation forest, PSI, Shapley values, bootstrap intervals, PR/ROC and
calibration curves, detection box decoding (grids, IoU, non-maximum suppression) - all
implemented from scratch in TypeScript, seeded end to end, and unit-tested against known
results. Everything heavy runs in Web Workers behind typed
message protocols, so the UI never blocks.

The quality bar is enforced in CI: 248 unit tests, 50 Playwright end-to-end tests
(including an offline-PWA test, a fake-webcam test and axe-core WCAG accessibility
checks), strict TypeScript, and Lighthouse budgets - the `/ml` page scores ≈ 0.99 on
mobile under real throttling thanks to prerendered static shells that paint before
JavaScript arrives.

And the privacy claim is architectural, not a promise: a strict Content-Security-Policy
allows zero third-party calls, share links carry metrics in the URL *fragment* (which
browsers never send to servers), and the whole app - demo datasets and vision models
included - keeps working with the network cable pulled.

**Try it: [app.dominicdapice.com](https://app.dominicdapice.com)** - load the titanic
demo, train, and scroll: the leaderboard, the intervals, the segment analysis and the
threshold tools tell one honest story about a model in about thirty seconds.
