"""Structured prompts for the Claude-powered coaching agent."""

SYSTEM_PROMPT = """You are an expert rowing coach and sports scientist specializing in lightweight men's rowing ergometer performance. You are coaching Joshua Dockins, a lightweight rower (160 lbs) targeting a sub-6:30 2k erg time by August 2026 (currently 6:50).

Your coaching philosophy:
- Polarized training model (80% low intensity / 20% high intensity)
- Data-driven decision making — every recommendation must be grounded in the athlete's metrics
- Recovery is training — adaptation happens during rest, not during work
- Progressive overload with careful fatigue management
- Weight management is critical: must maintain 160 lbs for lightweight eligibility

Training zones (based on max HR ~195):
- UT2 (Zone 1): 107-137 HR — Easy recovery/base work
- UT1 (Zone 2): 137-156 HR — Steady state (primary training zone)
- AT (Zone 3): 156-166 HR — Anaerobic threshold
- TR (Zone 4): 166-179 HR — VO2max / transport
- AN (Zone 5): 179-195 HR — Anaerobic / race pace

Key rowing relationships:
- Watts = 2.80 / (pace_per_meter)^3 — cubic relationship means small split drops require large power gains
- 2k split ≈ 6k split - 5 to 7 seconds
- Sub-6:30 2k = 1:37.5/500m split = ~235 watts average
- Current 6:50 2k = 1:42.5/500m split = ~205 watts — need ~30 watt improvement

Periodization (Feb-Aug 2026):
- Base 1 (Feb-Mar): Aerobic foundation, 70-90k m/week, 80%+ Zone 2
- Base 2 (Apr-May): Aerobic capacity + tempo, 80-100k m/week, 75/25 split
- Build (Jun-Jul): Threshold & race-pace, 60-80k m/week, 70/30 split
- Peak & Taper (Late Jul-Aug): Race simulation, decreasing volume

Always explain the "why" behind every recommendation. Be direct and specific — give exact splits, durations, and heart rate targets. Flag any concerning trends immediately."""


def weekly_analysis_prompt(data: dict) -> str:
    """Build the prompt for weekly training analysis."""
    return f"""Analyze this week's training data and provide a comprehensive weekly review.

## This Week's Data
{_format_dict(data.get('weekly_summary', {}))}

## Workouts This Week
{_format_workouts(data.get('workouts', []))}

## Recovery & Wellness
{_format_dict(data.get('recovery', {}))}

## Wellness Check-ins
{_format_wellness(data.get('wellness', []))}

## Weight Trend
{_format_dict(data.get('weight', {}))}

## Fitness/Fatigue Status
{_format_dict(data.get('fitness_fatigue', {}))}

## Acute:Chronic Workload Ratio
{_format_dict(data.get('acwr', {}))}

## Current 2k Prediction
{_format_dict(data.get('prediction', {}))}

## Current Training Phase
{data.get('phase', 'Unknown')}

## Weeks Until Goal Date
{data.get('weeks_remaining', 'Unknown')}

Provide:
1. **Week Summary**: Overall assessment of the training week (2-3 sentences)
2. **What Went Well**: Specific positives backed by data
3. **Concerns**: Any warning signs (overtraining, weight drift, poor recovery, missed targets)
4. **2k Progress**: Are we on track for sub-6:30 by August? What's the projected trajectory?
5. **Next Week Adjustments**: Specific modifications to the upcoming training week with exact prescriptions
6. **Key Metric to Watch**: The single most important metric to focus on next week"""


def plan_adjustment_prompt(data: dict) -> str:
    """Build the prompt for adjusting the training plan based on signals."""
    return f"""Based on the following signals, determine if the training plan needs adjustment.

## Current Signals
{_format_dict(data.get('signals', {}))}

## Current Plan for Next Week
{_format_planned_workouts(data.get('planned_workouts', []))}

## Recent Training Context
{_format_dict(data.get('context', {}))}

Evaluate whether any planned workouts should be modified. For each adjustment:
1. Which workout to change and what the new prescription should be
2. Why the change is needed (cite specific data)
3. What signal triggered the change

If no changes are needed, explain why the current plan is appropriate.

Return your response as structured JSON:
{{
  "adjustments_needed": true/false,
  "adjustments": [
    {{
      "workout_date": "YYYY-MM-DD",
      "original": "description of original workout",
      "modified": "description of modified workout",
      "reason": "why this change is needed"
    }}
  ],
  "overall_assessment": "brief summary"
}}"""


def coaching_chat_prompt(question: str, context: dict) -> str:
    """Build prompt for answering athlete questions."""
    return f"""The athlete asks: "{question}"

## Current Context
- Current 2k prediction: {context.get('prediction', 'N/A')}
- Training phase: {context.get('phase', 'N/A')}
- Fitness/Fatigue (CTL/ATL/TSB): {context.get('fitness_fatigue', 'N/A')}
- Weight status: {context.get('weight', 'N/A')}
- Recent workouts: {context.get('recent_workouts', 'N/A')}
- Recovery status: {context.get('recovery', 'N/A')}

Answer the question directly, with specific data references where possible. Be encouraging but honest. If the question requires information you don't have, say so and suggest what data would help answer it."""


def _format_dict(d: dict) -> str:
    if not d:
        return "No data available"
    lines = []
    for k, v in d.items():
        lines.append(f"- {k}: {v}")
    return "\n".join(lines)


def _format_workouts(workouts: list) -> str:
    if not workouts:
        return "No workouts recorded"
    lines = []
    for w in workouts:
        line = f"- {w.get('date', 'N/A')}: {w.get('description', w.get('workout_type', 'N/A'))}"
        if w.get('avg_split_seconds'):
            from src.data.metrics import format_split
            line += f" | Split: {format_split(w['avg_split_seconds'])}"
        if w.get('total_distance_m'):
            line += f" | {w['total_distance_m']}m"
        if w.get('avg_hr'):
            line += f" | HR: {w['avg_hr']}"
        if w.get('rpe'):
            line += f" | RPE: {w['rpe']}"
        lines.append(line)
    return "\n".join(lines)


def _format_wellness(wellness: list) -> str:
    if not wellness:
        return "No wellness data"
    lines = []
    for w in wellness:
        line = f"- {w.get('date', 'N/A')}: Fatigue={w.get('fatigue', '-')}, Soreness={w.get('muscle_soreness', '-')}, Stress={w.get('stress', '-')}, Mood={w.get('mood', '-')}, Sleep={w.get('sleep_quality_subjective', '-')}"
        lines.append(line)
    return "\n".join(lines)


def _format_planned_workouts(workouts: list) -> str:
    if not workouts:
        return "No planned workouts"
    lines = []
    for w in workouts:
        line = f"- {w.get('date', 'N/A')}: {w.get('title', 'N/A')} ({w.get('workout_type', 'N/A')})"
        if w.get('target_split_seconds'):
            from src.data.metrics import format_split
            line += f" | Target: {format_split(w['target_split_seconds'])}"
        lines.append(line)
    return "\n".join(lines)
