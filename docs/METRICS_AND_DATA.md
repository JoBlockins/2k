# Metrics and Data Model

This document catalogs every metric the 2K Erg Training AI Agent tracks, organized into seven tiers from primary performance data down to daily wellness. Each metric includes its source, collection frequency, and rationale for inclusion.

---

## Tier 1 -- Primary Performance (Concept2 Erg)

These are the core output metrics from every erg session. They directly measure rowing performance and form the foundation of all analysis.

| Metric | Unit | Source | Frequency | Rationale |
|---|---|---|---|---|
| **2k Time** | mm:ss.s | Concept2 PM5 / ErgData | Per 2k test (monthly) | The target metric. Everything else serves this number. |
| **500m Splits** | mm:ss.s per 500m | Concept2 PM5 / ErgData | Every session | The fundamental pace metric in rowing. Tracks intensity within and across sessions. |
| **Average Watts** | watts | Concept2 PM5 / ErgData | Every session | Absolute power output. More linear than split for tracking fitness gains. |
| **Stroke Rate (SPM)** | strokes/min | Concept2 PM5 / ErgData | Every session | Measures cadence. Efficiency = maintaining pace at lower SPM. Race rate typically 30-36. |
| **Drive Length** | meters | Concept2 PM5 / ErgData | Every session | Length of the power phase. Indicates technique consistency and range of motion. |
| **Distance per Stroke** | meters/stroke | Concept2 PM5 / ErgData | Every session | Efficiency metric. More distance per stroke at a given pace = better power application. |
| **Drag Factor** | unitless (90-130 typical) | Concept2 PM5 / ErgData | Every session | Resistance setting. Must be consistent across sessions for valid comparisons. Target: 120-130 for lightweight men. |

### Data Source & Integration

- **Concept2 Logbook API:** ErgData syncs PM5 data automatically to the Concept2 online logbook. The AI agent pulls session data via the Concept2 Logbook API.
- **Granularity:** Per-stroke data is available for detailed analysis. Per-interval data is the standard unit of analysis.
- **Storage:** Each session is stored with full split-by-split and summary data.

---

## Tier 2 -- Training Load & Heart Rate

These metrics quantify how hard the body is working and accumulating fatigue. They are essential for managing the balance between training stress and recovery.

| Metric | Unit | Source | Frequency | Rationale |
|---|---|---|---|---|
| **Heart Rate** | bpm | Polar H10 / Whoop 4.0 | Continuous during sessions | Real-time intensity marker. Determines zone distribution. |
| **Training Zone Distribution** | % time in each zone | Calculated from HR data | Per session, weekly rollup | Enforces the 80/20 polarized model. Ensures easy days stay easy. |
| **Weekly Volume** | meters | Concept2 Logbook | Weekly rollup | Total training load. Target ranges from 70k-100k depending on phase. |
| **Session RPE** | 1-10 scale | Manual input (athlete) | Per session | Subjective effort rating. Cross-referenced with HR to detect drift or mismatch. |
| **Training Load (TRIMP/TSS)** | arbitrary units | Calculated (HR x duration x intensity) | Per session, weekly rollup | Quantifies cumulative training stress. TRIMP uses HR zones; TSS uses power zones. |
| **Acute:Chronic Workload Ratio (ACWR)** | ratio | Calculated from TRIMP/TSS | Weekly | Injury risk indicator. Ideal range: 0.8-1.3. Above 1.5 = elevated injury risk. |

### The 80/20 Rule

The polarized training model dictates that approximately 80% of training volume should be at low intensity (Zone 2 / UT2) and 20% at high intensity (above threshold). The AI agent monitors zone distribution weekly and flags deviations.

### Data Sources & Integration

- **Polar H10:** Chest strap provides accurate beat-by-beat HR during sessions. Data syncs via Bluetooth to Polar Flow and/or Apple Health.
- **Whoop 4.0:** Provides 24/7 HR data including resting HR and session strain.
- **RPE:** Entered manually by the athlete after each session via the dashboard or a quick-input form.
- **Calculations:** TRIMP, TSS, ACWR, and zone distribution are computed by the AI agent's processing layer from raw HR and session data.

---

## Tier 3 -- Benchmark Tests

Periodic benchmark tests provide objective performance snapshots. Each test targets a different energy system and correlates with 2k performance in a known way.

| Metric | Unit | Target Range | Frequency | Rationale |
|---|---|---|---|---|
| **2k Test** | mm:ss | < 6:30 | Monthly (or per plan) | The target event. Direct measurement of goal progress. |
| **6k Test** | /500m split | ~1:48-1:50 | Every 4-6 weeks | Best predictor of 2k potential. 6k split + 5-7 sec ~ 2k split. A 1:49 6k predicts ~1:37 2k. |
| **30-Minute Test** | total meters | ~7,800-8,000m | Every 4-6 weeks | Aerobic capacity benchmark. Correlates with UT1/AT threshold. |
| **500m Test** | mm:ss | ~1:25-1:28 | Every 6-8 weeks | Anaerobic power / top-end speed. Ensures the athlete has sprint capacity for the 2k start and finish. |
| **Step Test** | HR vs. split at each step | N/A (trend-based) | Every 6-8 weeks | Maps the HR-to-split curve. Tracks aerobic efficiency gains over time. Deflection point indicates threshold. |

### Benchmark-to-2k Prediction Models

The AI agent uses the following established relationships:

- **6k split + ~5-7 seconds = predicted 2k split** (primary predictor)
- **30-min meters / 6 x 1.0 adjustment = rough 2k meter equivalent**
- **Paul's Law:** The relationship between 6k and 2k is the most reliable predictor in rowing. The agent weights this heavily.
- **500m test** establishes the "speed ceiling" -- an athlete cannot 2k faster than their sprint capacity allows.

### Data Sources & Integration

- All tests performed on the Concept2 erg and logged via ErgData.
- The AI agent schedules benchmark tests within the periodized plan and compares results across the timeline.

---

## Tier 4 -- Physiological & Recovery

These metrics track the body's baseline state and recovery capacity. They are leading indicators: changes here often precede changes in performance.

| Metric | Unit | Source | Frequency | Rationale |
|---|---|---|---|---|
| **Body Weight** | lbs | Withings Body+ | Daily (morning, post-void) | Lightweight requirement: must be at or below 160 lbs. Tracks trends, not daily noise. |
| **7-Day Weight Average** | lbs | Calculated from daily weight | Daily (rolling) | Smooths daily fluctuations. The true trend indicator for weight management. |
| **Resting Heart Rate** | bpm | Whoop 4.0 | Daily (morning) | Trending down = improving aerobic fitness. Acute spikes = fatigue, illness, or stress. |
| **HRV (RMSSD)** | ms | Whoop 4.0 | Daily (morning) | Gold-standard recovery metric. Higher baseline = better parasympathetic tone. Drops indicate incomplete recovery. |
| **Sleep Duration** | hours | Whoop 4.0 | Daily | Recovery happens during sleep. Target: 7.5-9 hours. Below 7 hours consistently = impaired adaptation. |
| **Sleep Quality** | % / score | Whoop 4.0 | Daily | Not all sleep is equal. Tracks deep sleep, REM, disturbances. |
| **VO2max Estimate** | mL/kg/min | Calculated / step test | Monthly | Aerobic ceiling. For sub-6:30 lightweight, estimated VO2max should be in the 60-65+ range. |

### Data Sources & Integration

- **Withings Body+:** Syncs via Withings Health Mate API. Daily weight is pulled automatically.
- **Whoop 4.0:** Syncs via Whoop API. Provides resting HR, HRV, sleep metrics, and recovery score each morning.
- **VO2max:** Estimated from step test results or pace-to-HR relationships. Not directly measured unless lab testing is available.
- **7-Day Weight Average:** Computed by the AI agent from the raw daily weight data.

---

## Tier 5 -- Strength

Rowing-specific strength metrics ensure the athlete has the muscular capacity to support the power demands of a sub-6:30 2k. Strength training is supplementary -- it serves the erg, not the other way around.

| Metric | Unit | Source | Frequency | Rationale |
|---|---|---|---|---|
| **Deadlift** | lbs (1RM or 3RM) | Manual input / gym log | Monthly test | Primary hip-hinge strength. Directly transfers to the rowing drive. Target: 1.75-2.0x BW (280-320 lbs). |
| **Back Squat** | lbs (1RM or 3RM) | Manual input / gym log | Monthly test | Leg drive strength. Foundation of rowing power. Target: 1.5-1.75x BW (240-280 lbs). |
| **Bench Pull / Bent Over Row** | lbs (1RM or 3RM) | Manual input / gym log | Monthly test | Horizontal pulling strength. Mirrors the rowing stroke's arm/back engagement. Target: 1.0-1.25x BW (160-200 lbs). |
| **Weighted Pull-ups** | added weight (lbs) | Manual input / gym log | Monthly test | Vertical pulling strength and lat engagement. Target: BW + 45-70 lbs. |
| **Core Tests** | time / reps | Manual input | Monthly | Plank holds, L-sits, or similar. Core stability transfers to power connection on the erg. |
| **BW Ratios** | ratio | Calculated | Monthly | Strength-to-weight ratios. Critical for lightweights -- absolute strength matters less than relative strength at 160 lbs. |

### Data Sources & Integration

- **Manual Input:** Strength data is entered by the athlete after gym sessions via the dashboard input form.
- **Gym Log:** If a gym tracking app is used, CSV export or manual transcription.
- **BW Ratios:** Calculated by the AI agent from strength numbers and current body weight.

---

## Tier 6 -- Nutrition

For a lightweight rower, nutrition is a balancing act: fuel high training volumes while maintaining 160 lbs. The AI agent monitors macronutrient intake and flags deficits that could impair recovery or performance.

| Metric | Unit | Source | Frequency | Rationale |
|---|---|---|---|---|
| **Caloric Intake** | kcal/day | MyFitnessPal | Daily | Must match energy expenditure. Under-fueling impairs recovery and performance. Over-fueling risks weight gain. |
| **Protein** | grams/day | MyFitnessPal | Daily | Target: 1.6-2.2 g/kg = 116-160 g/day at 72.6 kg. Essential for muscle recovery and adaptation. |
| **Carbohydrates** | grams/day | MyFitnessPal | Daily | Primary fuel for erg training. Should be periodized: higher on heavy training days, moderate on rest days. |
| **Fat** | grams/day | MyFitnessPal | Daily | Minimum ~0.8 g/kg (~58 g/day) for hormonal health. Remainder of calories after protein and carb targets. |
| **Hydration** | liters/day | Manual input / estimate | Daily | Dehydration impairs performance and is a weight-cutting risk for lightweights. Target: 3-4 L/day. |

### Lightweight-Specific Nutrition Considerations

- **Weight ceiling:** 160 lbs. The 7-day weight average must stay at or near this mark. The AI agent correlates caloric intake trends with weight trends.
- **Protein priority:** At 1.6-2.2 g/kg, protein intake is the first macro to lock in. This range supports training adaptation without excess caloric load.
- **Carb periodization:** High-volume steady-state days need more carbs (5-7 g/kg). Rest days and light days need less (3-4 g/kg).
- **No crash dieting:** Rapid weight loss impairs performance. The AI agent flags if weight drops too quickly (>1 lb/week sustained) or caloric intake drops below estimated BMR.

### Data Sources & Integration

- **MyFitnessPal:** Data exported via CSV or pulled via API (unofficial/third-party). Daily macro totals are the primary unit of analysis.
- **Manual Input:** Hydration tracking is self-reported via the dashboard.
- **Calculations:** The AI agent computes g/kg values from intake and current body weight.

---

## Tier 7 -- Daily Wellness (30-Second Check-In)

A brief daily self-assessment captures subjective readiness. These scores are fast to collect and surprisingly predictive of training quality and injury risk.

| Metric | Scale | Source | Frequency | Rationale |
|---|---|---|---|---|
| **Fatigue** | 1-10 (1 = fresh, 10 = exhausted) | Manual input | Daily (morning) | Overall energy level. Persistent high fatigue = possible overreaching. |
| **Muscle Soreness** | 1-10 (1 = none, 10 = severe) | Manual input | Daily (morning) | Localizes accumulated damage. High soreness + high-intensity planned = potential injury risk. |
| **Stress** | 1-10 (1 = relaxed, 10 = overwhelmed) | Manual input | Daily (morning) | Life stress impairs recovery. The AI agent accounts for non-training stressors. |
| **Mood / Motivation** | 1-10 (1 = low, 10 = high) | Manual input | Daily (morning) | Low motivation trending downward is an early sign of overtraining syndrome. |
| **Sleep Quality** | 1-10 (1 = terrible, 10 = excellent) | Manual input | Daily (morning) | Subjective sleep feel complements Whoop's objective sleep data. Discrepancies are informative. |

### Composite Wellness Score

The AI agent computes a **Daily Readiness Score** from these five inputs:

```
Readiness = (10 - Fatigue) + (10 - Soreness) + (10 - Stress) + Mood + Sleep Quality
            -----------------------------------------------------------------------
                                           5
```

This yields a 1-10 readiness score. The AI agent uses this to:

- Recommend session intensity adjustments (e.g., swap a hard interval session for steady state if readiness is below 5).
- Detect multi-day readiness trends that signal overreaching.
- Cross-reference with HRV and resting HR for a holistic recovery picture.

### Data Sources & Integration

- **Manual Input:** The athlete completes a 30-second check-in each morning via the dashboard or a quick-input form (5 sliders or number entries).
- **Storage:** Stored as a daily record with timestamp.
- **Analysis:** Trends over 7-day and 28-day windows. The AI agent looks for declining trends, not isolated bad days.

---

## Data Integration Summary

| Source | Integration Method | Metrics Covered |
|---|---|---|
| Concept2 PM5 / ErgData | Concept2 Logbook API | Tier 1 (all), Tier 3 (all tests) |
| Polar H10 | Polar Flow API / Apple Health | Tier 2 (HR, zones) |
| Whoop 4.0 | Whoop API | Tier 2 (HR), Tier 4 (RHR, HRV, sleep) |
| Withings Body+ | Withings Health Mate API | Tier 4 (body weight) |
| MyFitnessPal | CSV export or third-party API | Tier 6 (nutrition) |
| Manual Input (Dashboard) | Direct entry via web form | Tier 2 (RPE), Tier 5 (strength), Tier 6 (hydration), Tier 7 (wellness) |
| Calculated / Derived | AI agent processing layer | TRIMP/TSS, ACWR, zone distribution, BW ratios, 7-day weight avg, readiness score, VO2max estimate, 2k predictions |

### Data Freshness Requirements

| Cadence | Metrics |
|---|---|
| **Real-time (during session)** | HR, splits, watts, stroke rate |
| **Post-session** | Session summary, RPE, zone distribution, TRIMP |
| **Daily (morning)** | Body weight, RHR, HRV, sleep, wellness scores |
| **Daily** | Nutrition (logged throughout day, summarized at end) |
| **Weekly** | Volume rollup, ACWR, zone distribution rollup, weight trend |
| **Monthly / Per-plan** | Benchmark tests, strength tests, VO2max estimate |
