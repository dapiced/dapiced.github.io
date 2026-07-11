---
layout: post
title: "The Universe Just Went to Production"
date: 2026-07-11 13:00:00 -0400
tags: [astronomy, dataops, mlops]
description: "Ten million alerts a night, a 60-second SLO, and Kafka under the stars, the Vera C. Rubin Observatory, read with infrastructure eyes."
---

On June 30, 2026, the most ambitious scientific instrument went to production.

Not "saw first light", that happened a year ago, with the fanfare and the gorgeous press images. What happened eleven days ago is something I recognize from a different part of my life: after months of commissioning, system optimization and a formal operational readiness review, the Vera C. Rubin Observatory officially started its ten-year Legacy Survey of Space and Time (LSST). The head of the survey listed the criteria behind the go decision: image quality, effective survey speed, system uptime and reliability, calibration accuracy.

Uptime. Reliability. Calibration. Readiness review. I've spent twenty-five years around go-lives, and I know that vocabulary by heart. Strip out the telescope, and that paragraph could be pasted into any change request I've ever approved.

So I did what I always do with a system that impresses me: I went looking for the architecture. What I found is, I think, the most beautiful data pipeline ever built, and I don't mean in astronomy. I mean anywhere.

---

## The workload

Start with the instrument, because the numbers set the stage.

On Cerro Pachón, a 2,682-metre summit in the Chilean Andes, sits the Simonyi Survey Telescope: an 8.4-metre mirror feeding LSSTCam, the largest digital camera ever built, 3,200 megapixels, roughly the size of a small car, about three tonnes. Every ~40 seconds, all night, it takes a fresh image covering 3.5 degrees of sky, an area of about forty full moons. Call it a thousand images a night. Every three or four nights, it has covered the entire visible southern sky in six filter bands, and then it starts over, and keeps starting over, for ten years. Each patch of sky gets revisited roughly 800 times.

The output: about 10 terabytes of image data per night, around 30 petabytes of images by the end of the survey, a catalog of some 17 billion stars and 20 billion galaxies, trillions of measurements. An $800-million cosmic time-lapse.

Those are impressive storage numbers. Storage is also the least interesting part.

## A 60-second SLO, written into the requirements

Here is the number that stopped me: **sixty seconds**.

That's the budget between the camera shutter closing and the pipeline publishing an alert for everything that changed in the frame. Not a marketing aspiration, a requirement, sitting in the design documents with the same seriousness as any latency contract I've ever had to defend.

The reason is that transients are perishable data. A supernova in its first hours, a kilonova fading over days, a near-Earth asteroid that will be somewhere else tomorrow, the science often lives in how fast *other* telescopes can swing toward the coordinates. The photons don't wait for a batch window. So Rubin runs what any of us would recognize as a real-time service with a hard SLO, and the operations team held the launch until uptime, throughput and calibration cleared the bar. That's not "like" production discipline. That *is* production discipline, with the universe as the upstream dependency.

## `git diff` against yesterday's sky

How do you find what changed in a 3.2-gigapixel image? You subtract.

The technique is called Difference Image Analysis. Take tonight's frame, align it against a *template*, a deep reference image built by stacking previous visits to the same field, and subtract one from the other. Every star and galaxy that didn't change cancels out. What survives the subtraction is either something that moved, brightened, appeared... or an artifact.

The sky is the repository. Every visit is a commit. The science lives in the diff.

(I'm compressing brutally here: "align and subtract" hides some genuinely hard signal processing, the atmosphere blurs every exposure differently, so the pipeline has to match the point-spread functions before subtracting. The concept is a diff; the implementation is a career.)

Each image yields on the order of 10,000 detections. Which brings us to the part of this system I love most.

## Kafka under the stars

Every detection becomes an alert: a structured **Avro** packet - IDs, coordinates, fluxes, the light-curve history, small image cutouts - published to **Apache Kafka**.

Yes, that Kafka. The same broker technology carrying your clickstreams and your application logs is carrying the sky. At design cadence, ~10,000 alerts per image times ~1,000 images works out to about **ten million alerts per night**, roughly 115 messages per second, sustained, every clear night, for a decade. In these first weeks the system is already pushing seven million a night.

No human being consumes that. Nobody's inbox survives contact with the universe. So Rubin distributes the raw stream only to **community alert brokers** - seven systems approved for the full firehose: Fink, ALeRCE, ANTARES, Lasair, AMPEL, Pitt-Google, BABAMUL. Look at what a broker actually does and tell me this isn't the alert management we practice on our own systems:

- **cross-matching** each detection against archival catalogs — deduplication and enrichment;
- **machine-learning classification** — triage;
- **user-defined filters** — Lasair literally lets astronomers write SQL against the live stream — routing rules;
- **redistribution** through APIs, watchlists, downstream Kafka topics, and yes, notifications straight into Slack.

Follow that chain to its end: a star explodes in a galaxy millions of light-years away, and within about a minute of the photons landing in Chile, the event can surface as a Slack ping in some research group's channel. Someone, somewhere, is effectively on-call for the universe. Astronomy has industrialized alert triage at a scale that would humble most SOCs, and it solved it with exactly the toolbox we use for microservices, because at ten million events a night it's exactly the same problem: signal versus noise, latency versus completeness, and who gets woken up.

[![Diagram: the LSST alert pipeline read as infrastructure — a photon hits the 8.4 m mirror, difference imaging diffs tonight's sky against a template, each detection becomes an Avro packet on a Kafka topic, seven community brokers cross-match, ML-classify, filter and route, all within a 60-second SLO](/assets/img/lsst-alert-pipeline.svg)](/assets/img/lsst-alert-pipeline.svg)

*From photon to notification in sixty seconds. Click for full resolution.*

## A Lambda architecture, pointed at the sky

The second thing an infrastructure eye catches: there are two processing planes.

**Prompt processing** is the sixty-second path, the alert stream, plus a prompt products database you can query within 24 hours. **Data Release processing** is the other plane: every year, the project reprocesses *everything* from scratch — every image since night one, with the best calibrations and the latest pipeline code — to produce deep, internally consistent catalogs.

A speed layer for freshness. A batch layer for truth. I first met this pattern in a big-data course, as a textbook diagram with Nathan Marz's name attached: the **Lambda architecture**. It is one thing to see it in a slide deck. It is another to find it bolted to a mountain, pointed at the sky.

And that annual full reprocess is quietly the most radical guarantee in the whole system: the pipelines are versioned code, and given the raw photons plus the configuration, the science can be re-derived. What infrastructure-as-code promises our datacenters — state you can rebuild from source — modern astronomy simply requires. The catalog of the universe, reproducible on demand.

## ML is load-bearing

At ten million alerts a night, there is no human in the first-level loop. Machine learning sits in the hot path, and not as decoration.

First, real/bogus separation: models deciding whether a residual in the difference image is astrophysics or an artifact. Then, downstream at the brokers, classifiers assigning probabilities across a whole taxonomy, supernova? variable star? active galactic nucleus? asteroid? From light curves and engineered features, in near-real time. Fink describes its pipeline in terms of feature engineering and ML modules; ALeRCE's core product is curated classification probabilities across that taxonomy.

This is ML with a latency budget, uptime expectations, and drift to watch — the instrument ages, the sky does not hold its class balance constant, and a silently degrading classifier doesn't throw an exception; it just quietly drowns real supernovae in noise. Model monitoring, where the cost of failure is missed physics.

People occasionally ask why someone who has spent his whole career in infrastructure is spending his evenings learning machine learning. From now on I'll just point at Cerro Pachón: because ML stopped being a research artifact and became infrastructure, a load-bearing wall in the largest scientific instrument ever aimed at the night sky.

## You can touch this

Maybe the best part: the alerts are world-public. The brokers expose portals, Python clients, APIs and their own Kafka streams that anyone can subscribe to. Fink will literally hand you a topic. People have already wired broker streams into Spark Structured Streaming and Delta tables and built live supernova monitors on Databricks, the very stack I babysit at my day job, pointed at exploding stars instead of business events. As weekend-project bait goes, it doesn't get much better.

And the system works. During six weeks of optimization runs before the official start, Rubin found more than 11,000 previously unknown asteroids, including 33 near-Earth objects and 380 trans-Neptunian ones. That was the *smoke test*.

---

Here is the part I keep returning to.

A photon leaves a dying star millions of years before there is anyone here to care. It crosses intergalactic space, falls through the atmosphere above Cerro Pachón, lands on an 8.4-metre mirror, becomes a charge in a CCD, a residual in a difference image, an Avro record in a Kafka topic, a probability in a classifier, a row in a database and sometimes, a notification that wakes an astronomer. The last sixty seconds of a journey that long run through the same tools some of us have spent our careers operating.

I used to keep infrastructure work and looking at the night sky in separate compartments. Rubin just closed that gap for good. *Keeping watch*, it turns out, is the same verb whether the system under your care is a power grid or the sky. We built a machine that never blinks, put it on-call for the universe, and gave it a ten-year rotation.

Somewhere above Chile tonight, the shutter is closing every forty seconds, The diff is running!

**The Rubin Observatory**

[![rubinobservatory](/assets/img/RubinObs.jpg)](/assets/img/RubinObs.jpg)

**The Rubin Data Flow**

[![rubindata](/assets/img/RubinData.jpg)](/assets/img/RubinData.jpg)

---

**Further reading**

- [Rubin Observatory, the June 30, 2026 survey-start announcement](https://rubinobservatory.org/news/action-rubin-lsst-begins)
- [The Legacy Survey of Space and Time, explained](https://rubinobservatory.org/explore/how-rubin-works/lsst)
- [How the alert stream works](https://rubinobservatory.org/explore/how-rubin-works/alerts) and [the community brokers](https://rubinobservatory.org/for-scientists/data-products/alerts-and-brokers)
- [Sample Avro alert packets on GitHub](https://github.com/lsst-dm/sample_alert_info) - if you want to `fastavro` your way through the sky
- [A live Rubin alert monitor built on Databricks](https://medium.com/@maksim.nikiforov/chasing-supernovae-in-real-time-building-a-live-rubin-observatory-alert-monitor-on-databricks-cb3cf89b22d8) (Maksim Nikiforov)
- [Rubin alert leads to first follow up observations and detection of four supernovae](https://www.universetoday.com/articles/rubin-alert-leads-to-first-follow-up-observations-and-detection-of-four-supernovae)
- Ivezić et al., *LSST: From Science Drivers to Reference Design and Anticipated Data Products*, ApJ 873, 111 (2019), the reference paper
