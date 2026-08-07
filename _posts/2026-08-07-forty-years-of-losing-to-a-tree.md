---
layout: post
title: "Forty Years of Losing to a Tree"
date: 2026-08-07 00:10:00 -0400
tags: [machine-learning, deep-learning, data-science, kaggle]
description: "Deep learning took images in 2012 and text in 2018 - and kept losing to decision trees on tabular data until January 2025. I ran the four-decade rematch on one CPU."
image:
  path: /assets/img/tree-rematch-card.png
  width: 1200
  height: 630
---

On 8 January 2025, *Nature* published [a paper about spreadsheets](https://www.nature.com/articles/s41586-024-08328-6).

That is not how the authors would put it. The title is "Accurate predictions on small data with a tabular foundation model," the model is a transformer called TabPFN, and *Nature* does not, as a rule, publish machine learning benchmarks. It made an exception here, and the exception is the story: this paper marked the fall of the last benchmark where deep learning still lost. Not Go, not protein folding, not poetry. The table. Rows and columns. The CSV file. For roughly forty years, the most valuable data format in the working world belonged to an algorithm family whose founding document was published in 1984, and every neural challenger sent against it came back beaten.

I wanted to see that whole war compressed into one afternoon. So I staged the rematch myself: five algorithms spanning 1984 to 2023, four datasets old enough to have watched every challenger arrive, one CPU, default hyperparameters, seed 42. The results are at the bottom of this post. The final margin is nine thousandths of a point of AUC, and getting the challenger into the ring required extracting a 98.6-megabyte time capsule from a git tree, because my sandbox's proxy had opinions. We will get there.

First, the war.

[![The history of tabular machine learning drawn as a git commit graph: an amber main line of tree methods running from Fisher 1936 through CART 1984, AdaBoost 1997, Random Forests and Gradient Boosting 2001, XGBoost 2016 and LightGBM 2017, and a cyan neural-nets branch that wins images in 2012, ships TabPFN at ICLR 2023, and finally merges into the main line on 8 January 2025 when TabPFN v2 lands in Nature, followed by TabPFN-2.5 and Google's TabFM at HEAD in June 2026](/assets/img/tabular-ml-git-log.svg)](/assets/img/tabular-ml-git-log.svg)

## The most boring data in the world

A table is data where rows are things and columns mean something. Column 7 is `annual_income`. Column 12 is `days_since_last_claim`. There is no sky in it, no grammar, no melody - none of the structure deep learning feasts on. It is also, by any commercial measure, the data that runs the world: credit scoring, fraud detection, churn prediction, insurance pricing, hospital readmission risk, predictive maintenance. When something boring and consequential gets predicted, it gets predicted from a table.

And for the entire deep learning revolution, tables would not fall. AlexNet took images in 2012. Speech went next, then translation, then Go, then [protein structures](https://www.nature.com/articles/s41586-021-03819-2) - that one eventually collected a share of a Nobel Prize. Meanwhile, on Kaggle, where models compete on real prediction problems with money on the line, the reigning champion was a gradient-boosted decision tree. The [XGBoost paper](https://arxiv.org/abs/1603.02754) states it with the dryness of a court record: among the 29 winning solutions published on Kaggle's blog in 2015, 17 used XGBoost. Deep neural networks, the second most popular method, appeared in 11 - mostly the image and text contests. The community folklore compressed this into four words: *when in doubt, XGBoost*.

The modal model in production has never been a transformer. It is a committee of decision trees reading a table.

## 1984: if/else, learned from data

The founding document is a book: *Classification and Regression Trees*, 1984 - Leo Breiman, Jerome Friedman, Richard Olshen, Charles Stone. Statisticians, not AI people. Two years later, from the AI side, Ross Quinlan published [ID3](https://link.springer.com/article/10.1007/BF00116251). Different tribes, same discovery: you can learn a bureaucracy.

A decision tree is nothing more than nested if/else, chosen from data. Is `plasma_glucose` above 154? Go left. Is `age` above 28? Go right. Each split is picked greedily to make the resulting groups purer, and the recursion stops when the groups are small or clean enough. That is the whole algorithm. You can print the model. You can read it aloud to a regulator, which is a large part of why banks still love it. It needs no feature scaling, shrugs at missing values, and trains in milliseconds.

It also, on its own, is not very good. A single tree grown deep will happily memorize noise; grown shallow, it underfits. Statisticians call this high variance. My benchmark below calls it finishing last on all four datasets, once by twenty points. Hold that thought, because it matters for what "the tree won for forty years" actually means.

## The tree becomes a crowd

What actually won for forty years was never one tree. It was an escalating series of committees wearing the tree's name.

1997: [AdaBoost](https://doi.org/10.1006/jcss.1997.1504) (Freund and Schapire). Train a weak tree, reweight the examples it got wrong, train another, let them vote. Weak learners, combined, become arbitrarily strong - a theorem, not a slogan.

2001: Breiman, then 73 years old, publishes [Random Forests](https://link.springer.com/article/10.1023/A:1010933404324): hundreds of trees, each trained on a bootstrap sample of the rows and a random subset of the columns, decorrelated on purpose, averaged. The same year, Friedman publishes gradient boosting: each new tree is fit to the *residual errors* of the ensemble so far. Gradient descent, except every step downhill is a tree.

2014-2017: the industrialization. A graduate student named Tianqi Chen rewrites gradient boosting with sparsity-aware splits, regularization, and cache-conscious data layout, and calls it [XGBoost](https://arxiv.org/abs/1603.02754). Microsoft answers with [LightGBM](https://proceedings.neurips.cc/paper/2017/hash/6449f44a102fde848669bdd9eb6b76fa-Abstract.html), Yandex with CatBoost. By 2017 the 1984 algorithm has become a family of siege engines, and the table is their castle.

## Why the tables would not fall

It was not for lack of trying. Between 2012 and 2022 there was a steady drip of papers announcing that deep learning had finally caught up on tabular data, most of which evaporated outside their own evaluation setup. In 2022 three researchers - Grinsztajn, Oyallon and Varoquaux - ran [the autopsy](https://arxiv.org/abs/2207.08815) at NeurIPS: 45 curated datasets, everything tuned properly, and tree ensembles still on top of every neural architecture, including the early tabular transformers. Better, they explained *why*, and the three reasons are worth internalizing because they are really one reason.

**Real-world tabular targets are jagged.** Approval flips when a credit score crosses a threshold; a machine fails when a temperature does. Neural networks carry a built-in bias toward smooth functions - it is what makes them generalize on images. A tree has no such prejudice. A discontinuity is one split away.

**Tables are full of columns that do not matter.** Real tables drag along dozens of uninformative features. A tree simply never splits on them; they cost nothing. An MLP has to actively learn to ignore them, through every weight, against every batch of noise.

**Rotation invariance is the wrong symmetry.** This is the deep one. To an MLP's first layer, any rotation of the feature space is the same problem - it will happily begin from `0.3 × income − 1.7 × heart_rate` as a coordinate. But that quantity means nothing. Tables have privileged axes: the columns. An axis-aligned split respects them by construction. CNNs conquered images by hard-coding translation symmetry; transformers conquered text by hard-coding sequence. The tree owned tables because it hard-codes the one structural truth of tabular data: *columns mean things*.

Put together: deep learning was not missing scale on tables. It was missing the right inductive bias - and for a decade, nobody could find a way to give it one.

## The siege weapon was not a bigger network

The thing that finally worked did not attack the table at all. It attacked the concept of training.

In 2022, Müller and colleagues published a strange idea called [prior-data fitted networks](https://arxiv.org/abs/2112.10510): transformers, they showed, can learn to *do Bayesian inference* - to behave, in a single forward pass, like the posterior predictive distribution of a model class. A year later came the application, [TabPFN](https://arxiv.org/abs/2207.01848): pre-train a transformer on millions of small *synthetic* datasets, sampled from a prior over causal structures - tables that never existed, generated by the hundred million from random structural causal models. Then, at inference time, feed it your actual table: training rows, training labels, and test rows, all together, as context.

Read that again, because it inverts everything: **your data is never trained on.** No gradient ever touches it. `fit()` uploads the training set; `predict()` is one forward pass in which the model, in effect, conditions its learned prior on your 500 rows and emits a posterior. Training, as a per-dataset activity, is gone. The model does not learn your dataset. It has already learned what datasets are like.

The 2023 version was a proof of concept, capped at 1,000 rows, 100 features, 10 classes. The version *Nature* accepted in January 2025 handled real tables - categoricals, missing values, outliers, 10,000 rows - and, per the paper, beat baseline ensembles that had been tuned for four hours, in seconds, untuned. Since then the drumbeat has been steady: [TabPFN-2.5](https://arxiv.org/abs/2511.08667) in November 2025 stretched to 50,000 rows and 2,000 features; [TabICL](https://arxiv.org/abs/2502.05564) pushed in-context learning to still larger tables; and on 30 June 2026 Google shipped [TabFM](https://huggingface.co/google/tabfm-1.0.0-pytorch), with an `AI.PREDICT` SQL function [headed for BigQuery](https://www.marktechpost.com/2026/07/01/google-ai-introduces-tabfm-a-hybrid-attention-tabular-foundation-model-for-zero-shot-classification-and-regression/). The foundation model is moving into the database. That is the tree's home address.

## The rematch, at home

Benchmarks run by a model's authors always deserve a raised eyebrow, so I ran my own - deliberately small, deliberately fair to the trees, on one CPU with no GPU in sight.

The rules: stratified 5-fold cross-validation, ROC AUC, **default hyperparameters for everyone**, fixed seed. No tuning for anybody - which, note, is the setting the trees' own culture recommends against, and the setting the foundation model was explicitly built for.

The datasets are the elders of the UCI repository, all small, all older than some contestants: **sonar** (1988, 208×60) - submarine sonar chirps against rocks versus mines, assembled by Gorman and Sejnowski for their neural network experiments; **pima-diabetes** (1988, 768×8); **ionosphere** (1989, 351×34) - radar returns from the ionosphere; **breast-cancer-wisconsin** (1995, 569×30) - cell nuclei measured from fine-needle aspirates. Real measurements, real stakes, thousands of citations of battle history.

And a confession about the fifth contestant. This post was produced in a sandboxed session whose egress proxy allows PyPI, GitHub, and very little else; `huggingface.co` answers 403 Forbidden here, and the *Nature*-generation TabPFN weights live behind it. The only checkpoint that could cross the wire at all was the original 2023 prototype - committed directly into [the project's git history](https://github.com/automl/TabPFN), a single 98.6 MB blob sitting one and a half megabytes under GitHub's file-size ceiling, which I fished out with `git cat-file` from a tag three major versions old. So the neural corner is fought by a model **two generations behind** the current state of the art, patched by hand to run on a torch build three years its junior. Remember that while reading the table.

```python
models = {
    "CART 1984":             DecisionTreeClassifier(random_state=42),
    "Random Forest 2001":    RandomForestClassifier(random_state=42),
    "Gradient Boosting 2001": GradientBoostingClassifier(random_state=42),
    "XGBoost 2016":          XGBClassifier(random_state=42),
    "TabPFN 2023":           TabPFNClassifier(device="cpu", seed=42),
}
for X, y in datasets:                       # vintage 1988-1995
    for name, model in models.items():
        for train, test in StratifiedKFold(5, shuffle=True, random_state=42).split(X, y):
            model.fit(X[train], y[train])   # for TabPFN: an upload, not an optimization
            score(model.predict_proba(X[test]))
```

Mean ROC AUC over the five folds:

| Dataset | CART 1984 | Random Forest 2001 | Grad. Boosting 2001 | XGBoost 2016 | TabPFN 2023 |
|:---|---:|---:|---:|---:|---:|
| sonar (1988) | 0.712 | 0.927 | 0.920 | 0.925 | **0.932** |
| pima-diabetes (1988) | 0.672 | 0.824 | 0.828 | 0.791 | **0.833** |
| ionosphere (1989) | 0.889 | 0.979 | 0.965 | 0.965 | **0.985** |
| breast-cancer (1995) | 0.900 | 0.989 | 0.993 | 0.994 | **0.997** |

[![Benchmark results as horizontal bars, ROC AUC over five stratified folds with default hyperparameters: TabPFN 2023 narrowly tops Random Forest, Gradient Boosting and XGBoost on all four classic datasets - sonar, pima-diabetes, ionosphere and breast-cancer-wisconsin - while the single 1984 CART tree finishes far behind everywhere](/assets/img/tree-rematch-results.svg)](/assets/img/tree-rematch-results.svg)

Five things this table says, in decreasing order of comfort:

**The 1984 tree, alone, was never the champion.** On pima it scores 0.672 to the ensembles' 0.82-0.83 - not a rounding error, a different sport. Everything the tree family achieved, it achieved as a crowd. The forty-year reign belongs to bagging and boosting; the lone tree has been obsolete since roughly 1997. What survived was not an algorithm but an inductive bias, re-armored every decade.

**The prototype went four for four.** Margins of +0.003 to +0.009 AUC over the best tree, each one inside a standard deviation - on any single dataset I would call it noise, and you should too. But four out of four, with zero hyperparameters touched, from the *weakest* foundation model checkpoint in existence, is the same pattern the large benchmarks report with proper statistics at scale: on small tables, the prior now beats the ensemble.

**One of these datasets was collected by connectionists.** Sonar was built in 1988 to study neural networks, then spent decades as a stock benchmark where tree ensembles comfortably outscored them. In this rematch, the neural net finally tops that table - thirty-eight years after the data was recorded.

**The trees keep the throughput crown, easily.** XGBoost spends 0.04 seconds per fold; TabPFN spends 0.3 to 0.7 on my CPU - and unlike the trees, it pays at *prediction* time, because the training set ships along with every forward pass. At 500 rows, nobody cares. At 50 million rows, this is not a contest; it is not even a conversation. Know which regime you are in.

**Defaults are a lottery, which is the whole point.** Untuned XGBoost lost to untuned Random Forest on two of four datasets - anyone who has burned a weekend on `max_depth` and `learning_rate` grids is nodding. Tuning would close that gap. The foundation model's entire pitch is that there is no gap to close and no weekend to burn: what you saw is what it does, first try, every try.

## Merge commit

In 2001 - the same year as the Random Forest paper - Breiman published an essay called [Statistical Modeling: The Two Cultures](https://projecteuclid.org/journals/statistical-science/volume-16/issue-3/Statistical-Modeling--The-Two-Cultures-with-comments-and-a/10.1214/ss/1009213726.full), accusing his own discipline of irrelevance. The *data modeling* culture, he wrote, assumes the data was generated by a nice distribution and estimates its parameters; the *algorithmic* culture assumes nothing, predicts, and measures. He had defected to the second culture and built its best weapon, and he died in 2005 believing the forests had settled the argument.

Now look at what finally beat them. A prior-data fitted network is a transformer trained to approximate *Bayesian posterior prediction* - the data-modeling culture's holiest object, the thing all those distributional assumptions existed to reach - manufactured by brute algorithmic force from a hundred million synthetic tables, and evaluated exactly the way Breiman demanded: held-out, adversarial, no excuses. The war between the two cultures did not end with a winner. It ended with a merge commit, dated 8 January 2025.

The trees are not going anywhere. They still score your credit card in single-digit milliseconds, they still win outright at scales no foundation model reaches, they can still be printed out and argued with in front of a regulator, and the strongest AutoML ensembles now fold TabPFN in *alongside* boosted trees rather than instead of them - absorption, not extinction. But something did end this year. For the first time since 1984, *just use XGBoost* is not the end of the tabular conversation. It is the baseline the new thing is measured against.

Forty years is a good run for an if statement. The merge took eighty-nine years, measured from Fisher's fork. The forward pass takes half a second.
