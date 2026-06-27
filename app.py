# ============================================================
# app.py  —  CUMTA Traffic Intelligence Streamlit Application
#
# Run with:  streamlit run app.py
# ============================================================

import sys
import os

# Guarantee that the folder containing app.py is on the Python path.
# Streamlit Cloud sometimes runs from a different working directory,
# which causes "No module named 'utils'" even when the folder exists.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from utils.data_loader import load_csv, load_postgres, generate_demo, validate
from utils import analysis

# ── Page config (must be the very first Streamlit call) ──────────────────────
st.set_page_config(
    page_title = "CUMTA Traffic Intelligence",
    page_icon  = "🚦",
    layout     = "wide",
    initial_sidebar_state = "expanded",
)

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Subtle card behind metric boxes */
[data-testid="metric-container"] {
    background: #f7f9fc;
    border: 1px solid #e0e5eb;
    border-radius: 8px;
    padding: 12px 16px;
}
/* Tighten tab font */
[data-baseweb="tab"] > div { font-size: 13px; font-weight: 600; }
/* Remove top padding on main area */
.block-container { padding-top: 1.5rem; }
/* Download button */
.stDownloadButton > button {
    border: 1px solid #1f77b4;
    color: #1f77b4;
    background: white;
}
</style>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
#  SIDEBAR — Data Source & Navigation
# ════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 🚦 CUMTA Traffic\nIntelligence")
    st.markdown("---")

    # ── Data Source ──────────────────────────────────────────
    st.markdown("### 📂 Data Source")
    source = st.radio(
        "Choose input:",
        ["🧪 Demo Data", "📄 Upload CSV", "🗄️ PostgreSQL"],
        index=0,
        label_visibility="collapsed",
    )

    data = None   # will hold the loaded DataFrame

    # ── Demo Data ────────────────────────────────────────────
    if source == "🧪 Demo Data":
        n_rows = st.slider("Dataset size", 2000, 20000, 7000, 1000,
                           help="Rows of synthetic traffic observations")
        if st.button("🔄 Regenerate", use_container_width=True):
            st.cache_data.clear()
        with st.spinner("Generating demo data…"):
            data = generate_demo(n_rows=n_rows)
        st.success(f"✅ {len(data):,} rows · {data['shapefile_segment_name'].nunique()} segments")

    # ── CSV Upload ───────────────────────────────────────────
    elif source == "📄 Upload CSV":
        uploaded = st.file_uploader(
            "Drop your exported traffic CSV here",
            type=["csv"],
            help="Must include the columns listed in the Data Source & API Mapping Directory",
        )
        if uploaded:
            with st.spinner("Reading CSV…"):
                data = load_csv(uploaded.read())
            if data is not None:
                st.success(f"✅ {len(data):,} rows loaded")
        else:
            st.info("👆 Upload a CSV to begin")

    # ── PostgreSQL ───────────────────────────────────────────
    elif source == "🗄️ PostgreSQL":
        with st.expander("🔌 Connection Settings", expanded=True):
            pg_host   = st.text_input("Host",     value="localhost")
            pg_port   = st.number_input("Port",   value=5432, step=1, format="%d")
            pg_db     = st.text_input("Database", value="cumta_traffic")
            pg_user   = st.text_input("Username", value="postgres")
            pg_pass   = st.text_input("Password", type="password")
            pg_query  = st.text_area(
                "SQL Query",
                value="SELECT * FROM traffic_metrics ORDER BY RANDOM() LIMIT 10000;",
                height=90,
            )
        if st.button("🔗 Connect & Load", use_container_width=True, type="primary"):
            with st.spinner("Connecting to PostgreSQL…"):
                data = load_postgres(pg_host, int(pg_port), pg_db, pg_user, pg_pass, pg_query)
            if data is not None:
                st.success(f"✅ {len(data):,} rows loaded from DB")

    st.markdown("---")

    # ── Page Navigation ───────────────────────────────────────
    st.markdown("### 🗂️ Analysis Modules")
    NAV = {
        "🏠  Dashboard"            : "dash",
        "🔴  H1 — Bottleneck Map"  : "h1",
        "🕒  H2 — Temporal Peaks"  : "h2",
        "🌧️  H4 — Weather Impact"  : "h4",
        "🛣️  H7 — Flyover & Slope" : "h7",
        "📐  H8 — Length Dilution" : "h8",
        "📊  Raw Data Explorer"    : "explorer",
    }
    page_label = st.radio(
        "Go to:", list(NAV.keys()), index=0, label_visibility="collapsed"
    )
    page = NAV[page_label]

    st.markdown("---")
    st.caption("CUMTA Traffic Intelligence Pilot v1.0\nAll column names follow Data Source & API Mapping Directory v1.")


# ════════════════════════════════════════════════════════════
#  Guard — no data loaded yet
# ════════════════════════════════════════════════════════════
if data is None:
    st.markdown("## Welcome to CUMTA Traffic Intelligence 🚦")
    st.info("👈  Select a **Data Source** in the sidebar and load your data to begin.", icon="ℹ️")
    st.image(
        "https://upload.wikimedia.org/wikipedia/commons/thumb/4/41/"
        "Simple_icon_map.svg/800px-Simple_icon_map.svg.png",
        width=300,
    )
    st.stop()

# Validate available modules
vld = validate(data)


# ════════════════════════════════════════════════════════════
#  SHARED COLOUR PALETTES
# ════════════════════════════════════════════════════════════
CLASS_COLORS = {
    "Root Cause Bottleneck": "#d62728",
    "Spillover Victim"     : "#ff7f0e",
    "Free Flow"            : "#2ca02c",
}
WEATHER_COLORS = {
    "Dry"           : "#2ca02c",
    "Light Rain"    : "#17becf",
    "Moderate Rain" : "#ff7f0e",
    "Heavy Rain"    : "#d62728",
}
DAY_COLORS = {"Weekday": "#1f77b4", "Weekend": "#ff7f0e"}
LAYER_COLORS = {"Express": "#1f77b4", "At-Grade": "#d62728"}


# ════════════════════════════════════════════════════════════
#  PAGE: DASHBOARD
# ════════════════════════════════════════════════════════════
if page == "dash":
    st.title("🚦 CUMTA Traffic Intelligence — Overview Dashboard")
    st.caption("*Pilot analysis for the CUMTA transit corridor network*")
    st.markdown("---")

    # ── Top-level KPIs ────────────────────────────────────────
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("📦 Observations",     f"{len(data):,}")
    k2.metric("🗺️ Segments Tracked", f"{data['shapefile_segment_name'].nunique()}")
    k3.metric("📈 Mean Network TTI", f"{data['travel_time_index_tti'].mean():.3f}")
    k4.metric("⚠️ Max TTI Spike",    f"{data['travel_time_index_tti'].max():.2f}×")
    rain_col = "precipitation_intensity_mm_h"
    rain_pct = (data[rain_col] > 0.5).mean() * 100 if rain_col in data.columns else 0
    k5.metric("🌧️ Rainy Observations", f"{rain_pct:.1f}%")

    st.markdown("---")
    col_l, col_r = st.columns([3, 2])

    with col_l:
        # Network-wide TTI histogram
        fig = px.histogram(
            data, x="travel_time_index_tti", nbins=60,
            color_discrete_sequence=["#1f77b4"],
            title="Network-Wide TTI Distribution (all observations)",
            labels={"travel_time_index_tti": "Travel Time Index (TTI)"},
        )
        fig.add_vline(x=2.0, line_dash="dash", line_color="red",
                      annotation_text="Root Cause ≥ 2.0", annotation_position="top right")
        fig.add_vline(x=1.5, line_dash="dot", line_color="orange",
                      annotation_text="Spillover ≥ 1.5", annotation_position="top right")
        fig.update_layout(height=320, margin=dict(t=45, b=0, l=0, r=0),
                          showlegend=False, bargap=0.05)
        st.plotly_chart(fig, use_container_width=True)

    with col_r:
        # Segment class donut (quick H1 at default thresholds)
        h1_quick = analysis.run_h1(data)
        cc = h1_quick["class_counts"]
        pie_df = pd.DataFrame({"Class": list(cc.keys()), "Count": list(cc.values())})
        fig_pie = px.pie(
            pie_df, names="Class", values="Count",
            color="Class", color_discrete_map=CLASS_COLORS,
            title="Segment Class Distribution",
            hole=0.45,
        )
        fig_pie.update_traces(textposition="inside", textinfo="percent+label")
        fig_pie.update_layout(height=320, margin=dict(t=45, b=0, l=0, r=0),
                              showlegend=False)
        st.plotly_chart(fig_pie, use_container_width=True)

    # ── Module readiness ──────────────────────────────────────
    st.markdown("---")
    st.subheader("Analysis Module Readiness")
    m_cols = st.columns(5)
    module_meta = [
        ("H1", "Bottleneck Map",  "🔴"),
        ("H2", "Temporal Peaks",  "🕒"),
        ("H4", "Weather Impact",  "🌧️"),
        ("H7", "Flyover & Slope", "🛣️"),
        ("H8", "Length Dilution", "📐"),
    ]
    for i, (mod, name, icon) in enumerate(module_meta):
        ok  = mod in vld["available_modules"]
        lbl = "✅ Ready" if ok else "⚠️ Missing cols"
        m_cols[i].metric(f"{icon} {mod}", name, lbl)

    if vld["missing_core"]:
        st.warning(f"⚠️ Missing core columns: `{'`, `'.join(vld['missing_core'])}`")


# ════════════════════════════════════════════════════════════
#  PAGE: H1 — BOTTLENECK LOCALIZATION
# ════════════════════════════════════════════════════════════
elif page == "h1":
    st.title("🔴 H1 — Systemic Bottleneck Localization")
    st.info(
        "**Business Question:** Which micro-segments are root-cause bottlenecks "
        "creating cascading spillover queues, and where should engineers focus first?",
        icon="❓",
    )

    # Controls
    c1, c2, c3 = st.columns(3)
    root_t  = c1.slider("Root Cause TTI Threshold",  1.5, 5.0, 2.0, 0.1,
                         help="Segments with mean TTI ≥ this = primary bottleneck")
    spill_t = c2.slider("Spillover TTI Threshold",   1.1, root_t - 0.1, 1.5, 0.1,
                         help="Segments with mean TTI ≥ this = absorbing queue overflow")
    top_n   = c3.slider("Top N to Display",          5,
                         min(50, data["shapefile_segment_name"].nunique()), 20)

    # Run
    h1 = analysis.run_h1(data, root_t, spill_t)
    seg = h1["segment_tti"]
    cc  = h1["class_counts"]

    # KPIs
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("🔴 Root Cause Segments", cc.get("Root Cause Bottleneck", 0),
              f"Mean TTI ≥ {root_t}")
    k2.metric("🟠 Spillover Victims", cc.get("Spillover Victim", 0),
              f"TTI {spill_t} – {root_t}")
    k3.metric("🟢 Free Flow Segments", cc.get("Free Flow", 0),
              f"TTI < {spill_t}")
    worst = seg.iloc[0]
    k4.metric("⬆️ Worst Segment",
              f"{worst['mean_tti']:.3f} TTI",
              worst["shapefile_segment_name"])

    st.markdown("---")
    tab1, tab2, tab3 = st.tabs(["📊 Ranking Chart", "📋 Priority Table", "📉 TTI Distribution"])

    with tab1:
        plot_seg = seg.head(top_n).copy()
        fig = px.bar(
            plot_seg.sort_values("mean_tti"),
            x="mean_tti", y="shapefile_segment_name",
            color="congestion_class",
            color_discrete_map=CLASS_COLORS,
            orientation="h",
            title=f"Top {top_n} Segments — Mean TTI Severity (hover for full stats)",
            labels={
                "mean_tti"              : "Mean TTI",
                "shapefile_segment_name": "Segment",
                "congestion_class"      : "Classification",
            },
            hover_data={
                "mean_tti"             : ":.3f",
                "max_tti"              : ":.3f",
                "p90_tti"              : ":.3f",
                "mean_absolute_delay_s": ":.1f",
                "observation_count"    : True,
            },
        )
        fig.add_vline(x=root_t, line_dash="dash", line_color="red",
                      annotation_text=f"Root Cause ({root_t})")
        fig.add_vline(x=spill_t, line_dash="dot", line_color="orange",
                      annotation_text=f"Spillover ({spill_t})")
        fig.update_layout(height=max(420, top_n * 24),
                          margin=dict(l=0, r=30, t=50, b=0))
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        class_filter = st.multiselect(
            "Filter by class:", seg["congestion_class"].unique().tolist(),
            default=seg["congestion_class"].unique().tolist(),
        )
        display_cols = [
            "priority_rank", "shapefile_segment_name", "congestion_class",
            "mean_tti", "max_tti", "p90_tti", "mean_absolute_delay_s", "observation_count",
        ]
        avail = [c for c in display_cols if c in seg.columns]
        filtered_seg = seg[seg["congestion_class"].isin(class_filter)][avail]

        st.dataframe(
            filtered_seg.style
            .format({"mean_tti": "{:.3f}", "max_tti": "{:.3f}",
                     "p90_tti": "{:.3f}", "mean_absolute_delay_s": "{:.1f}s"})
            .background_gradient(subset=["mean_tti"], cmap="RdYlGn_r"),
            use_container_width=True, height=420,
        )
        st.download_button(
            "⬇️ Download Priority List (CSV)",
            filtered_seg.to_csv(index=False).encode(),
            "H1_bottleneck_priority.csv", "text/csv",
        )

    with tab3:
        fig = px.histogram(
            seg, x="mean_tti", nbins=30,
            color="congestion_class", color_discrete_map=CLASS_COLORS,
            barmode="overlay", opacity=0.75,
            title="Distribution of Per-Segment Mean TTI",
            labels={"mean_tti": "Mean TTI per Segment", "congestion_class": "Class"},
        )
        fig.update_layout(height=380)
        st.plotly_chart(fig, use_container_width=True)


# ════════════════════════════════════════════════════════════
#  PAGE: H2 — TEMPORAL PEAKS
# ════════════════════════════════════════════════════════════
elif page == "h2":
    st.title("🕒 H2 — Temporal Peak Profiling & Network Failure Rates")
    st.info(
        "**Business Question:** At what exact hour does the network fail, how long does "
        "recovery take, and how does the pattern shift on weekends vs weekdays?",
        icon="❓",
    )

    c1, c2 = st.columns(2)
    fail_t    = c1.slider("Failure TTI Threshold", 1.5, 4.0, 2.0, 0.1,
                           help="A segment 'fails' when its TTI crosses this value")
    clear_base = c2.slider("Clearance Baseline TTI", 1.0, 1.5, 1.2, 0.05,
                            help="Network is 'clear' once mean TTI drops below this")

    h2 = analysis.run_h2(data, fail_t, clear_base)
    hp = h2["hourly_profile"]
    wd = h2["weekday_stats"]
    we = h2["weekend_stats"]

    # KPIs
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("📈 Weekday Peak Hour", f"{wd.get('peak_hour', '--'):02d}:00",
              f"TTI = {wd.get('peak_tti', '--')}")
    k2.metric("📈 Weekend Peak Hour", f"{we.get('peak_hour', '--'):02d}:00",
              f"TTI = {we.get('peak_tti', '--')}")
    ch = wd.get("clear_hour", -1)
    k3.metric(
        "⬇️ Weekday Clearance",
        f"{ch:02d}:00" if ch > 0 else "Doesn't clear",
        f"{wd.get('congested_hours', 0)}h in congestion",
    )
    k4.metric("🔴 Peak Failure Rate", f"{hp['failure_rate_pct'].max():.1f}%",
              "of segments in severe congestion")

    st.markdown("---")
    tab1, tab2, tab3 = st.tabs(
        ["📈 24-Hour TTI Profile", "📊 Hourly Failure Rate", "🗺️ Segment × Hour Heatmap"]
    )

    with tab1:
        day_sel = st.multiselect("Day types:", ["Weekday", "Weekend"],
                                  default=["Weekday", "Weekend"])
        hp_plot = hp[hp["day_type"].isin(day_sel)]

        fig = go.Figure()
        for dtype, grp in hp_plot.groupby("day_type"):
            grp  = grp.sort_values("hour_of_day")
            col  = DAY_COLORS.get(dtype, "gray")
            # Confidence band
            fig.add_trace(go.Scatter(
                x=pd.concat([grp["hour_of_day"], grp["hour_of_day"][::-1]]),
                y=pd.concat([grp["mean_tti"] + grp["std_tti"],
                             (grp["mean_tti"] - grp["std_tti"])[::-1]]),
                fill="toself",
                fillcolor=col + "26",   # 15 % opacity hex
                line=dict(width=0), showlegend=False,
            ))
            # Main line
            fig.add_trace(go.Scatter(
                x=grp["hour_of_day"], y=grp["mean_tti"],
                mode="lines+markers", name=f"{dtype} (mean)",
                line=dict(color=col, width=2.5), marker=dict(size=5),
                hovertemplate=(
                    f"<b>{dtype}</b><br>"
                    "Hour: %{x:02d}:00<br>"
                    "Mean TTI: %{y:.3f}<extra></extra>"
                ),
            ))

        fig.add_hline(y=fail_t,    line_dash="dash", line_color="red",
                      annotation_text=f"Failure Threshold ({fail_t})")
        fig.add_hline(y=1.5,       line_dash="dot",  line_color="orange",
                      annotation_text="Congestion Onset (1.5)")
        fig.add_hline(y=clear_base, line_dash="dot", line_color="green",
                      annotation_text=f"Clearance Baseline ({clear_base})")
        fig.update_layout(
            title="24-Hour Mean TTI Profile (shaded = ±1 std dev)",
            xaxis=dict(title="Hour of Day", tickvals=list(range(24)),
                       ticktext=[f"{h:02d}:00" for h in range(24)], tickangle=45),
            yaxis=dict(title="Mean Travel Time Index (TTI)"),
            hovermode="x unified", height=430,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        )
        st.plotly_chart(fig, use_container_width=True)

        # Summary table
        st.markdown("**Peak & Clearance Summary:**")
        sum_rows = []
        for s in [wd, we]:
            ch_ = s.get("clear_hour", -1)
            sum_rows.append({
                "Day Type"         : s.get("label", ""),
                "Peak Hour"        : f"{s.get('peak_hour', '--'):02d}:00",
                "Peak TTI"         : s.get("peak_tti", "--"),
                "Clearance Hour"   : f"{ch_:02d}:00" if ch_ > 0 else "Doesn't clear",
                "Clearance Window" : f"{ch_ - s.get('peak_hour', ch_)}h" if ch_ > 0 else "–",
                "Hours Congested"  : f"{s.get('congested_hours', 0)}h",
            })
        st.dataframe(pd.DataFrame(sum_rows), use_container_width=True, hide_index=True)

    with tab2:
        fig = px.bar(
            hp, x="hour_of_day", y="failure_rate_pct",
            color="day_type", barmode="group",
            color_discrete_map=DAY_COLORS,
            title=f"% of Segments with TTI ≥ {fail_t} (Network Failure Rate) by Hour",
            labels={
                "hour_of_day"      : "Hour of Day",
                "failure_rate_pct" : f"Failure Rate (% segments TTI ≥ {fail_t})",
                "day_type"         : "Day Type",
            },
        )
        fig.update_xaxes(tickvals=list(range(24)),
                          ticktext=[f"{h:02d}:00" for h in range(24)], tickangle=45)
        fig.update_layout(height=380)
        st.plotly_chart(fig, use_container_width=True)

        st.download_button(
            "⬇️ Download Hourly Profile (CSV)",
            hp.to_csv(index=False).encode(),
            "H2_hourly_profile.csv", "text/csv",
        )

    with tab3:
        hm = h2["heatmap_data"]
        if hm is not None and not hm.empty:
            fig = px.imshow(
                hm,
                labels=dict(x="Hour of Day", y="Segment", color="Mean TTI"),
                title="Segment × Hour Mean TTI Heatmap (red = congested)",
                color_continuous_scale="RdYlGn_r",
                aspect="auto",
            )
            fig.update_xaxes(
                tickvals=list(range(24)),
                ticktext=[f"{h:02d}:00" for h in range(24)],
                tickangle=45,
            )
            fig.update_layout(height=max(400, hm.shape[0] * 18))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Heatmap requires shapefile_segment_name and hour_of_day columns.")


# ════════════════════════════════════════════════════════════
#  PAGE: H4 — WEATHER IMPACT
# ════════════════════════════════════════════════════════════
elif page == "h4":
    st.title("🌧️ H4 — Weather-Driven Environmental Variance")
    st.info(
        "**Business Question:** How much does rain degrade network capacity vs a dry day, "
        "and can we mathematically isolate weather anomaly events?",
        icon="❓",
    )

    if "precipitation_intensity_mm_h" not in data.columns:
        st.error("❌ Column `precipitation_intensity_mm_h` not found in dataset.")
        st.stop()

    c1, c2 = st.columns(2)
    anom_m    = c1.slider("Anomaly TTI Multiplier", 1.1, 2.0, 1.4, 0.05,
                           help="Event flags as anomaly when TTI ≥ dry_baseline × this")
    rain_sig  = c2.slider("Rain Significance Threshold (mm/hr)", 0.5, 7.6, 2.5, 0.5,
                           help="Minimum rain intensity to qualify as a weather anomaly")

    h4 = analysis.run_h4(data, anom_m, rain_sig)
    wi = h4["weather_impact"]

    # KPIs
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("☀️ Dry Baseline TTI", f"{h4['dry_base']:.3f}")
    heavy_up = wi[wi["weather_condition"] == "Heavy Rain"]["tti_uplift_pct"].values
    k2.metric("⛈️ Heavy Rain Uplift",
              f"{heavy_up[0]:+.1f}%" if len(heavy_up) > 0 and not np.isnan(heavy_up[0]) else "N/A",
              "vs dry baseline")
    k3.metric("📐 Rain Sensitivity",
              f"{h4['slope_r']:.4f} TTI/mm·hr⁻¹",
              f"R² = {h4['r_r']**2:.3f}")
    k4.metric("👁️ Visibility Correlation",
              f"r = {h4['vis_r']:.3f}",
              "p < 0.05 ✅" if h4["vis_p"] < 0.05 else "Not significant ❌")

    st.markdown("---")
    tab1, tab2, tab3 = st.tabs(
        ["☁️ Weather Class Impact", "📉 Rain Sensitivity Regression", "🚨 Anomaly Segments"]
    )

    with tab1:
        fig = go.Figure()
        for _, row in wi.iterrows():
            if pd.isna(row["mean_tti"]):
                continue
            wc = str(row["weather_condition"])
            fig.add_trace(go.Bar(
                name=wc, x=[wc], y=[row["mean_tti"]],
                error_y=dict(type="data", array=[row["std_tti"]], visible=True),
                marker_color=WEATHER_COLORS.get(wc, "gray"),
                hovertemplate=(
                    f"<b>{wc}</b><br>"
                    f"Mean TTI: {row['mean_tti']:.3f}<br>"
                    f"Uplift vs Dry: {row['tti_uplift_abs']:+.3f} "
                    f"({row['tti_uplift_pct']:+.1f}%)<br>"
                    f"Std Dev: {row['std_tti']:.3f}<br>"
                    f"N: {int(row['sample_count'])}<extra></extra>"
                ),
            ))

        fig.add_hline(y=h4["dry_base"], line_dash="dash", line_color="green",
                      annotation_text=f"Dry Baseline TTI = {h4['dry_base']:.3f}")
        fig.update_layout(
            title="Mean TTI by Weather Condition (± 1 Std Dev error bars)",
            yaxis_title="Mean Travel Time Index (TTI)",
            xaxis_title="Weather Condition (severity increases →)",
            showlegend=False, height=420,
        )
        st.plotly_chart(fig, use_container_width=True)

        # Impact table
        tbl = wi[["weather_condition", "mean_tti", "tti_uplift_abs",
                   "tti_uplift_pct", "sample_count"]].copy()
        tbl.columns = ["Weather Class", "Mean TTI", "Uplift (abs)",
                        "Uplift (%)", "N Observations"]
        st.dataframe(
            tbl.style.format({
                "Mean TTI"      : "{:.3f}",
                "Uplift (abs)"  : "{:+.3f}",
                "Uplift (%)"    : "{:+.1f}",
                "N Observations": "{:.0f}",
            }),
            use_container_width=True, hide_index=True, height=200,
        )

    with tab2:
        rain_rows = h4["df_tagged"][h4["df_tagged"]["precipitation_intensity_mm_h"] > 0]
        sample_n  = min(5000, len(rain_rows))
        plot_rain = rain_rows.sample(sample_n, random_state=42) if sample_n > 0 else rain_rows

        fig = px.scatter(
            plot_rain,
            x="precipitation_intensity_mm_h",
            y="travel_time_index_tti",
            color="weather_condition",
            color_discrete_map=WEATHER_COLORS,
            opacity=0.40,
            title=(
                f"Rain Sensitivity Regression  "
                f"(R² = {h4['r_r']**2:.3f} | p = {h4['p_r']:.2e})"
            ),
            labels={
                "precipitation_intensity_mm_h": "Precipitation Intensity (mm/hr)",
                "travel_time_index_tti"        : "Travel Time Index (TTI)",
                "weather_condition"            : "Weather Condition",
            },
        )
        x_range = np.linspace(
            data["precipitation_intensity_mm_h"].min(),
            data["precipitation_intensity_mm_h"].max(), 300,
        )
        fig.add_trace(go.Scatter(
            x=x_range,
            y=h4["slope_r"] * x_range + h4["intercept_r"],
            mode="lines", name=f"OLS  slope = {h4['slope_r']:.4f}",
            line=dict(color="black", width=2.5, dash="dash"),
        ))
        fig.update_layout(height=430)
        st.plotly_chart(fig, use_container_width=True)

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown(f"""
**OLS Rain Sensitivity Slope:**

| Metric | Value |
|--------|-------|
| Slope (TTI per mm/hr rain) | `{h4['slope_r']:.5f}` |
| Intercept | `{h4['intercept_r']:.4f}` |
| R² | `{h4['r_r']**2:.4f}` |
| p-value | `{h4['p_r']:.4e}` |
| Significance | {'✅ p < 0.05' if h4['p_r'] < 0.05 else '❌ p ≥ 0.05'} |
""")
        with col_b:
            st.markdown(f"""
**Visibility ↔ TTI Correlation:**

| Metric | Value |
|--------|-------|
| Pearson r | `{h4['vis_r']:.4f}` |
| p-value | `{h4['vis_p']:.4e}` |
| Significance | {'✅ p < 0.05' if h4['vis_p'] < 0.05 else '❌ p ≥ 0.05'} |
| Direction | {'Negative ✓ (lower vis → higher TTI)' if h4['vis_r'] < 0 else 'Positive (check data)'} |
""")

    with tab3:
        anom_df = h4["anomaly_by_seg"][h4["anomaly_by_seg"]["anomaly_event_count"] > 0].head(20)
        if len(anom_df) > 0:
            fig = px.bar(
                anom_df.sort_values("anomaly_event_count"),
                x="anomaly_event_count", y="shapefile_segment_name",
                orientation="h",
                color="anomaly_event_count",
                color_continuous_scale="Reds",
                title=(
                    f"Most Rain-Sensitive Segments "
                    f"(TTI ≥ baseline × {anom_m} AND rain ≥ {rain_sig} mm/hr)"
                ),
                labels={
                    "anomaly_event_count"   : "Weather Anomaly Event Count",
                    "shapefile_segment_name": "Segment",
                },
            )
            fig.update_layout(height=420, coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)
            st.download_button(
                "⬇️ Download Anomaly Rankings (CSV)",
                h4["anomaly_by_seg"].to_csv(index=False).encode(),
                "H4_weather_anomaly.csv", "text/csv",
            )
        else:
            st.info("No anomaly events detected with current thresholds — try lowering the sliders.")


# ════════════════════════════════════════════════════════════
#  PAGE: H7 — FLYOVER & GRADIENT
# ════════════════════════════════════════════════════════════
elif page == "h7":
    st.title("🛣️ H7 — Flyover Exit & Uphill Gradient Penalties")
    st.info(
        "**Business Question:** Do steep inclines permanently slow heavy fleets? "
        "Do express flyovers eliminate congestion or simply relocate it to the exit ramp?",
        icon="❓",
    )

    for col in ["segment_slope_grade", "network_layer_type"]:
        if col not in data.columns:
            st.error(f"❌ Required column `{col}` not found in dataset.")
            st.stop()

    h7       = analysis.run_h7(data)
    lt       = h7["layer_tti"]
    slope_df = h7["slope_tti"]

    exp_row = lt[lt["network_layer_type"] == "Express"]["mean_tti"]
    agr_row = lt[lt["network_layer_type"] == "At-Grade"]["mean_tti"]

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("🚧 At-Grade Mean TTI", f"{agr_row.values[0]:.3f}" if len(agr_row) > 0 else "N/A")
    k2.metric("🌉 Express Mean TTI",  f"{exp_row.values[0]:.3f}" if len(exp_row) > 0 else "N/A")
    k3.metric("📊 Welch t-statistic",  f"{h7['t_stat']:.3f}",
              "✅ Significant" if h7["t_pval"] < 0.05 else "❌ Not significant")
    k4.metric("🔴 Exit Queue Candidates", len(h7["exit_cands"]),
              f"At-Grade TTI ≥ {h7['exit_thresh']:.2f}")

    st.markdown("---")
    tab1, tab2, tab3 = st.tabs(
        ["🌉 Layer Type Comparison", "⛰️ Slope Analysis", "🗺️ Interaction Heatmap"]
    )

    with tab1:
        col_a, col_b = st.columns([3, 2])
        with col_a:
            fig = px.bar(
                lt, x="network_layer_type", y="mean_tti", error_y="std_tti",
                color="network_layer_type", color_discrete_map=LAYER_COLORS,
                text="mean_tti",
                title="Express Flyover vs At-Grade Ground — Mean TTI",
                labels={"mean_tti": "Mean TTI (± Std Dev)",
                        "network_layer_type": "Infrastructure Type"},
            )
            fig.update_traces(texttemplate="%{text:.3f}", textposition="outside")
            fig.update_layout(showlegend=False, height=380)
            st.plotly_chart(fig, use_container_width=True)

        with col_b:
            st.markdown("#### Statistical Test")
            sig_label = "✅ SIGNIFICANT" if h7["t_pval"] < 0.05 else "❌ NOT significant"
            st.markdown(f"""
| Metric | Value |
|--------|-------|
| t-statistic | `{h7['t_stat']:.4f}` |
| p-value | `{h7['t_pval']:.4e}` |
| Result | **{sig_label}** |

The TTI gap between Express and At-Grade is
{'**statistically confirmed** — flyovers and at-grade roads perform measurably differently.' if h7['t_pval'] < 0.05
 else '**not yet confirmed** — may need more data or longer observation window.'}

#### Top Exit Queue Candidates
*(Highest-TTI At-Grade segments — likely absorbing flyover discharge)*
""")
            st.dataframe(
                h7["exit_cands"].head(10)
                .rename(columns={"shapefile_segment_name": "Segment", "mean_tti": "Mean TTI"})
                .style.format({"Mean TTI": "{:.3f}"}),
                use_container_width=True, height=240, hide_index=True,
            )

    with tab2:
        fig_bar = px.bar(
            slope_df.dropna(subset=["mean_tti"]),
            x="slope_category", y="mean_tti", error_y="std_tti",
            color="mean_tti", color_continuous_scale="RdYlGn_r",
            text="mean_tti",
            title="Mean TTI by Topographic Slope Category",
            labels={"slope_category": "Slope Category",
                    "mean_tti": "Mean TTI (± Std Dev)"},
        )
        fig_bar.update_traces(texttemplate="%{text:.3f}", textposition="outside")
        fig_bar.update_layout(height=380, coloraxis_showscale=False)
        st.plotly_chart(fig_bar, use_container_width=True)

        # Box plot — TTI distribution per slope × layer
        box_data = h7["df_tagged"].dropna(subset=["slope_category"])
        fig_box = px.box(
            box_data, x="slope_category", y="travel_time_index_tti",
            color="network_layer_type", color_discrete_map=LAYER_COLORS,
            title="TTI Distribution by Slope Category × Network Layer",
            labels={"travel_time_index_tti": "Travel Time Index (TTI)",
                    "slope_category"        : "Slope Category",
                    "network_layer_type"    : "Layer"},
        )
        fig_box.update_layout(height=380)
        st.plotly_chart(fig_box, use_container_width=True)

    with tab3:
        piv = h7["pivot"]
        if piv is not None and not piv.empty:
            fig = px.imshow(
                piv,
                labels=dict(x="Slope Category", y="Network Layer", color="Mean TTI"),
                title="TTI Heatmap: Infrastructure Layer × Slope Category",
                color_continuous_scale="RdYlGn_r",
                text_auto=".2f",
                aspect="auto",
            )
            fig.update_layout(height=280)
            st.plotly_chart(fig, use_container_width=True)
            st.caption(
                "Darker cells = higher congestion. "
                "The worst-case combination is the intersection most in need of structural intervention."
            )
        else:
            st.warning("Could not build the heatmap — check that both columns are present and non-empty.")


# ════════════════════════════════════════════════════════════
#  PAGE: H8 — LENGTH DILUTION
# ════════════════════════════════════════════════════════════
elif page == "h8":
    st.title("📐 H8 — Spatial Slicing Accuracy & 'Length Dilution'")
    st.info(
        "**Business Question:** Does routing APIs' end-to-end segment measurement hide "
        "severe localised traffic jams by averaging them with free-flow stretches?",
        icon="❓",
    )

    if "true_driving_distance_meters" not in data.columns:
        st.error("❌ Column `true_driving_distance_meters` not found in dataset.")
        st.stop()

    n_q = st.select_slider("Length bin count:", [3, 4, 5, 6], value=4,
                            help="Number of equal-frequency bins to group segments by length")

    h8  = analysis.run_h8(data, n_q)
    ss  = h8["segment_spatial"]

    # KPIs
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("🗂️ Segments Analysed", len(ss))
    direction = "⬇️ Confirms dilution" if h8["corr_r"] < -0.15 else "Weak / inconclusive"
    k2.metric("🔗 Pearson r (Length vs Peak TTI)", f"{h8['corr_r']:.4f}", direction)
    k3.metric("📉 TTI drop per 100m longer", f"{h8['slope'] * 100:.4f}",
              f"R² = {h8['r_val']**2:.3f}")
    max_gap_row = ss.iloc[0] if len(ss) > 0 else None
    k4.metric(
        "⚠️ Highest Dilution Gap",
        f"{max_gap_row['dilution_gap']:.3f}" if max_gap_row is not None else "–",
        max_gap_row["shapefile_segment_name"] if max_gap_row is not None else "",
    )

    st.markdown("---")
    tab1, tab2, tab3 = st.tabs(
        ["📉 Length vs Peak TTI", "📊 Quartile Analysis", "📋 Dilution Gap Ranking"]
    )

    with tab1:
        x_line = np.linspace(ss["true_driving_distance_meters"].min(),
                              ss["true_driving_distance_meters"].max(), 300)
        fig = px.scatter(
            ss,
            x="true_driving_distance_meters",
            y="max_peak_tti",
            color="dilution_gap_pct",
            color_continuous_scale="YlOrRd",
            hover_name="shapefile_segment_name",
            hover_data={
                "mean_tti"                   : ":.3f",
                "dilution_gap"               : ":.3f",
                "dilution_gap_pct"           : ":.1f",
                "true_driving_distance_meters": ":.0f",
            },
            title=(
                f"Segment Length vs Maximum Peak TTI  "
                f"(Pearson r = {h8['corr_r']:.4f} | p = {h8['corr_p']:.2e})"
            ),
            labels={
                "true_driving_distance_meters": "True Driving Distance (meters)",
                "max_peak_tti"               : "Maximum Peak TTI Spike",
                "dilution_gap_pct"           : "Dilution Gap %",
            },
        )
        fig.add_trace(go.Scatter(
            x=x_line,
            y=h8["slope"] * x_line + h8["intercept"],
            mode="lines",
            name=f"OLS  slope = {h8['slope']:.5f}",
            line=dict(color="red", width=2.5, dash="dash"),
        ))
        fig.update_layout(height=450)
        st.plotly_chart(fig, use_container_width=True)

        st.markdown(f"""
**Interpretation:**
- A **negative slope** + significant p-value → longer segments *suppress* detectable peak TTI → dilution hypothesis confirmed.
- Current slope: `{h8['slope']:.5f}` TTI units per additional metre of segment length.
- Every extra **100m** of segment length hides `{h8['slope'] * 100:.4f}` TTI units of peak congestion.
""")

    with tab2:
        qs = h8["quartile_stats"]
        if not qs.empty:
            col_a, col_b = st.columns(2)
            with col_a:
                fig = px.bar(
                    qs, x="length_quartile", y="mean_of_max_peak_tti",
                    color="mean_dilution_gap_pct", color_continuous_scale="YlOrRd",
                    text="mean_dilution_gap_pct",
                    title="Mean Peak TTI by Segment Length Quartile",
                    labels={"length_quartile"      : "Quartile (Q1 = shortest)",
                            "mean_of_max_peak_tti" : "Mean of Max Peak TTI",
                            "mean_dilution_gap_pct": "Avg Dilution Gap %"},
                )
                fig.update_traces(texttemplate="Gap: %{text:.1f}%", textposition="outside")
                fig.update_layout(height=370, coloraxis_showscale=False)
                st.plotly_chart(fig, use_container_width=True)

            with col_b:
                tbl = qs[["length_quartile", "avg_length_m", "mean_of_max_peak_tti",
                           "mean_dilution_gap", "mean_dilution_gap_pct", "segment_count"]].copy()
                tbl.columns = ["Quartile", "Avg Length (m)", "Mean Peak TTI",
                                "Avg Dilution Gap", "Gap %", "N Segments"]
                st.dataframe(
                    tbl.style.format({
                        "Avg Length (m)" : "{:.0f}",
                        "Mean Peak TTI"  : "{:.3f}",
                        "Avg Dilution Gap": "{:.3f}",
                        "Gap %"          : "{:.1f}%",
                    }).background_gradient(subset=["Mean Peak TTI"], cmap="RdYlGn_r"),
                    use_container_width=True, hide_index=True, height=240,
                )
                st.markdown(f"""
**OLS Regression:**
- Slope: `{h8['slope']:.6f}` TTI/m
- R²: `{h8['r_val']**2:.4f}`
- p-value: `{h8['p_val']:.4e}` {'✅' if h8['p_val'] < 0.05 else '❌'}
""")
        else:
            st.warning("Not enough distinct length values for quartile binning — upload a larger dataset.")

    with tab3:
        top_dil = ss.head(20)
        fig = px.bar(
            top_dil,
            x="dilution_gap",
            y="shapefile_segment_name",
            orientation="h",
            color="dilution_gap_pct",
            color_continuous_scale="YlOrRd",
            title="Top 20 Segments — Hidden Micro-Congestion (Dilution Gap = Max TTI − Mean TTI)",
            labels={
                "dilution_gap"           : "Dilution Gap (Max Peak TTI − Mean TTI)",
                "shapefile_segment_name" : "Segment",
                "dilution_gap_pct"       : "Gap %",
            },
            hover_data={
                "true_driving_distance_meters": ":.0f",
                "mean_tti"                    : ":.3f",
                "max_peak_tti"                : ":.3f",
                "dilution_gap_pct"            : ":.1f",
            },
        )
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)

        st.caption(
            "A high dilution gap means the segment's **average TTI looks acceptable** "
            "but it regularly experiences **extreme local spikes** that a conventional "
            "routing API would completely miss."
        )
        st.download_button(
            "⬇️ Download Dilution Gap Analysis (CSV)",
            ss.to_csv(index=False).encode(),
            "H8_dilution_analysis.csv", "text/csv",
        )


# ════════════════════════════════════════════════════════════
#  PAGE: RAW DATA EXPLORER
# ════════════════════════════════════════════════════════════
elif page == "explorer":
    st.title("📊 Raw Data Explorer")
    st.markdown("Filter and inspect the loaded dataset, then download your slice.")

    col_f1, col_f2, col_f3, col_f4 = st.columns(4)

    with col_f1:
        all_segs = sorted(data["shapefile_segment_name"].unique().tolist())
        seg_sel  = st.multiselect("Segments:", all_segs, default=all_segs[:5],
                                   help="Leave empty to show all")

    with col_f2:
        hour_range = st.slider("Hour range:", 0, 23, (0, 23))

    with col_f3:
        tti_min = float(data["travel_time_index_tti"].min())
        tti_max = float(data["travel_time_index_tti"].max())
        tti_range = st.slider("TTI range:", tti_min, tti_max,
                               (tti_min, tti_max), step=0.1)

    with col_f4:
        day_filter = st.multiselect("Day type:", ["Weekday", "Weekend"],
                                     default=["Weekday", "Weekend"])
        day_codes  = []
        if "Weekday" in day_filter: day_codes.append(0)
        if "Weekend" in day_filter: day_codes.append(1)

    # Apply filters
    mask = (
        (data["hour_of_day"].between(*hour_range)) &
        (data["travel_time_index_tti"].between(*tti_range)) &
        (data["is_weekend"].isin(day_codes))
    )
    if seg_sel:
        mask &= data["shapefile_segment_name"].isin(seg_sel)

    filtered = data[mask].copy()

    st.metric("Filtered rows", f"{len(filtered):,} / {len(data):,}")
    st.dataframe(filtered, use_container_width=True, height=480)

    st.download_button(
        "⬇️ Download Filtered Dataset (CSV)",
        filtered.to_csv(index=False).encode(),
        "cumta_filtered_export.csv", "text/csv",
    )
