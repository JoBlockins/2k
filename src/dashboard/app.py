"""Streamlit dashboard for the 2K Training Coach."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from datetime import date, timedelta

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.agent.coach import CoachAgent
from src.agent.plan_generator import generate_full_plan
from src.data.metrics import (
    calculate_acwr,
    calculate_fitness_fatigue,
    format_split,
    format_time,
    predict_2k_from_benchmarks,
    split_to_watts,
    weekly_summary,
    weight_trend,
)
from src.models.benchmark import BenchmarkTest
from src.models.body import BodyWeight
from src.models.database import SessionLocal, init_db
from src.models.nutrition import DailyNutrition
from src.models.strength import StrengthBenchmark
from src.models.training_plan import PlannedWorkout, TrainingPhase
from src.models.wellness import DailyWellness, RecoveryMetrics
from src.models.workout import Workout
from src.data.concept2_csv import import_concept2_csv

# ── Page config ──────────────────────────────

st.set_page_config(
    page_title="2K Training Coach",
    page_icon="🚣",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize DB
init_db()


def get_db():
    return SessionLocal()


# ── Sidebar navigation ──────────────────────────

st.sidebar.title("2K Training Coach")
st.sidebar.markdown("**Goal:** Sub-6:30 by Aug 2026")
st.sidebar.markdown("**Current:** 6:50 | **Target:** 6:30")
st.sidebar.divider()

page = st.sidebar.radio(
    "Navigate",
    ["Daily Log", "Weekly Summary", "Trends", "2K Predictor", "Benchmarks", "Training Plan", "Import Data", "Chat with Coach"],
)

# ── Daily Log ──────────────────────────────

if page == "Daily Log":
    st.title("Daily Training Log")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Wellness Check-in")
        with st.form("wellness_form"):
            wellness_date = st.date_input("Date", value=date.today())
            fatigue = st.slider("Fatigue", 1, 10, 5)
            soreness = st.slider("Muscle Soreness", 1, 10, 3)
            stress = st.slider("Stress", 1, 10, 4)
            mood = st.slider("Mood / Motivation", 1, 10, 7)
            sleep_q = st.slider("Sleep Quality", 1, 10, 7)
            wellness_notes = st.text_area("Notes", height=68)

            if st.form_submit_button("Save Wellness"):
                db = get_db()
                existing = db.query(DailyWellness).filter(DailyWellness.date == wellness_date).first()
                if existing:
                    existing.fatigue = fatigue
                    existing.muscle_soreness = soreness
                    existing.stress = stress
                    existing.mood = mood
                    existing.sleep_quality_subjective = sleep_q
                    existing.notes = wellness_notes or None
                else:
                    db.add(DailyWellness(
                        date=wellness_date, fatigue=fatigue, muscle_soreness=soreness,
                        stress=stress, mood=mood, sleep_quality_subjective=sleep_q,
                        notes=wellness_notes or None,
                    ))
                db.commit()
                db.close()
                st.success("Wellness saved!")

        st.subheader("Body Weight")
        with st.form("weight_form"):
            weight_date = st.date_input("Date", value=date.today(), key="weight_date")
            weight_lbs = st.number_input("Weight (lbs)", min_value=140.0, max_value=180.0, value=160.0, step=0.1)

            if st.form_submit_button("Save Weight"):
                db = get_db()
                db.add(BodyWeight(date=weight_date, weight_lbs=weight_lbs, source="manual"))
                db.commit()
                db.close()
                st.success(f"Weight saved: {weight_lbs} lbs")

    with col2:
        st.subheader("Log Workout")
        with st.form("workout_form"):
            wo_date = st.date_input("Date", value=date.today(), key="wo_date")
            wo_type = st.selectbox("Type", ["steady_state", "tempo", "threshold", "interval", "race_pace", "test", "strength", "other"])
            wo_desc = st.text_input("Description", placeholder="e.g., 60min SS or 4x2k r4:00")

            col_a, col_b = st.columns(2)
            with col_a:
                wo_distance = st.number_input("Distance (m)", min_value=0, value=0, step=100)
                wo_split_min = st.number_input("Avg Split (min)", min_value=0, max_value=3, value=1)
                wo_spm = st.number_input("Avg SPM", min_value=0.0, max_value=50.0, value=0.0, step=0.5)
                wo_rpe = st.slider("RPE", 1, 10, 5, key="wo_rpe")

            with col_b:
                wo_time_min = st.number_input("Time (minutes)", min_value=0.0, value=0.0, step=1.0)
                wo_split_sec = st.number_input("Avg Split (sec)", min_value=0.0, max_value=59.9, value=45.0, step=0.1)
                wo_hr = st.number_input("Avg HR", min_value=0, max_value=220, value=0)
                wo_drag = st.number_input("Drag Factor", min_value=0, max_value=200, value=125)

            wo_notes = st.text_area("Notes", height=68, key="wo_notes")

            if st.form_submit_button("Save Workout"):
                db = get_db()
                split_secs = wo_split_min * 60 + wo_split_sec if wo_split_min or wo_split_sec else None
                from src.data.metrics import calculate_trimp

                workout = Workout(
                    date=wo_date,
                    workout_type=wo_type,
                    description=wo_desc or None,
                    source="manual",
                    total_distance_m=wo_distance or None,
                    total_time_seconds=wo_time_min * 60 if wo_time_min else None,
                    avg_split_seconds=split_secs,
                    avg_watts=split_to_watts(split_secs) if split_secs else None,
                    avg_spm=wo_spm or None,
                    avg_hr=wo_hr or None,
                    rpe=wo_rpe,
                    drag_factor=wo_drag or None,
                    notes=wo_notes or None,
                )

                if workout.avg_hr and workout.total_time_seconds:
                    workout.trimp = calculate_trimp(
                        duration_minutes=workout.total_time_seconds / 60,
                        avg_hr=workout.avg_hr,
                    )

                db.add(workout)
                db.commit()
                db.close()
                st.success("Workout saved!")

    # Recovery metrics from Whoop
    st.divider()
    st.subheader("Recovery & Readiness")
    db = get_db()
    today_recovery = db.query(RecoveryMetrics).filter(
        RecoveryMetrics.date == date.today()
    ).first()
    if not today_recovery:
        today_recovery = db.query(RecoveryMetrics).filter(
            RecoveryMetrics.date == date.today() - timedelta(days=1)
        ).first()
        if today_recovery:
            st.caption("Showing yesterday's recovery (today not yet available)")

    if today_recovery:
        rc1, rc2, rc3, rc4 = st.columns(4)
        with rc1:
            score = today_recovery.whoop_recovery_score
            st.metric("Recovery Score", f"{score:.0f}%" if score is not None else "N/A")
        with rc2:
            st.metric("HRV (RMSSD)", f"{today_recovery.hrv_rmssd:.0f} ms" if today_recovery.hrv_rmssd else "N/A")
        with rc3:
            st.metric("Resting HR", f"{today_recovery.resting_hr} bpm" if today_recovery.resting_hr else "N/A")
        with rc4:
            strain = today_recovery.whoop_strain
            st.metric("Strain", f"{strain:.1f}" if strain is not None else "N/A")

        # Sleep breakdown
        sc1, sc2, sc3, sc4 = st.columns(4)
        with sc1:
            dur = today_recovery.sleep_duration_minutes
            if dur:
                hrs, mins = divmod(dur, 60)
                st.metric("Sleep", f"{hrs}h {mins}m")
            else:
                st.metric("Sleep", "N/A")
        with sc2:
            sq = today_recovery.sleep_quality_score
            st.metric("Sleep Quality", f"{sq:.0f}%" if sq is not None else "N/A")
        with sc3:
            st.metric("Deep Sleep", f"{today_recovery.deep_sleep_minutes} min" if today_recovery.deep_sleep_minutes else "N/A")
        with sc4:
            st.metric("REM Sleep", f"{today_recovery.rem_sleep_minutes} min" if today_recovery.rem_sleep_minutes else "N/A")
    else:
        st.write("No recovery data available. Sync Whoop to see metrics here.")

    # Today's planned workout
    st.divider()
    st.subheader("Today's Planned Workout")
    planned = db.query(PlannedWorkout).filter(
        PlannedWorkout.date == date.today(),
        PlannedWorkout.status == "scheduled",
    ).first()

    if planned:
        st.info(f"**{planned.title}**\n\n{planned.description}")
        tc1, tc2, tc3 = st.columns(3)
        with tc1:
            if planned.target_split_seconds:
                st.metric("Target Split", format_split(planned.target_split_seconds))
        with tc2:
            if planned.target_spm_low:
                spm_str = f"{planned.target_spm_low}"
                if planned.target_spm_high and planned.target_spm_high != planned.target_spm_low:
                    spm_str += f"-{planned.target_spm_high}"
                st.metric("Target SPM", spm_str)
        with tc3:
            if planned.target_hr_low:
                hr_str = f"{planned.target_hr_low}"
                if planned.target_hr_high:
                    hr_str += f"-{planned.target_hr_high}"
                st.metric("Target HR", hr_str)
        if planned.target_distance_m:
            st.caption(f"Target distance: {planned.target_distance_m:,}m")
        if planned.target_time_seconds:
            t_min = planned.target_time_seconds / 60
            st.caption(f"Target time: {t_min:.0f} min")
    else:
        st.write("No planned workout for today.")
    db.close()


# ── Weekly Summary ──────────────────────────────

elif page == "Weekly Summary":
    st.title("Weekly Summary")

    # Week selector
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    selected_week = st.date_input("Week starting", value=week_start)

    db = get_db()
    summary = weekly_summary(db, selected_week)

    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Volume", f"{summary['total_meters']:,}m")
    with col2:
        st.metric("Sessions", summary["session_count"])
    with col3:
        st.metric("Training Load (TRIMP)", summary["total_trimp"])
    with col4:
        if summary["low_intensity_pct"] is not None:
            st.metric("Low/High Split", f"{summary['low_intensity_pct']:.0f}/{summary['high_intensity_pct']:.0f}")
        else:
            st.metric("Low/High Split", "N/A")

    # Fitness / Fatigue
    st.subheader("Fitness & Fatigue")
    ff = calculate_fitness_fatigue(db, selected_week + timedelta(days=6))
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Fitness (CTL)", ff["ctl"])
    with col2:
        st.metric("Fatigue (ATL)", ff["atl"])
    with col3:
        st.metric("Form (TSB)", ff["tsb"])
    with col4:
        st.metric("Status", ff["status"].replace("_", " ").title())

    # ACWR
    acwr = calculate_acwr(db, selected_week + timedelta(days=6))
    st.metric("Acute:Chronic Ratio", f"{acwr['acwr']} ({acwr['risk'].replace('_', ' ')})")

    # Weight
    wt = weight_trend(db, selected_week + timedelta(days=6))
    if wt:
        st.subheader("Weight")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Latest", f"{wt['latest']} lbs")
        with col2:
            st.metric("7-Day Avg", f"{wt['seven_day_avg']} lbs" if wt['seven_day_avg'] else "N/A")
        with col3:
            st.metric("vs Target (160)", f"{wt['deviation_from_target']:+.1f} lbs" if wt['deviation_from_target'] is not None else "N/A")

    # Workouts this week
    st.subheader("Workouts")
    workouts = db.query(Workout).filter(
        Workout.date >= selected_week,
        Workout.date <= selected_week + timedelta(days=6),
    ).order_by(Workout.date).all()

    for w in workouts:
        with st.expander(f"{w.date} — {w.description or w.workout_type}"):
            cols = st.columns(5)
            cols[0].metric("Distance", f"{w.total_distance_m:,}m" if w.total_distance_m else "N/A")
            cols[1].metric("Split", format_split(w.avg_split_seconds) if w.avg_split_seconds else "N/A")
            cols[2].metric("SPM", w.avg_spm or "N/A")
            cols[3].metric("HR", w.avg_hr or "N/A")
            cols[4].metric("RPE", w.rpe or "N/A")

    db.close()


# ── Trends ──────────────────────────────

elif page == "Trends":
    st.title("Training Trends")

    db = get_db()
    days_back = st.slider("Days to show", 14, 180, 60)
    start = date.today() - timedelta(days=days_back)

    # Split trend
    workouts = db.query(Workout).filter(
        Workout.date >= start,
        Workout.avg_split_seconds.isnot(None),
    ).order_by(Workout.date).all()

    if workouts:
        import pandas as pd

        df = pd.DataFrame([
            {"date": w.date, "split": w.avg_split_seconds, "type": w.workout_type, "watts": w.avg_watts}
            for w in workouts
        ])

        fig = px.scatter(df, x="date", y="split", color="type",
                         title="Average Split Over Time",
                         labels={"split": "Split (sec/500m)", "date": "Date"})
        fig.add_hline(y=97.5, line_dash="dash", line_color="green",
                      annotation_text="Goal: 1:37.5")
        fig.update_yaxes(autorange="reversed")
        st.plotly_chart(fig, use_container_width=True)

        # Watts trend
        fig_watts = px.scatter(df, x="date", y="watts", color="type",
                               title="Average Watts Over Time")
        fig_watts.add_hline(y=235, line_dash="dash", line_color="green",
                            annotation_text="Goal: 235W")
        st.plotly_chart(fig_watts, use_container_width=True)

    # Volume trend (weekly)
    st.subheader("Weekly Volume")
    weeks = []
    current = start
    while current <= date.today():
        ws = weekly_summary(db, current)
        weeks.append({"week": current, "meters": ws["total_meters"], "sessions": ws["session_count"]})
        current += timedelta(days=7)

    if weeks:
        import pandas as pd
        df_vol = pd.DataFrame(weeks)
        fig_vol = px.bar(df_vol, x="week", y="meters", title="Weekly Volume (meters)")
        st.plotly_chart(fig_vol, use_container_width=True)

    # Weight trend
    weights = db.query(BodyWeight).filter(
        BodyWeight.date >= start
    ).order_by(BodyWeight.date).all()

    if weights:
        import pandas as pd
        df_wt = pd.DataFrame([{"date": w.date, "weight": w.weight_lbs} for w in weights])
        fig_wt = px.line(df_wt, x="date", y="weight", title="Body Weight Trend")
        fig_wt.add_hline(y=160, line_dash="dash", line_color="red", annotation_text="Target: 160 lbs")
        st.plotly_chart(fig_wt, use_container_width=True)

    # HRV trend
    recovery = db.query(RecoveryMetrics).filter(
        RecoveryMetrics.date >= start,
        RecoveryMetrics.hrv_rmssd.isnot(None),
    ).order_by(RecoveryMetrics.date).all()

    if recovery:
        import pandas as pd
        df_hrv = pd.DataFrame([{"date": r.date, "HRV": r.hrv_rmssd, "RHR": r.resting_hr} for r in recovery])
        fig_hrv = px.line(df_hrv, x="date", y="HRV", title="HRV (RMSSD) Trend")
        st.plotly_chart(fig_hrv, use_container_width=True)

    db.close()


# ── 2K Predictor ──────────────────────────────

elif page == "2K Predictor":
    st.title("2K Prediction")

    db = get_db()
    prediction = predict_2k_from_benchmarks(db)

    if prediction:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Predicted 2K", prediction["formatted_time"])
        with col2:
            st.metric("Predicted Split", prediction["formatted_split"])
        with col3:
            gap = prediction["gap_seconds"]
            st.metric("Gap to Goal", f"{gap:+.1f}s", delta=f"{-gap:.1f}s to go" if gap > 0 else "GOAL MET!")

        st.subheader("Prediction Sources")
        for p in prediction["predictions"]:
            source_name = p["source"].replace("_", " ").title()
            st.write(f"- **{source_name}** ({p['date']}): {format_time(p['predicted_2k_time'])} "
                     f"(confidence: {p['confidence']:.0%})")
    else:
        st.warning("No benchmark data available for prediction. Complete a 2k, 6k, or 30-minute test to get started.")

    # Benchmark history
    st.subheader("2K Test History")
    tests = db.query(BenchmarkTest).filter(
        BenchmarkTest.test_type == "2k"
    ).order_by(BenchmarkTest.date).all()

    if tests:
        import pandas as pd
        df = pd.DataFrame([
            {"date": t.date, "time": t.total_time_seconds, "split": t.avg_split_seconds}
            for t in tests
        ])
        fig = px.line(df, x="date", y="time", title="2K Test Results Over Time",
                      labels={"time": "Time (seconds)"})
        fig.add_hline(y=390, line_dash="dash", line_color="green", annotation_text="Goal: 6:30")
        fig.update_yaxes(autorange="reversed")
        st.plotly_chart(fig, use_container_width=True)

    db.close()


# ── Benchmarks ──────────────────────────────

elif page == "Benchmarks":
    st.title("Benchmark Tests")

    db = get_db()

    # Log new benchmark
    with st.expander("Log New Benchmark Test"):
        with st.form("benchmark_form"):
            bm_date = st.date_input("Date")
            bm_type = st.selectbox("Test Type", ["2k", "6k", "30min", "500m", "step"])

            col1, col2 = st.columns(2)
            with col1:
                bm_time_min = st.number_input("Time (min)", min_value=0, value=0)
                bm_time_sec = st.number_input("Time (sec)", min_value=0.0, max_value=59.9, value=0.0, step=0.1)
                bm_avg_hr = st.number_input("Avg HR", min_value=0, value=0)
            with col2:
                bm_distance = st.number_input("Distance (m)", min_value=0, value=0)
                bm_split_min = st.number_input("Avg Split (min)", min_value=0, value=1, key="bm_split_min")
                bm_split_sec = st.number_input("Avg Split (sec)", min_value=0.0, max_value=59.9, value=40.0, step=0.1, key="bm_split_sec")

            bm_notes = st.text_area("Notes", key="bm_notes")

            if st.form_submit_button("Save Benchmark"):
                total_time = (bm_time_min * 60 + bm_time_sec) if bm_time_min or bm_time_sec else None
                split_secs = bm_split_min * 60 + bm_split_sec if bm_split_min or bm_split_sec else None

                benchmark = BenchmarkTest(
                    date=bm_date,
                    test_type=bm_type,
                    total_time_seconds=total_time,
                    total_distance_m=bm_distance or None,
                    avg_split_seconds=split_secs,
                    avg_watts=split_to_watts(split_secs) if split_secs else None,
                    avg_hr=bm_avg_hr or None,
                    notes=bm_notes or None,
                )
                db.add(benchmark)
                db.commit()
                st.success("Benchmark saved!")

    # Display benchmarks by type
    for test_type in ["2k", "6k", "30min", "500m", "step"]:
        tests = db.query(BenchmarkTest).filter(
            BenchmarkTest.test_type == test_type
        ).order_by(BenchmarkTest.date.desc()).all()

        if tests:
            st.subheader(f"{test_type.upper()} Tests")
            for t in tests:
                time_str = format_time(t.total_time_seconds) if t.total_time_seconds else "N/A"
                split_str = format_split(t.avg_split_seconds) if t.avg_split_seconds else "N/A"
                st.write(f"- **{t.date}**: Time: {time_str} | Split: {split_str} | Watts: {t.avg_watts or 'N/A'}")

    # Strength benchmarks
    st.subheader("Strength Benchmarks")
    with st.expander("Log Strength Test"):
        with st.form("strength_bm_form"):
            sb_date = st.date_input("Date", key="sb_date")
            sb_exercise = st.selectbox("Exercise", ["deadlift", "back_squat", "bench_pull", "weighted_pullup", "bent_row"])
            sb_type = st.selectbox("Test Type", ["1rm", "3rm", "5rm"])
            sb_weight = st.number_input("Weight (lbs)", min_value=0.0, value=0.0, step=5.0)

            if st.form_submit_button("Save Strength Benchmark"):
                sb = StrengthBenchmark(
                    date=sb_date,
                    exercise_name=sb_exercise,
                    test_type=sb_type,
                    weight_lbs=sb_weight,
                    bodyweight_lbs=160.0,
                    bw_ratio=round(sb_weight / 160.0, 2) if sb_weight else None,
                )
                db.add(sb)
                db.commit()
                st.success("Strength benchmark saved!")

    strength_bms = db.query(StrengthBenchmark).order_by(
        StrengthBenchmark.exercise_name, StrengthBenchmark.date.desc()
    ).all()

    if strength_bms:
        current_exercise = None
        for sb in strength_bms:
            if sb.exercise_name != current_exercise:
                current_exercise = sb.exercise_name
                st.markdown(f"**{current_exercise.replace('_', ' ').title()}**")
            st.write(f"  - {sb.date}: {sb.test_type.upper()} = {sb.weight_lbs} lbs (BW ratio: {sb.bw_ratio}x)")

    db.close()


# ── Training Plan ──────────────────────────────

elif page == "Training Plan":
    st.title("Training Plan")

    db = get_db()

    # Generate plan button
    phases = db.query(TrainingPhase).all()
    if not phases:
        if st.button("Generate Training Plan"):
            result = generate_full_plan(db)
            st.success(f"Plan generated: {result['total_workouts']} workouts across {result['phases']} phases")
            st.rerun()
    else:
        # Show phases
        st.subheader("Training Phases")
        for p in db.query(TrainingPhase).order_by(TrainingPhase.start_date).all():
            today = date.today()
            is_current = p.start_date <= today <= p.end_date
            marker = " (CURRENT)" if is_current else ""
            st.write(f"**{p.name.replace('_', ' ').title()}{marker}**: {p.start_date} → {p.end_date}")
            st.caption(p.focus)

        # Calendar view (2-week lookahead)
        st.subheader("Upcoming Workouts")
        start = date.today()
        end = start + timedelta(days=13)

        planned = db.query(PlannedWorkout).filter(
            PlannedWorkout.date >= start,
            PlannedWorkout.date <= end,
        ).order_by(PlannedWorkout.date).all()

        for w in planned:
            day_name = w.date.strftime("%A %b %d")
            color = {
                "steady_state": "🟢", "tempo": "🟡", "threshold": "🔴",
                "interval": "🔴", "race_pace": "🔴", "strength": "🟠",
                "rest": "⚪", "test": "🟣",
            }.get(w.workout_type, "⚪")

            with st.expander(f"{color} {day_name} — {w.title}"):
                st.write(w.description)
                if w.target_split_seconds:
                    st.metric("Target Split", format_split(w.target_split_seconds))
                if w.target_hr_low:
                    st.write(f"Target HR: {w.target_hr_low}-{w.target_hr_high}")
                if w.was_adjusted:
                    st.warning(f"Adjusted: {w.adjustment_reason}")

    db.close()


# ── Import Data ──────────────────────────────

elif page == "Import Data":
    st.title("Import Data")

    st.subheader("Concept2 Logbook CSV Import")
    st.markdown("""
**How to export your data from Concept2:**
1. Go to [log.concept2.com](https://log.concept2.com) and log in
2. Navigate to your logbook
3. Click the download/export button for the season you want
4. Save the CSV file to your computer
5. Upload it below
""")

    uploaded_file = st.file_uploader("Upload Concept2 CSV", type=["csv"])

    if uploaded_file is not None:
        # Save to data/raw/ directory
        import os
        save_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "data", "raw", uploaded_file.name,
        )
        with open(save_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.write(f"File saved: `{uploaded_file.name}`")

        # Preview
        import pandas as pd
        df_preview = pd.read_csv(save_path)
        st.write(f"**{len(df_preview)} rows found**")
        st.dataframe(df_preview.head(10))

        if st.button("Import to Database"):
            db = get_db()
            with st.spinner("Importing..."):
                stats = import_concept2_csv(db, save_path)
            db.close()

            if stats["errors"] > 0:
                st.warning(f"Imported {stats['imported']} workouts, skipped {stats['skipped']} duplicates, {stats['errors']} errors")
                for err in stats["error_details"][:10]:
                    st.caption(f"Error: {err}")
            else:
                st.success(f"Imported {stats['imported']} workouts, skipped {stats['skipped']} duplicates")

    # Show existing imported workouts
    db = get_db()
    imported_count = db.query(Workout).filter(Workout.source == "concept2_csv").count()
    st.divider()
    st.metric("Workouts Imported from Concept2", imported_count)
    db.close()


# ── Chat with Coach ──────────────────────────────

elif page == "Chat with Coach":
    st.title("Chat with Your AI Coach")
    st.caption("Ask questions about your training, performance, or plan.")

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # Chat input
    if prompt := st.chat_input("Ask your coach..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                db = get_db()
                coach = CoachAgent()
                response = coach.chat(db, prompt)
                db.close()
            st.write(response)

        st.session_state.messages.append({"role": "assistant", "content": response})

    # Suggested questions
    st.sidebar.subheader("Suggested Questions")
    suggestions = [
        "Am I on track for sub-6:30?",
        "Why was my split slower today?",
        "Should I take a rest day?",
        "What should I focus on this week?",
        "How is my recovery looking?",
        "Am I training too hard or too easy?",
    ]
    for s in suggestions:
        st.sidebar.caption(f"💬 {s}")
