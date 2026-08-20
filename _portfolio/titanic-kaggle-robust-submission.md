---
layout: portfolio
title: "Titanic on Kaggle - When Better Local Validation Doesn't Mean a Better Score"
date: 2026-08-20 07:00:00 -0400
lang: en
tags: [machine-learning, kaggle, data-science, validation, testing]
description: >-
  A solo deep-dive into the classic Kaggle Titanic competition, pushed beyond the
  usual notebook: tested feature engineering, ticket-grouped validation, four model
  families compared - and a Gradient Boosting that scored 0.8440 locally but 0.75358
  on Kaggle. Why I stopped at an honest 0.78947 instead of chasing the leaderboard.
translation_url: /portfolio/titanic-kaggle-soumission-robuste/
translation_label: "🇫🇷 Lire cet article en français"
---

The Titanic competition is the "hello world" of Kaggle - which is exactly why I picked it. With the modeling problem well understood, I could focus on a harder question that follows you into every real ML project: **what do you do when your local validation says you are improving and the leaderboard says you are not?**

My final, legitimate score is **0.78947** (330 correct predictions out of 418), obtained without ever using the known survival of a family member or ticket companion to predict a passenger's fate. The number matters less than how I got there - and where I chose to stop.

## What I built

The project goes beyond a single notebook: an exploratory notebook plus a set of small, tested Python scripts.

- Exploration and cleaning with pandas;
- Feature engineering around the passenger's title, family, ticket, and fare;
- Comparison of logistic regression, Random Forest, Gradient Boosting, and CatBoost;
- Stratified cross-validation first, then **grouped validation by ticket** so that members of the same travel group never straddle a fold;
- Blends, threshold tuning, and a prediction-flip analysis that aligns every submission on `PassengerId` to see exactly which passengers each change affects;
- **Unit tests** that pin down the feature schema and prove the "safe" features have no direct dependence on the `Survived` target.

## The finding: OOF 0.8440, Kaggle 0.75358

The most interesting result of the project is a divergence. My best Gradient Boosting reached **0.8440 out-of-fold** - the strongest local score of the whole series - and then scored **0.75358 on Kaggle**, the *worst* of my decisive experiments. Picking the model on OOF alone would have led me in exactly the wrong direction.

| Approach | OOF accuracy | Kaggle score | Flips vs reference |
| --- | ---: | ---: | ---: |
| Enriched features + logistic regression | 0.8238 / 0.8249 grouped | 0.75837 | 37 |
| Gradient Boosting + enriched features | **0.8440** | 0.75358 | 39 |
| Logistic/RF/GB blend, grouped OOF threshold | 0.8384 grouped | 0.76315 | 27 |
| Cautious meta-stack, 0.5 threshold | 0.8305 | 0.78468 | 2 |
| Group-corrected reference | - | **0.78947** | 0 |

Three limits explain the gap:

1. **The public test set is tiny.** One flipped prediction moves the score by about `0.002392` - a difference of `k` predictions bounds the new score within `± k/418` of the old one.
2. **Selection pressure amplifies noise.** Comparing many variants and keeping the best OOF results is a good way to select fold-specific noise rather than signal.
3. **Folds don't reproduce the test set.** Even grouped by ticket, cross-validation folds match neither the composition of Kaggle's 418 passengers nor all of their family correlations.

## The line I drew

Well-known Titanic tricks use the *known survival* of a relative or ticket companion to predict a passenger's outcome. Even with careful cross-fitting, those rules exploit the targets of related rows - a form of leakage I did not want in the solution I present. I kept relational features computed **without the target** - family size, surname frequency, ticket prefix, ticket-group size - and left the rest out.

## A reproducible conclusion

The deliverable is not just a score, it is a verifiable one: a canonical submission file, a frozen byte-identical copy with its **SHA-256 recorded**, a script that compares any two submissions passenger by passenger, and a test suite (`unittest`) that guards the feature contracts. Every experiment that shaped the final decision is summarized with its numbers in the repository's `EXPERIMENTS.md`.

## Lessons learned

**Correct code, convincing local validation, and true generalization are three different things.** Unit tests protect the first, OOF comparisons inform the second, and nothing short of genuinely held-out data guarantees the third.

**A small public leaderboard is a noisy measurement, not a target.** After consistent failures across logistic regression, boosting, blending, and stacking, I stopped treating OOF as a promise of score and used it as a diagnostic tool.

**Knowing when to stop is part of the method.** I ended the submissions at 0.78947. I would reopen the project under two conditions: an independent evaluation that played no role in development, and a leak-free hypothesis showing a stable gain. Without those, keeping the current result *is* the most solid conclusion.

## Full titanic GitHub project

[Titanic](https://github.com/dapiced/titanic)
