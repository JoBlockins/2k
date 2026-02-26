# Training Philosophy

This document lays out the physiological principles and training methodology that guide the AI agent's decision-making. Every recommendation the system makes is rooted in these concepts.

---

## Polarized Training Model (80/20)

The foundational training principle for this program is **polarized training**: roughly 80% of training volume at low intensity and 20% at high intensity, with relatively little time spent in the moderate "gray zone."

### Why Polarized?

Research on elite endurance athletes -- including rowers, cyclists, runners, and cross-country skiers -- consistently shows that polarized intensity distribution produces superior endurance adaptations compared to threshold-heavy or evenly distributed approaches.

The physiological reasoning:

- **Low-intensity work (80%)** develops the aerobic engine: mitochondrial density, capillary density, stroke volume, fat oxidation efficiency, and Type I fiber recruitment. These adaptations are volume-dependent and require many hours at controlled intensities.
- **High-intensity work (20%)** provides the stimulus for VO2max development, lactate buffering capacity, neuromuscular recruitment, and race-specific fitness. These adaptations require intensity that cannot be sustained in high volumes.
- **The gray zone (moderate intensity)** is too hard to accumulate high volume (leading to chronic fatigue) and too easy to produce the sharp stimulus needed for high-end adaptation. It produces mediocre results in both directions.

### Application for Joshua

At 160 lbs targeting sub-6:30, the 80/20 split means:

- **80% of meters** at UT2 (steady state): 1:55-2:05 splits, HR below 75% of max, conversational pace. This is the unglamorous foundation that builds the aerobic base required to sustain ~235 watts for 6:30.
- **20% of meters** at UT1 and above: tempo, threshold, VO2max intervals, and race-pace work. This is where the body learns to tolerate and clear lactate at 1:37.5 splits.

The AI agent monitors weekly zone distribution and flags sessions where the athlete drifted into the gray zone during "easy" sessions. Heart rate is the primary enforcement mechanism.

---

## Periodization: The Six-Month Plan

The six months from February to August 2026 are divided into four macro-phases, each with a distinct physiological focus. The progression moves from high-volume, low-intensity base building to low-volume, high-intensity race sharpening.

### Phase 1: Base 1 (February -- March 2026)

**Goal:** Build the aerobic foundation.

| Parameter | Target |
|---|---|
| Weekly Volume | 70,000 -- 90,000 meters |
| Intensity Split | 80%+ UT2, minimal higher intensity |
| Session Types | Long steady state (60-90 min), occasional UT1 |
| Stroke Rate | 18-22 SPM (low rate, focus on length and efficiency) |
| Split Range | 1:55-2:05 (UT2), 1:50-1:55 (UT1) |
| Strength | 2-3 sessions/week, hypertrophy/foundation phase |
| Key Adaptations | Mitochondrial biogenesis, capillary density, aerobic enzyme activity, movement efficiency |

**Rationale:** The aerobic system is the limiting factor in a 2k. Approximately 70-80% of energy in a 6:30 2k comes from aerobic metabolism. Base 1 builds the engine before asking it to run fast. Rushing past this phase is the most common mistake athletes make.

**Benchmark:** 6k test at end of March. Target: 1:52-1:54 split (predicting ~6:40-6:45 2k). This establishes the baseline and confirms the aerobic work is laying groundwork.

---

### Phase 2: Base 2 (April -- May 2026)

**Goal:** Expand aerobic capacity and introduce tempo work.

| Parameter | Target |
|---|---|
| Weekly Volume | 80,000 -- 100,000 meters (peak volume phase) |
| Intensity Split | 75% UT2, 15% UT1, 10% AT |
| Session Types | Steady state, tempo intervals (20-40 min at UT1), threshold intervals (AT) |
| Stroke Rate | 18-22 (UT2), 22-26 (UT1), 26-30 (AT) |
| Split Range | 1:55-2:05 (UT2), 1:48-1:52 (UT1), 1:42-1:46 (AT) |
| Strength | 2 sessions/week, transition to strength-power phase |
| Key Adaptations | Increased lactate threshold, improved stroke efficiency at tempo, sustained aerobic gains |

**Rationale:** Base 2 is the highest-volume phase. The body can now handle more meters. Tempo work at UT1 pushes the lactate threshold upward without the recovery cost of true interval work. The 75/25 split introduces more intensity while keeping the aerobic focus dominant.

**Benchmark:** 6k test at end of May. Target: 1:49-1:51 split (predicting ~6:33-6:37 2k). This should show meaningful improvement from the March test and confirm the athlete is tracking toward sub-6:30.

---

### Phase 3: Build (June -- July 2026)

**Goal:** Develop threshold capacity and introduce race-pace work.

| Parameter | Target |
|---|---|
| Weekly Volume | 60,000 -- 80,000 meters (volume decreases, intensity increases) |
| Intensity Split | 70% UT2, 15% AT, 10% TR, 5% AN |
| Session Types | Steady state (maintained), threshold intervals (4x2k, 3x3k), VO2max intervals (8x500m, 5x1000m), race-pace pieces |
| Stroke Rate | 18-22 (UT2), 26-30 (AT), 30-34 (TR), 34+ (AN) |
| Split Range | 1:55-2:05 (UT2), 1:42-1:46 (AT), 1:36-1:40 (TR), 1:25-1:32 (AN) |
| Strength | 1-2 sessions/week, maintenance only |
| Key Adaptations | Lactate tolerance, race-pace neuromuscular patterns, pacing confidence, power at high stroke rates |

**Rationale:** The aerobic base is built. Now the body learns to operate at and above the target 2k pace. Threshold intervals teach sustained output at ~1:37.5. VO2max intervals build the top-end capacity that allows the athlete to push through the third 500m of a 2k (the hardest part). Volume drops because high-intensity work demands more recovery.

**Benchmark:** 2k test in early July. Target: 6:32-6:35. This confirms the athlete is within striking distance. If behind, the AI agent adjusts the remaining weeks. 500m test in late June. Target: 1:27-1:28 (confirms sufficient sprint capacity).

---

### Phase 4: Peak & Taper (Late July -- August 2026)

**Goal:** Sharpen race fitness, shed fatigue, arrive at tryouts in peak condition.

| Parameter | Target |
|---|---|
| Weekly Volume | Decreasing: 50k -> 40k -> 30k over final 3 weeks |
| Intensity Split | Reduced volume, maintained or slightly increased intensity per session |
| Session Types | Race simulations (full 2k or 2k-pace 2x1k), short sharp intervals, easy recovery rows |
| Stroke Rate | Race rate (32-36) for hard sessions, 18-20 for recovery |
| Split Range | Race pace 1:37.5 or faster for quality sessions |
| Strength | Minimal or none. Preserve muscle, avoid fatigue. |
| Key Adaptations | Neuromuscular sharpness, psychological confidence, glycogen supercompensation, full recovery from training fatigue |

**Rationale:** The taper is where fitness "comes out." The months of base and build training have created a deep pool of fitness buried under accumulated fatigue. Reducing volume by 40-60% while keeping a few sharp sessions allows the body to fully absorb prior training. Performance typically improves 2-4% during a proper taper.

**Target:** Sub-6:30 at the August 2026 tryouts. The final 10-14 days before race day are critical: the AI agent manages volume reduction, monitors HRV and readiness, and ensures the athlete arrives fresh but sharp.

---

## Rowing-Specific Physiology

### The 6k and 30-Minute Tests as 2k Predictors

In rowing, the 6k test is the gold standard predictor of 2k potential:

- **6k split + 5 to 7 seconds = approximate 2k split.**
- A 1:49 average 6k split predicts a 2k split of approximately 1:42-1:44, but this understates the relationship for well-trained athletes. In practice, a 1:49 6k often correlates with a 1:37-1:39 2k depending on the athlete's anaerobic contribution.

The more accurate model:

- The 6k test measures sustainable aerobic power (roughly VO2max pace).
- The 2k test draws approximately 70-80% aerobic and 20-30% anaerobic.
- The gap between 6k pace and 2k pace reflects the athlete's anaerobic capacity and pain tolerance.
- Tracking this gap over time reveals whether improvement is coming from aerobic gains (6k improving) or anaerobic gains (gap widening).

The 30-minute test serves a similar purpose:

- **30-minute average split maps closely to UT1/AT threshold.**
- Target: 7,800-8,000 meters in 30 minutes (1:55.4-1:52.5 split).
- Improvement in the 30-minute test indicates aerobic development is progressing.

### Energy System Contribution to the 2k

A 6:30 2k effort draws from multiple energy systems:

| System | Contribution | Timeframe |
|---|---|---|
| **Aerobic (oxidative)** | ~70-80% | Sustained throughout, dominant from 60s onward |
| **Anaerobic glycolysis** | ~15-25% | Significant in first 60s and final sprint |
| **Phosphocreatine (PCr)** | ~3-5% | First 10-15 seconds only |

This is why the aerobic base (Phases 1-2) is so critical. The majority of energy for a 2k comes from aerobic metabolism. An athlete with a weak aerobic base cannot sustain sub-6:30 regardless of anaerobic capacity.

---

## The Cubic Relationship: Split and Watts

The relationship between 500m split and watts on the Concept2 erg follows a cubic function:

```
watts = 2.80 / pace^3
```

Where `pace` is the time in seconds to row 500 meters.

### Implications

| Split | Pace (sec) | Watts |
|---|---|---|
| 2:00.0 | 120.0 | ~162 W |
| 1:55.0 | 115.0 | ~184 W |
| 1:50.0 | 110.0 | ~210 W |
| 1:45.0 | 105.0 | ~242 W |
| 1:42.5 | 102.5 | ~260 W |
| 1:40.0 | 100.0 | ~280 W |
| 1:37.5 | 97.5 | ~302 W |
| 1:35.0 | 95.0 | ~327 W |

Key observations:

- **The relationship is not linear.** Dropping 5 seconds from 2:00 to 1:55 costs ~22 watts. Dropping 5 seconds from 1:40 to 1:35 costs ~47 watts. The faster you go, the more power each second costs.
- **For Joshua's goal:** Moving from 1:42.5 (6:50 pace, ~260W) to 1:37.5 (6:30 pace, ~302W) requires approximately **42 additional watts** of sustained output. This is a ~16% increase in power.
- **Training implication:** Small split improvements at fast paces require significant physiological development. This reinforces the need for a systematic, phased approach rather than simply "training harder."

Note: The exact formula the Concept2 uses is `watts = 2.80 / (split/500)^3` where split is in seconds. The table above uses the simplified form for illustration. Real-world values will match the PM5 display.

---

## Recovery-Adaptation Cycle

### The Fundamental Principle

Training does not make you faster. **Recovery from training** makes you faster. The training stimulus creates stress and micro-damage. During recovery, the body adapts by rebuilding stronger. If the next stimulus comes before recovery is complete, the athlete accumulates fatigue rather than fitness. This is the path to overtraining.

```
Training Stimulus --> Fatigue + Fitness Signal --> Recovery --> Supercompensation
                                                     ^
                                                     |
                                              This is where
                                            improvement happens
```

### Why More Is Not Always Better

The "more is better" fallacy is the leading cause of stalled progress and overtraining in rowing:

- **Overreaching (short-term):** 1-2 weeks of accumulated fatigue. Performance dips. Recoverable with 3-5 days of reduced load. Can be intentional (functional overreaching before a taper).
- **Overtraining (long-term):** Weeks to months of sustained overreaching without adequate recovery. Performance declines. HRV drops chronically. Mood and motivation crater. Recovery takes weeks to months. This is what the AI agent exists to prevent.

### How the AI Agent Manages Recovery

The AI agent uses a multi-signal approach to monitor recovery:

1. **HRV trend:** A declining 7-day HRV trend suggests incomplete recovery. The agent recommends reduced intensity or an extra rest day.
2. **Resting HR trend:** An elevated RHR (>5 bpm above baseline) is an early warning of accumulated fatigue or illness.
3. **Wellness scores:** Declining readiness scores across multiple days indicate the athlete is not recovering between sessions.
4. **ACWR:** If the acute:chronic workload ratio exceeds 1.3, the agent flags the athlete is ramping load too quickly. Above 1.5 is a red-flag zone.
5. **Session quality:** If target splits are consistently missed or RPE is elevated relative to intensity, the agent considers whether fatigue is the cause.

When multiple signals converge, the AI agent adjusts the plan: swapping a hard session for easy work, inserting an extra rest day, or reducing volume for the week. The goal is to keep the athlete in the "productive training" zone without tipping into overtraining.

---

## Weight Management for Lightweights

### The Constraint

Joshua must weigh 160 lbs (72.6 kg) or less at the August 2026 tryouts. This is a hard constraint, not a suggestion. Lightweight rowing imposes this limit, and exceeding it means disqualification.

### The Tension

High training volume demands high caloric intake for recovery and adaptation. But eating too much causes weight gain. Eating too little impairs recovery and performance. The lightweight rower lives in a narrow nutritional corridor.

### Principles

1. **Maintain, do not cut.** The goal is to train at or near 160 lbs throughout the program, not to bulk up and cut weight before race day. Cutting weight impairs performance. Water manipulation is dangerous and reduces power output.

2. **Protein first.** At 1.6-2.2 g/kg (116-160 g/day), protein supports muscle repair and satiety. This is the first macro to lock in each day.

3. **Carbs fuel training.** On high-volume days (>14k meters), carbohydrate intake should be 5-7 g/kg (363-508 g). On rest days, 3-4 g/kg (218-290 g) is sufficient. Carb periodization allows the athlete to fuel hard sessions without excess caloric intake on easy days.

4. **Fat for hormonal health.** Minimum 0.8 g/kg (~58 g/day). Chronically low fat intake suppresses testosterone and impairs recovery. This is a common issue for lightweight rowers who cut fat too aggressively.

5. **Monitor the 7-day average, not the daily weigh-in.** Body weight fluctuates 1-3 lbs day to day based on hydration, sodium intake, glycogen stores, and gut contents. The 7-day rolling average is the true trend indicator. The AI agent tracks this and only flags concern if the 7-day average trends above 162 lbs or below 156 lbs.

6. **No crash diets.** If weight trends upward, the AI agent recommends a modest deficit (200-300 kcal/day) rather than aggressive restriction. Losing more than 1 lb/week while training at high volumes will impair performance and increase injury risk.

### AI Agent Role in Weight Management

- Correlates caloric intake with weight trends.
- Flags if protein intake drops below 1.6 g/kg.
- Alerts if 7-day weight average exceeds 162 lbs (time to tighten up) or drops below 156 lbs (possible under-fueling).
- Adjusts carb recommendations based on planned training load for the day.

---

## Strength Training Philosophy

### Purpose

Strength training for a lightweight rower serves one purpose: **increase power transfer on the erg.** It is not bodybuilding. It is not powerlifting. Every exercise is selected for its relevance to the rowing stroke.

### The Rowing Stroke and Force Application

The rowing drive consists of:

1. **Leg drive (60% of power):** Quads, glutes, hamstrings push against the footplate.
2. **Back swing (30% of power):** Posterior chain (erectors, lats) opens the body angle.
3. **Arm pull (10% of power):** Biceps, lats, forearms finish the stroke.

Strength training targets these movement patterns, emphasizing the posterior chain and leg drive.

### Key Lifts

| Exercise | Movement Pattern | Rowing Relevance | Target (BW Ratio) |
|---|---|---|---|
| **Deadlift** | Hip hinge | Mimics the drive: posterior chain, hip extension, grip strength | 1.75-2.0x BW (280-320 lbs) |
| **Back Squat** | Knee/hip extension | Leg drive power. Foundation of the catch-to-mid-drive | 1.5-1.75x BW (240-280 lbs) |
| **Bench Pull / Bent Row** | Horizontal pull | Mirrors the arm draw. Lat and upper back strength | 1.0-1.25x BW (160-200 lbs) |
| **Weighted Pull-ups** | Vertical pull | Lat strength, scapular stability, grip endurance | BW + 45-70 lbs |
| **Core Work** | Anti-extension, anti-rotation | Power transfer between legs and arms. Stability at the catch | Planks, L-sits, hanging leg raises |

### Periodization of Strength

Strength training follows a secondary periodization within each macro-phase:

- **Base 1 (Feb-Mar):** Hypertrophy/foundation. 3 sessions/week. 3-4 sets x 8-12 reps. Moderate load. Build work capacity and address weaknesses.
- **Base 2 (Apr-May):** Strength-power transition. 2 sessions/week. 4-5 sets x 4-6 reps. Heavier load. Develop maximal strength.
- **Build (Jun-Jul):** Maintenance. 1-2 sessions/week. 3 sets x 3-5 reps. Maintain strength gains while managing total training stress.
- **Peak (Late Jul-Aug):** Minimal or eliminated. Preserve muscle, avoid soreness, prioritize erg performance and recovery.

### Weight Considerations

For a 160-lb lightweight, strength-to-weight ratio matters more than absolute strength. Adding 5 lbs of muscle would require losing 5 lbs of fat to stay at 160, which may or may not be beneficial. The AI agent tracks BW ratios and ensures strength work is not causing unwanted weight gain.

---

## Training Zones for Rowing

Rowing uses a five-zone system that maps to physiological intensity thresholds. Heart rate, split, and RPE are used together to classify intensity.

### Zone Definitions

| Zone | Name | % Max HR | Lactate | RPE | Description |
|---|---|---|---|---|---|
| **UT2** | Utilization Training 2 | 55-75% | < 2 mmol/L | 2-4 | Easy, conversational. Can sustain for 60-90+ min. Primary aerobic development zone. |
| **UT1** | Utilization Training 1 | 75-80% | 2-3 mmol/L | 4-6 | Moderate. "Comfortably uncomfortable." Tempo work. Can sustain for 20-40 min. |
| **AT** | Anaerobic Threshold | 80-85% | 3-4 mmol/L | 6-7 | Hard. At or near lactate threshold. Can sustain for 15-25 min. Threshold intervals. |
| **TR** | Transport | 85-90% | 4-8 mmol/L | 7-9 | Very hard. VO2max zone. Can sustain for 3-8 min. Interval work. |
| **AN** | Anaerobic | 90-100% | > 8 mmol/L | 9-10 | Maximal. Sprint zone. Can sustain for <2 min. Race starts and finishes. |

### Estimated Splits by Zone (for Joshua at Current Fitness)

| Zone | Current Split Range | Target Split Range (by August) |
|---|---|---|
| **UT2** | 2:00-2:10 | 1:55-2:05 |
| **UT1** | 1:52-1:58 | 1:48-1:52 |
| **AT** | 1:46-1:50 | 1:42-1:46 |
| **TR** | 1:40-1:44 | 1:36-1:40 |
| **AN** | 1:30-1:36 | 1:25-1:32 |

These split ranges will be recalibrated after each benchmark test. As fitness improves, each zone's splits shift downward, reflecting the same physiological effort at a faster pace.

### Heart Rate Zone Calculation

Zones are calculated using the **Karvonen method** (heart rate reserve):

```
Target HR = Resting HR + (HR Reserve x Zone %)
HR Reserve = Max HR - Resting HR
```

For example, if Joshua's max HR is 195 and resting HR is 52:
- HR Reserve = 143
- UT2 ceiling (75%): 52 + (143 x 0.75) = 159 bpm
- AT floor (80%): 52 + (143 x 0.80) = 166 bpm

The AI agent uses actual HR data from the Polar H10 to classify each minute of each session into zones, then computes session and weekly distribution.

### Why Zones Matter for the AI Agent

The AI agent uses zone data for three critical functions:

1. **Enforce 80/20:** If weekly distribution shows 65% UT2 and 35% above, the athlete is spending too much time in the gray zone. The AI agent recommends slowing down easy sessions.

2. **Track aerobic development:** Over time, the same zone (e.g., UT2) should be achievable at faster splits. If Joshua starts Base 1 doing UT2 at 2:05 and by the end of Base 2 does UT2 at 1:58, that is a concrete sign of aerobic improvement.

3. **Calibrate training prescriptions:** When the AI agent prescribes "45 minutes at UT2," it defines that in HR terms, not split terms. This prevents the athlete from rowing too hard on good days and ensures consistency regardless of daily fluctuations in feel.

---

## Summary: The Guiding Principles

1. **Build the aerobic base first.** The 2k is an aerobic event. Do not skip to intensity work prematurely.
2. **Polarize intensity.** 80% easy, 20% hard. Avoid the gray zone.
3. **Periodize systematically.** Base -> Build -> Peak. Each phase has a purpose.
4. **Recover deliberately.** Training stress without recovery produces fatigue, not fitness.
5. **Fuel the machine.** At 160 lbs, nutrition is a precision tool, not an afterthought.
6. **Strength supports rowing.** Lift to row faster, not to lift heavier.
7. **Let data drive decisions.** The AI agent exists to remove guesswork and emotion from training adjustments.
8. **Trust the process.** A 20-second improvement over 6 months requires patience. The gains are nonlinear -- they will come.
