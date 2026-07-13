---
layout: post
title: "The Oldest System in Production"
date: 2026-07-13 21:00:00 -0400
tags: [astronomy, dataops, engineering]
description: "Forty-nine years of uptime, 23 watts of transmit power, a 45-hour deploy loop, and a risky change window scheduled for this month. Voyager 1, read with infrastructure eyes."
---

Two days ago I wrote about [the newest system in production](/blog/2026/07/the-universe-just-went-to-production/): the Vera C. Rubin Observatory, ten million alerts a night, a 60-second SLO, Kafka under the stars. Tonight I want to look at the other end of the spectrum.

The oldest system in production is not a mainframe in a bank basement. It is not that COBOL batch job nobody dares to touch. It is an 825-kilogram spacecraft launched on September 5, 1977, currently about 25.8 billion kilometres from Earth, moving away at 17 kilometres per second, running on computers with less total memory than a single one of Rubin's alert packets.

Voyager 1 has been in continuous operation for forty-eight years and ten months. It is still taking commands. It is still shipping telemetry. And this very month, July 2026, its operators are attempting one of the riskiest changes in the system's history.

If you have ever kept an old system alive because it was still doing something no other system could do, this story is for you.

---

## The spec sheet nobody would sign today

Start with the hardware, because the numbers are absurd in the opposite direction from Rubin's.

Voyager 1 carries three pairs of computers — command, flight data, attitude control — with a combined memory of roughly 68 kilobytes. Not gigabytes. Not megabytes. Kilobytes. For comparison: a single Avro alert packet from the Rubin pipeline, with its image cutouts, runs around 80 KB. One message from the newest system in production would not fit in the entire memory of the oldest.

The radio transmitter emits about 23 watts, the power of a refrigerator light bulb. By the time that signal has spread across 25.8 billion kilometres, the Deep Space Network's 70-metre dishes are fishing attowatts out of the noise. Telemetry comes down at 160 bits per second. Not megabits. Bits. A rate at which this blog post would take about ten minutes to download.

Electricity comes from three radioisotope thermoelectric generators: slugs of plutonium-238 whose decay heat is converted into current. No solar panels work out there, the Sun is just the brightest star in the sky. The RTGs produced 470 watts at launch and have been fading ever since, in the most predictable capacity decline any engineer has ever had to plan around: about **4 watts per year**, every year, forever, dictated not by load or budget but by the half-life of plutonium. There is no procurement process that gets you more. The power budget only goes down.

Nobody would sign this spec sheet today. And yet: forty-eight years of uptime.

## The incident: garbage on the wire

In November 2023, Voyager 1 stopped making sense.

The spacecraft was still alive, still receiving commands, still transmitting a carrier, but the telemetry had turned to gibberish. A repeating, unreadable pattern where science and engineering data should have been. Anyone who has stared at a corrupted log stream at 3 a.m. knows that exact feeling, except here the "log stream" was arriving from interstellar space and every diagnostic round-trip took **45 hours**: 22.5 hours for the command to arrive at light speed, 22.5 hours for the answer to come back.

Think about that feedback loop for a second. Every hypothesis you test costs you two days. There is no SSH. There is no console. There is no "have you tried turning it off and on again", because if it goes off out there, in the cold, it may never come back on.

The team at JPL spent months on root cause analysis and finally traced the fault to the Flight Data Subsystem: a single failed memory chip had taken out about **3% of the FDS memory**, including a portion of the code. The hardware was unfixable by definition. The only option was software: take the code that lived on the dead chip, break it into pieces, relocate the pieces into free corners of the surviving memory, and rewrite every cross-reference so that the fragments still executed as one program.

Now add the constraints. The code is 1970s assembly. The original development environment is gone. There is no testbed, no emulator, no staging spacecraft. The engineers who wrote it have long since retired, some have passed away; part of the institutional memory exists as paper documents in boxes. Verification was done the only way left: **by inspection**. Humans reading assembly, line by line, convincing themselves it was correct, because the first real test would be production.

The patch was uplinked on April 18, 2024. Then everyone waited 45 hours. On April 20, coherent engineering telemetry resumed, and by June the science instruments were back online.

I have sat through my share of tense deploys. I have never signed off on a change that could not be tested at all, targeting hardware nobody has been able to touch since before I was in school, with a two-day wait to learn whether I had just killed the only interstellar data source humanity has. We talk a lot about "confidence in the change process". This is the ceiling of that scale.

## The rollback that could have exploded

It gets better. In 2025, the team performed what I can only describe as the most dangerous rollback in the history of operations.

Voyager 1 keeps its antenna pointed at Earth using small thrusters. The primary roll thrusters had been written off as dead **since 2004**, twenty-one years, when their catalyst-bed heaters lost power. The mission had been running on the backups ever since. But by 2025 the backup thrusters were slowly clogging with propellant residue and might fail within months. Losing attitude control means losing the antenna lock on Earth. Losing the antenna lock means silence, permanent.

So the engineers went back to a two-decades-old failure and re-litigated the diagnosis. Their new theory: the heaters had never actually broken; a disturbance in the power supply circuits had effectively flipped a switch to the wrong position. If they were right, the "dead" thrusters could be revived. If they were wrong, and the thrusters fired while frozen cold, the mission documentation used the word *explosion*.

There was also a deadline, and it is the most relatable detail in the whole story: a **maintenance window**. Deep Space Station 43 in Canberra, the only antenna on Earth powerful enough to send commands to Voyager, was about to go offline for upgrades from May 2025 to February 2026. Whatever fix was going to happen had to happen before the ops team lost their uplink.

On March 20, 2025, the command sequence arrived, the heaters warmed up, and thrusters that had been considered dead for twenty-one years fired. The failover path was restored before the maintenance window closed the door.

Re-reading a twenty-year-old post-mortem, discovering the root cause was wrong, and un-failing the hardware with a config change. Every ops engineer knows a smaller version of that story. This one just happened 25 billion kilometres away, with an explosion clause.

## Load shedding, four watts at a time

Meanwhile, the power budget keeps doing the only thing it knows how to do.

Voyager 1 launched with ten science instruments. The team has been shutting them down one by one for years — not because they failed, but to keep the heaters running and the remaining instruments alive. It is load shedding in its purest form: every year the RTGs give you four watts less, and every few years that arithmetic forces you to choose which observation humanity stops making, forever. The cosmic ray subsystem was switched off in February 2025 after 47 years of operation. This April, the Low-Energy Charged Particles instrument followed, after almost 49 years of near-continuous service.

Read that again the way we would write it in a decommission ticket: *service LECP retired after 49 years of operation; no successor system exists; data collection at this position in space will not resume in any currently living human's lifetime.*

Two instruments remain: the magnetometer and the plasma wave subsystem, still measuring the interstellar medium, still the only in-situ sensors humanity has ever placed outside the Sun's bubble. Current projections say the RTGs can support engineering data until around 2036.

## The Big Bang: a canary deploy, 49 years in

Which brings us to this month.

Rather than keep amputating instruments, the Voyager team has designed a manoeuvre they nicknamed the **Big Bang**: switch off a whole group of powered devices at once and bring up lower-power alternatives in their place, rebalancing the entire electrical and thermal budget in one coordinated change. If it works, it buys at least a year before the next shutdown, and might even allow the instrument turned off in April to be powered back on.

And here is the part that made me smile in recognition: they are not trying it on Voyager 1 first. Voyager 2, which has a little more power margin and sits a little closer to Earth, ran the change first, in May and June. If the results hold, Voyager 1 gets the same change in **July 2026**.

That is a canary deploy. A staged rollout with the healthier node first, on a distributed system whose two nodes are tens of billions of kilometres from the operators, and from each other. The practice we apply every week to stateless microservices, applied to the two most remote machines ever built, because it is simply what careful operations looks like, at any scale, at any distance.

Somewhere at JPL right now, someone is watching 160 bits per second of telemetry and deciding whether to proceed. I hope their change ticket gets approved. I have never meant that sentence more sincerely.

[![Diagram: the Voyager 1 operations timeline read as infrastructure — launch in 1977, Pale Blue Dot in 1990, roll thrusters written off in 2004, interstellar space in 2012, then a zoom on the busy years 2023–2026: the memory-chip incident and its patch, the 21-year thruster rollback, load shedding, the Big Bang canary, and the one-light-day milestone of November 2026](/assets/img/voyager-ops-timeline.svg)](/assets/img/voyager-ops-timeline.svg)

*Forty-nine years of uptime, read as a change log. Click for full resolution.*

---

## What actually keeps a system alive

Here is what Voyager 1 has taught me, and it is not really about space.

The hardware was never the point. The hardware is 1970s silicon with 68 KB of memory and a failing chip. What has kept this system in production for forty-nine years is everything we file under "boring": redundant design and graceful degradation, telemetry rich enough to debug a fault from one solar system away, documentation that survived longer than its authors' careers, and above all an unbroken chain of people willing to learn a dying assembly language to keep a promise made before many of them were born.

Every legacy system I have ever babysat, I have at some point resented. The undocumented job, the config nobody understands, the machine that cannot be patched. Voyager reframes all of it. Legacy is not the code that time forgot. Legacy is the system that outlived its creators *because it kept being worth saving*. The Voyager engineers are not stuck maintaining an old spacecraft. They are custodians of the farthest thing human hands have ever built, and they treat a 45-hour ping like a privilege.

On November 18, 2026, at 2:16 a.m. Pacific time, Voyager 1 will cross a threshold no machine has ever crossed: it will be **one full light-day** from Earth. A command sent that morning will take twenty-four hours to arrive. The spacecraft will spend that entire day flying on trust, doing exactly what it was last told, the way it has every day since 1977.

Rubin watches the sky and never blinks. Voyager left, and never looked back, except once, in 1990, to take a picture of a pale blue dot.

Both are in production. Both are on-call rotations that someone, tonight, is quietly honouring. The newest system we have and the oldest one are running the same playbook: watch the telemetry, respect the power budget, test on the canary, and keep the signal alive.

Forty-nine years of uptime. The diff is still running.

**Voyager 1, alone in interstellar space** *(artist's concept, NASA/JPL-Caltech)*

[![Artist's concept of Voyager 1 in interstellar space, its white high-gain dish antenna pointed back toward a distant Sun](https://photojournal.jpl.nasa.gov/jpeg/PIA17462.jpg)](https://photojournal.jpl.nasa.gov/catalog/PIA17462)

**The Pale Blue Dot** *(1990, reprocessed in 2020, NASA/JPL-Caltech)*

[![The Pale Blue Dot: Earth as a fraction of a pixel caught in a scattered ray of sunlight, photographed by Voyager 1 from 6 billion kilometres away](https://photojournal.jpl.nasa.gov/jpeg/PIA23645.jpg)](https://photojournal.jpl.nasa.gov/catalog/PIA23645)

---

**Further reading**

- [NASA's Voyager 1 Resumes Sending Engineering Updates to Earth](https://www.jpl.nasa.gov/news/nasas-voyager-1-resumes-sending-engineering-updates-to-earth/) — the FDS memory patch, April 2024
- [Engineers Pinpoint Cause of Voyager 1 Issue](https://science.nasa.gov/blogs/voyager/2024/04/04/engineers-pinpoint-cause-of-voyager-1-issue-are-working-on-solution/) — the root cause analysis, in NASA's own words
- [NASA's Voyager 1 Revives Backup Thrusters Before Command Pause](https://www.jpl.nasa.gov/news/nasas-voyager-1-revives-backup-thrusters-before-command-pause/) — the 2025 thruster resurrection
- [NASA Shuts Off Instrument on Voyager 1 to Keep Spacecraft Operating](https://science.nasa.gov/blogs/voyager/2026/04/17/nasa-shuts-off-instrument-on-voyager-1-to-keep-spacecraft-operating/) — the LECP shutdown, April 2026
- [Voyager 1 shuts off instrument to buy time before 'Big Bang' fix](https://www.cnn.com/2026/04/27/science/voyager-1-big-bang) — the power-swap manoeuvre and its canary rollout
- [Voyager 1 — Wikipedia](https://en.wikipedia.org/wiki/Voyager_1) — distances, instrument timeline, and the road to one light-day
