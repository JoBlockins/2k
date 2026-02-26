# Project Overview: 2K Erg Training AI Agent

## Athlete Profile

| Field | Value |
|---|---|
| **Name** | Joshua Dockins |
| **Category** | Men's Lightweight |
| **Weight** | 160 lbs (72.6 kg) |
| **Current 2k Time** | 6:50 |
| **Goal 2k Time** | Sub-6:30 |
| **Timeline** | February 2026 -- August 2026 (~6 months) |
| **Target Event** | August 2026 Tryouts |

---

## Timeline

The training window runs from **February 2026 through August 2026**, roughly six months of structured preparation. This timeline is divided into four macro-phases:

1. **Base 1 (Feb -- Mar):** Aerobic foundation building, high volume at low intensity.
2. **Base 2 (Apr -- May):** Continued aerobic development with introduction of tempo work.
3. **Build (Jun -- Jul):** Threshold and race-pace training, shift toward intensity.
4. **Peak & Taper (Late Jul -- Aug):** Race simulation, volume reduction, performance sharpening.

The final 2k test at August 2026 tryouts is the singular, non-negotiable target of the entire program.

---

## What "Sub-6:30" Means in Rowing Terms

A 2,000-meter ergometer test under 6 minutes and 30 seconds demands:

- **Average 500m split:** ~1:37.5 per 500 meters
- **Average power output:** ~235 watts sustained for the full piece
- **Stroke rate:** Typically 30--36 strokes per minute during a 2k race effort
- **Duration:** Roughly 6:28--6:29 at the target, with a margin of no more than 1--2 seconds

For context, 6:30 sits in the competitive range for men's lightweight rowing at the collegiate and club level. The improvement from 6:50 to 6:30 represents a 20-second drop, which translates to roughly a 5% improvement in split time and approximately a 15% increase in average wattage (from ~202W to ~235W). This is a substantial but achievable gain over a six-month window with structured training.

### The Split-Watts Relationship

Rowing power follows a cubic relationship:

```
watts = 2.80 / pace^3
```

Where `pace` is the 500m split expressed in seconds. This means small improvements in split require disproportionately larger increases in power output. Going from 1:42.5 (6:50 pace) to 1:37.5 (6:30 pace) requires roughly 33 additional watts of sustained output.

---

## Why AI Coaching

Traditional coaching relies on periodic check-ins, subjective feel, and the coach's experience to adjust training plans. This works, but it has gaps:

- **Delayed feedback:** A human coach reviews a week of data at the next meeting. The AI agent processes data daily or after every session.
- **Limited data integration:** A human coach may look at erg splits and body weight. The AI agent ingests heart rate trends, HRV, sleep quality, nutrition logs, wellness scores, and training load metrics simultaneously.
- **Consistency:** The AI agent applies the same analytical framework every single day without fatigue, bias, or forgetfulness.
- **Personalization at scale:** The agent builds a model of this specific athlete's response patterns -- how Joshua recovers, how his splits respond to volume changes, how weight fluctuations affect performance.
- **Predictive capacity:** By tracking the relationship between training inputs and performance outputs over time, the AI agent can project 2k performance and flag when the athlete is on track, ahead, or behind schedule.

The goal is not to replace human coaching entirely but to create a data-driven feedback loop that operates continuously: ingest data, analyze trends, adjust the plan, explain the reasoning, and repeat.

---

## Success Criteria

The project succeeds if all of the following are met at the August 2026 tryouts:

1. **Primary:** Joshua pulls a 2k erg score of **sub-6:30** (6:29.9 or faster).
2. **Weight:** Body weight remains at or below **160 lbs** on race day (lightweight requirement).
3. **Health:** No overtraining injuries or illness that derail the timeline.
4. **Process:** The AI agent demonstrably contributes to training decisions -- plan adjustments, recovery recommendations, pacing strategies -- throughout the six-month block.

Secondary success indicators:

- 6k benchmark improves to the 1:48--1:50 range (predictive of sub-6:30 2k).
- 30-minute test reaches 7,800--8,000 meters.
- Resting heart rate trends downward over the training block.
- HRV trends upward, indicating improved aerobic fitness and recovery capacity.

---

## Device and App Stack

The AI agent draws data from the following sources, forming a comprehensive picture of training, recovery, and readiness:

### Primary Training Device

| Device | Purpose | Data Provided |
|---|---|---|
| **Concept2 PM5 + ErgData** | Erg training | Splits, watts, stroke rate, drive length, distance, drag factor, full stroke data per session |

### Wearables and Health Devices

| Device | Purpose | Data Provided |
|---|---|---|
| **Polar H10** | Chest strap HR monitor | Real-time heart rate during sessions, R-R intervals for HRV |
| **Whoop 4.0** | 24/7 recovery tracking | HRV (RMSSD), resting HR, sleep duration/quality, strain score, recovery score |
| **Withings Body+** | Smart scale | Body weight, body composition trends |

### Software and Apps

| App | Purpose | Data Provided |
|---|---|---|
| **ErgData** (Concept2) | Erg session logging | Syncs PM5 data to Concept2 Logbook; provides API access |
| **MyFitnessPal** | Nutrition tracking | Caloric intake, macronutrient breakdown (protein, carbs, fat) |
| **Apple Health** | Central health hub | Aggregates data from Polar, Whoop, and other sources |

### Data Flow

```
Concept2 PM5 --> ErgData --> Concept2 Logbook API --> AI Agent
Polar H10 --> Polar Flow / Apple Health -----------------> AI Agent
Whoop 4.0 --> Whoop API ---------------------------------> AI Agent
Withings Body+ --> Withings API --------------------------> AI Agent
MyFitnessPal --> CSV Export / API ------------------------> AI Agent
Manual Input (RPE, Wellness) -----------------------------> AI Agent
```

All data flows into the AI agent's data layer, where it is stored, processed, and made available for analysis, plan adjustment, and dashboard visualization.
