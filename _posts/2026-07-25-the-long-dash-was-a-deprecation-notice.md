---
layout: post
title: "The Long Dash Was a Deprecation Notice"
date: 2026-07-25 20:00:00 -0400
tags: [metrology, time, infrastructure, engineering]
description: "Canada switched off CHU on 22 June 2026. No instrument on Earth outputs UTC: the authoritative value is a monthly PDF, published weeks in arrears."
image: /assets/img/long-dash-og.jpg
---
## The Last Thirty-Six Seconds

On 22 June 2026 someone in Cleveland, Ohio pointed a receiver at 7.850 MHz and pressed record. The file runs thirty-six seconds and occupies 8.78 megabytes, credited to a user called Therealrak at Case Western Reserve University and published under a CC BY 4.0 licence. It is, so far as I can establish, the archival record of the end of Canada's spoken time signal on the air.

<figure>
<audio controls preload="none" src="/assets/audio/chu-canada-terminal-broadcast.wav">
Your browser will not play this file. You can <a href="/assets/audio/chu-canada-terminal-broadcast.wav">download the recording</a> instead.
</audio>
<figcaption>CHU's terminal broadcast, received on 7.850 MHz in Cleveland, Ohio, 22 June 2026, recorded by Therealrak. Served from a local copy, because this post is about exactly that; the original lives on <a href="https://en.wikipedia.org/wiki/File:CHU_Canada_terminal_broadcast.wav">Wikimedia Commons</a>. Licensed CC BY 4.0.</figcaption>
</figure>

I was not listening, and I did not know it was happening. I found out weeks late, from a mailing list, in the flat register mailing lists reserve for things that are already over. No transcription of the final words has been published.

The station was [CHU](<https://en.wikipedia.org/wiki/CHU_(radio_station)>). Its final configuration was three frequencies at three powers: 3330 kHz at 3 kW, 7850 kHz at 5 kW, 14670 kHz at 3 kW. The transmitter site was a field near Barrhaven, Ontario, about fifteen kilometres southwest of downtown Ottawa. As of 2020 there were three atomic clocks at the station itself, in a special enclosure built to eliminate possible electromagnetic interference, compared against the atomic clocks at NRC headquarters. Three atomic clocks in a shielded room in a field settled their disagreements with each other and with Ottawa, and the result went out loud, in two languages, to anybody with an antenna. The last announcement went out at 10:10 EDT, which is 14:10 UTC. The NRC notice said the station would close on 22 June 2026 "after more than a century of operation," and gave no technical rationale. Nothing replaced it.

Two things died here, and they are not the same thing. The long dash in my title stopped on 9 October 2023. CHU, the shortwave station in the field, stopped on 22 June 2026.

CHU distributed NRC's time, and the label on the tin said UTC. UTC on 22 June 2026 did not exist on 22 June 2026, and I can show you the PDF that proves it, along with the fact that the day itself is not in it.

## A Station Older Than Its Own Unit

Read CHU's history as a decommissioning record and it stops being a heritage plaque. It becomes the log of a system migrated in place, layer by layer, for a century, without ever going down.

It began in 1923 as an experimental station with the call sign 9CC, run by the Dominion Observatory in Ottawa. Regular daytime transmission started in January 1929 as VE9OB, on about 40.8 metres, which is 7.353 MHz. The call sign became CHU in 1938, on 3.33, 7.335 and 14.67 MHz, with a transmitter power of ten watts. That is ten watts for a national time service.

The seconds pulses were originally derived from pendulum clocks, with quartz crystal control arriving in 1933. Voice announcements were added in 1952 using a French-made speaking clock, replaced in 1960 by an Audichron unit. From 1964 the station was bilingual, with English announcements by Harry Mannis and French by Miville Couture, both of CBC Montreal, and Morse code station identification on the hour. By 1978 every part of the transmitted signal derived from an NRC-designed caesium beam frequency standard.

Then, effective 1 January 2009, 7.335 MHz became 7.85 MHz. That was not an improvement. ITU reallocations arising from WRC-03 prioritised broadcasting use of the band, so the time station moved. It is a small administrative fact with a large meaning: when something more commercially urgent wants the band, the time signal is the thing that yields.

The thing on the air in June 2026 shared almost no hardware with the thing that went on the air in 1923, and a listener from 1938 would still have known exactly what they were hearing.

Including the unit, and I will say this part once. CHU went on the air in 1923, when the second was still a fraction of the rotation of the Earth. In 1967 the 13th CGPM redefined it as "the duration of 9192631770 periods of the radiation corresponding to the transition between the two hyperfine levels of the ground state of the caesium 133 atom," choosing that number to match the existing ephemeris second within the measurement precision then available. The station outlived the redefinition of the very unit it existed to distribute.

## The One Everybody Heard, and the Buffer That Killed It

Most Canadians never owned a shortwave receiver, so CHU is not what they remember. They remember the long dash, a different artifact with a different cause of death.

The National Research Council time signal ran from 5 November 1939 to its final broadcast on 9 October 2023: over eighty-four years, which made it Canada's longest-running radio programme. It aired daily on CBC Radio One shortly before one o'clock Eastern, occupied anywhere from fifteen to sixty seconds, and ended precisely at 13:00. That variable duration tells you it was not a segment with a length but a reservation held open until the instant it existed to mark. The signal was a series of 300 millisecond pips of an 800 Hz sine wave tone, then silence, then a final one-second tone. The English wording was fixed: "The National Research Council official time signal. The beginning of the long dash indicates exactly one o'clock, Eastern Standard Time." Daylight Saving Time was substituted when it applied. Lorne Greene was among the programme's earliest announcers, when he was working at CBC station CBO.

It did not end because the clocks got worse. It ended for accuracy reasons instead. HD Radio transmitters introduced delays of up to nine seconds, and CBC's distribution had multiplied into multiple paths, each with its own latency, so there was no longer any way to guarantee that the leading edge of that final tone reached a given listener at 13:00:00.

You cannot broadcast a timestamp through a pipeline that queues.

This was a buffering problem. Not a metrology problem, not a funding problem, not obsolescence. We have all shipped that bug, and when we ship it we fix the pipeline, because the pipeline is ours. Here the payload was a national institution and the pipeline was the whole Canadian broadcast plant, correctly optimised for reach and resilience, so the institution was retired instead.

Shortwave has one property those paths lack. The delay from a transmitter in a field to a receiver on a desk is a property of the physical path. It varies and you do not know it, but it does not depend on which cache tier answered, and it cannot be nine seconds. That is a low bar. The modern stack failed to clear it.

## One O'Clock, at the Table

My father, Vincenzo D'Apice, was born in 1937, the year before the call sign CHU came into use. The long dash began on 5 November 1939. He died on 8 August 2022, and the long dash ended on 9 October 2023, so the signal outlived him by about fourteen months.

For most of my life there was a family lunch every week. Italian, long, loud, and a radio on because there was always a radio on. Shortly before one o'clock the announcer said his piece, the pips ran, and the long tone landed underneath the conversation. I have written about him here once before, in [A Star for My Father](/blog/2026/07/a-star-for-my-father/), and I am not going to do it twice.

Nothing in that house was ever set because of that signal. I do not think the possibility occurred to anyone in decades of hearing it.

The value of that signal was not accuracy. It was never accuracy. Its value was that everyone heard it at the same moment. That is precisely the property that got deprecated.

## Nobody Has UTC

There is no instrument on Earth that outputs UTC.

Not at NRC, not at NIST, not at the BIPM. There is no rack, no oven, no output connector anywhere from which coordinated universal time itself emerges. UTC is a paper time scale, and the standard phrasing is that it is "only known with the highest precision in retrospect." What physically exists are the local realisations, UTC(k), each an ensemble of real clocks producing real ticks, maintained by a national institute. Canada's is UTC(NRC), and UTC(NRC) is Canada's legal time. It is not a copy of Canada's legal time but the thing itself, and it is also not UTC.

The reconciliation happens at the Bureau International des Poids et Mesures, which takes clock and comparison data from roughly eighty institutes and publishes Circular T monthly, giving [UTC - UTC(k)] at five-day intervals for each participating laboratory. Circular T 457 lists about seventy laboratories in its section 1 table. That publication is the authoritative statement of what time it was. It is a table of numbers, in a PDF, and it comes out after the fact.

This is the row for Canada in the circular that covers June.

```
BIPM Circular T No. 462     published 2026 July 10, 11h UTC
period covered: 2026 May 29 - 2026 June 28   (MJD 61189 - 61219)

[UTC - UTC(NRC)], in nanoseconds

    MAY 29   (MJD 61189)     1.8
    JUN  3   (MJD 61194)     2.5
    JUN  8   (MJD 61199)     2.5
    JUN 13   (MJD 61204)     2.0
    JUN 18   (MJD 61209)     1.3
    JUN 23   (MJD 61214)     0.6
    JUN 28   (MJD 61219)     0.2

    uA = 0.2 ns     uB = 2.8 ns     combined u = 2.8 ns
```

Read the dates down the left side. The sampling is five days wide. It lands on 18 June, and then on 23 June.

CHU went silent on 22 June.

The day Canada stopped saying the time out loud is not a row in the record of Canadian time. If you want to know how far UTC(NRC) stood from UTC at 14:10 UTC on 22 June 2026, at the moment of the last announcement, the answer is not written down anywhere. You interpolate it, between 1.3 nanoseconds on the eighteenth and 0.6 nanoseconds on the twenty-third, and you carry the uncertainty of that interpolation yourself. And the document that brackets the day was not published until 10 July 2026, eighteen days after the transmitter went quiet. Every clock you own or administer is a cache with an unknown error, and this is the origin server: monthly, in arrears, as a PDF, with no invalidation signal and no plan to add one.

Now the part that keeps this honest. The lag is designed in rather than a failure, and the numbers themselves are magnificent. Across an entire month UTC(NRC) sat within about two and a half nanoseconds of UTC, and over the second half of that month it closed steadily, reaching 0.2 nanoseconds by 28 June. The statistical uncertainty uA is 0.2 ns while the systematic uncertainty uB of 2.8 ns dominates the combined u, which tells you the residual doubt about Canadian time is not noise in Canada's clocks. Canada's time scale is not the weak link in anything. It is one of the finest things the country maintains, and it was getting better while the last way of hearing it was switched off. Accuracy was never what was lost.

## The Walk Nobody Asked Me to Make

So I walked the chain outward from a machine I own.

Run `chronyc tracking`. It reports the reference ID and name of the source you are actually locked to, which is not always the one you configured, plus the stratum, the last and RMS offsets, and the frequency and skew of the local oscillator. Then it reports the two fields that carry the whole argument: root delay and root dispersion. Root delay is the total network path delay to the stratum-1 at the head of my particular tree. Root dispersion is the accumulated error estimate along that same path. Together they bound the maximum error, and the interesting question about that bound is what it is a bound against.

It is a bound relative to the reference clock at the head of my chain. It is not relative to UTC. There is no field for that on any machine I have ever administered, and there could not be one. Chrony is not overstating anything; it is being scrupulous about a local quantity, and I have watched capable engineers read those numbers as an accuracy figure against official time. My own numbers are unremarkable, which is why I am not pasting them. Run it on a machine you administer and read those two fields, because they are the only honest ones on the screen.

The hops go like this. My server trusts a stratum-1, over a network whose asymmetry I have never measured. That stratum-1 traces to a national laboratory by whatever arrangement its operator actually maintains, which I take on trust. If the laboratory is Canadian, it traces to UTC(NRC), a physical ensemble whose offset from UTC is a quantity somebody else computes. That offset is sampled at five-day intervals, so the nearest published value sits days away from the moment I care about, and the document carrying it arrives weeks after the month it describes.

The interval widens at every hop, and so does the unit. The tightest hop in the chain is measured in single-digit nanoseconds, and it is the one I contribute nothing to. The last hop is measured in weeks, not because anyone is careless, but because the definition of the quantity requires it. Nothing on the machine models that last gap, and an alert on it would not be actionable, because the information it wants does not exist yet.

Which brings me to the admission this post is really built on. In more than twenty-five years of operations, nobody has ever asked me to prove traceability back to Ottawa. Not once. I have configured NTP and then chrony on more machines than I can count, in more environments than I can remember, and no one has ever asked me the obvious question: traceable to what, exactly. Nobody has asked me to produce a Circular T, or to name the laboratory at the head of the chain, or to say how stale the last authoritative comparison was. Everybody wants the clocks to agree. Nobody wants the provenance. I made this walk because the question occurred to me one evening, which is the only reason anyone ever makes it.

The chain is not broken. It is real, it is walkable, and it is documented to a standard most of our infrastructure would envy. The destination is simply this: "traceable to UTC" is a claim about a document that does not exist yet.

## What Is Still on the Air

I do not want to overstate the funeral, so here is the inventory.

NRC's telephone talking clock still answers, at 613-745-1576 in English and 613-745-9426 in French. Note what it is, though. It is not a broadcast. It is a unicast fetch with a voice, one caller at a time.

Across the border WWV is still transmitting from Fort Collins, Colorado, on 2.5 MHz and 20 MHz at 2.5 kW ERP and on 5, 10 and 15 MHz at 10 kW ERP, and its sister station WWVH on Kauai carries the same frequencies. WWV's broadcast time is accurate to within 100 nanoseconds of UTC and 20 nanoseconds of the national time standard, and that specification describes the signal leaving the transmitter. It says nothing about the instant the tick reaches your antenna, and people quote it as though it did. WWVB is still on 60 kHz with a carrier frequency accuracy of one part in 10<sup>14</sup>, quietly driving the radio-controlled clocks of North America. In 2019 all three stations were recommended for defunding and elimination in NIST's Fiscal Year 2019 budget request; the final 2019 NIST budget preserved the funding for all three. They are on the air because of a line item.

Radio time is not dead. Canada's is, and it was not replaced. NRC now relies on NTP, its web clock and that telephone number, and it publishes no accuracy specification for either the web clock or the NTP service. That absence is the shape of the new interface: you fetch, you are given a value, and no bound is stated, because nobody asks for one.

The unit itself is also in play. There have been 27 leap seconds since 1972, all positive, most recently on 31 December 2016, and TAI minus UTC has been frozen at 37 seconds ever since. The 30 June 2012 leap second produced outages at Reddit through Apache Cassandra, at Mozilla through Hadoop, at Qantas, and across an assortment of sites running Linux. A discontinuity in the time scale is a discontinuity in production. A negative leap second has not yet become necessary partly because, as Agnew showed in Nature in April 2024, water from increasing ice cap melt migrates toward the equator and slows the rotation back down. CGPM Resolution 4, adopted 18 November 2022, calls for increasing the maximum permitted difference between UT1 and UTC "in, or before, 2035," with a plan ensuring the continuity of UTC for at least a century, and Resolution 5 concerns the future redefinition of the second. The 28th CGPM meets from 13 to 15 October 2026. I am publishing before the vote and I am not going to guess at it.

The class of thing retired in June was not a frequency and not a clock. It was an interface that broadcasts to consumers it cannot enumerate. CHU had no idea who was listening and did not need to know: no handshake, no subscription, no per-client state, no way to tell whether a single receiver was tuned in. By every standard I would apply at work that is an appalling interface, and it had one property no unicast fetch can reproduce. Everyone got the same value at the same instant, and everyone knew everyone else had it too. What replaced it is better by every measure I can put a number on. More accurate, individually fetched, silently cached, and believed without inspection.

It stopped arriving everywhere at once in 2023, and in June a transmitter in a field southwest of Ottawa stopped doing it too. Every machine I run keeps better time than that radio ever delivered. Not one of them says it out loud.
