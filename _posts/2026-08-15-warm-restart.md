---
layout: post
title: "Warm Restart"
date: 2026-08-15 09:00:00 -0400
tags: [machine-learning, deep-learning, meta, career]
description: "The most copied learning-rate schedule in deep learning has rest built in. Written on vacation, three weeks before the fall 2026 session - machine learning and deep learning - begins."
---

In three weeks, I go back to school.

The fall 2026 session is the one my whole certificate has been climbing toward: machine learning and deep learning, formally, with deadlines and grades - the two subjects I have spent the summer [writing about from the bleachers](/blog/2026/08/forty-years-of-losing-to-a-tree/). Right now, though, I am on vacation. And I have the August disease of every mid-career student: the low hum of guilt that says every day spent doing nothing is a day the textbooks are winning.

So, as therapy, I went looking for what the field I am about to study actually says about rest. It turns out the argument is settled, and it is settled *inside the algorithms*. The most copied learning-rate schedule in modern deep learning does not tolerate rest. It **schedules** it.

[![The 2026 learning-rate schedule drawn as cosine annealing with warm restarts: an amber curve decays through the winter session, restarts on May 1, decays through the spring session into the August vacation valley - where a cyan marker reads "you are here, aug 15" at the minimum - then a bright vertical warm restart on September 1 relaunches the rate to maximum for the fall 2026 session, labeled ML + DL, decaying through December](/assets/img/warm-restart-schedule.svg)](/assets/img/warm-restart-schedule.svg)

## The learning rate is enthusiasm

The learning rate is the most human number in machine learning. It is the answer to the question: *when new evidence arrives, how much do you let it move you?* Set it high and the model lurches at every example, overshooting, unlearning at night what it learned in the morning. Set it low and the model becomes that person who has read everything and changed their mind about nothing.

So practitioners decay it. Start bold, finish careful. The most elegant version is cosine annealing: the rate glides down a half-cosine from its maximum to nearly zero. If you have ever been a student, you have lived this curve. September is the top - big steps, whole worldviews revised in a week. December is the bottom - tiny adjustments, polishing details for the exam. The curve *is* a semester.

And the naive assumption - my August-guilt assumption - is that the curve should only go down. Learn harder, decay slower, never stop. One long semester from here to the horizon.

In 2016, Ilya Loshchilov and Frank Hutter published a schedule called [SGDR - Stochastic Gradient Descent with Warm Restarts](https://arxiv.org/abs/1608.03983) - that does the opposite, and it is one keyword argument in every framework today:

```python
scheduler = torch.optim.lr_scheduler.CosineAnnealingWarmRestarts(
    optimizer, T_0=4, eta_min=1e-5,   # glide down for a term... then snap back up
)
```

When the rate has annealed all the way down - when the model is at its most careful, its most converged, its most *finished* - the schedule snaps the learning rate back up to maximum. On purpose. Repeatedly. And the models come out **better**: the restarts shake the optimizer out of narrow, brittle valleys of the loss landscape, and there is [a body of evidence](https://arxiv.org/abs/1609.04836) that the wide, flat minima you settle into after a restart are precisely the ones that generalize to data you have never seen.

Read the shape of that curve again, because I keep drawing it on this year: the deep drop is not the failure of the climb. The deep drop is the *precondition* of the next climb. You cannot restart warm unless you first actually stop.

There is a bonus, and it is my favorite part. In 2017, a follow-up paper called [Snapshot Ensembles](https://arxiv.org/abs/1704.00109) noticed that if you save the model at the bottom of each cycle - each converged, careful, end-of-term self - and let those snapshots vote together, you get an ensemble for free. Subtitle of the paper: *train 1, get M for free*. Every version of you that finished a cycle still gets a vote. Nothing you converged to is wasted.

## Momentum

Here is the fear, stated plainly, because leaving it unstated gives it power: I am going back to school with twenty-five years of infrastructure behind me and a textbook in front of me, and some part of every mid-career student whispers that the counter resets to zero. New subject, new gradient, beginner again.

The optimizer disagrees. No serious one moves on the current gradient alone. Since [1964](https://distill.pub/2017/momentum/), the standard trick has been momentum: the update is an exponentially weighted memory of *every gradient that came before*, with the newest merely bending the trajectory. A heavy ball rolling downhill does not stop to reconsider its life at each pebble. Velocity accumulates. It carries you across flat, discouraging stretches of the landscape; it damps the panicked oscillations of the first week of a course.

Twenty-five years of production systems is not baggage I drag into a classroom. It is the velocity term. When the lecture defines overfitting, I have watched it page an on-call engineer at 3 a.m. When it defines a pipeline, I have migrated fifteen hundred of them. The gradient is new. The ball was already moving.

## The beach is a replay buffer

One more, because this is the one that absolves the dock and the deck chair entirely.

In 1994, Matthew Wilson and Bruce McNaughton recorded the hippocampi of rats and found [something astonishing](https://www.science.org/doi/10.1126/science.8036517): the place cells that had fired in sequence while a rat ran a maze fired again, in the same patterns, while the rat *slept*. The brain re-runs its day offline. The learning does not happen only in the maze. A large share of it happens afterward, in the replay - which is when short-term traces get consolidated into something that lasts.

Twenty-one years later, DeepMind's [DQN agent](https://www.nature.com/articles/nature14236) - the one that learned Atari from raw pixels - worked *because* of a mechanism its authors explicitly borrowed from the hippocampus: an experience replay buffer. The agent stores what happened and learns by replaying it later, shuffled, at leisure, decorrelated from the pressure of the moment. Without the buffer, the whole thing destabilizes and forgets.

So that is what August is. Not paused training - consolidation. Somewhere in the background, a year of statistics is being replayed out of order: R vectors on a lake, distributions on a long drive, last session's proofs resurfacing at odd hours the way replayed sequences do. The vacation is not an interruption of the training loop. It is the part of the loop where the training becomes permanent.

## What September holds

The fall session, then. Machine learning and deep learning - the real courses, the ones with my name on the enrollment. I spent the summer writing about this field as an outsider with a blog: its forty-year war over tabular data, its optimizers, its history. Starting in September, the field gets to ask *me* the questions, and I intend to enjoy that reversal enormously.

The train/validation split is already arranged. Coursework is the training set. [Kaggle](https://www.kaggle.com/dominicdapice) is the held-out data - the place where theory meets a leaderboard that has never read my homework and does not grade on effort. A model is what it scores on data it has not seen; a student, I suspect, is the same.

And the schedule and the sky agree, which I take as a good omen. Here in Québec, September is when [Andromeda climbs back into the evening sky](/blog/2026/07/a-star-for-my-father/) - and on the star-path to that galaxy, there is one star I always find first. My father watched me work my whole life. This fall, on every clear night between me and the deadline, he gets to watch me study. I will take that over any productivity system ever devised.

Three more weeks at η_min, and I will not feel guilty about a single day of it. The schedule says this is the part where I get better at things I am not currently doing. Then September 1: learning rate back to maximum, biggest steps of the year, everything revisable again.

The optimizer has a name for it, and so does the calendar. Warm restart.

*On y va.*
