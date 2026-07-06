import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
import traceback

# 1. Page Configuration & Professional Engineering Styling Enforcements
st.set_page_config(
    page_title="CUMTA Corridor Diagnostics Suite",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom injection for scannable UI visual formatting rules
st.markdown("""
    <style>
    .main .block-container { padding-top: 2rem; }
    h1, h2, h3 { font-weight: 700 !important; color: #1e293b; }
    div.stButton > button:first-child {
        background-color: #1f77b4; color: white; border-radius: 6px; font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# =============================================================================
# 2. MASTER ENGINE INTERFACE CONTROLLER
# =============================================================================
def main():
    st.title("CUMTA Core Transit Network Diagnostics Cockpit")
    st.markdown("### Integrated 3D Spatial-Temporal Network Performance & Anomaly Analytics Framework")
    st.write("---")
    
    # Sidebar data intake section
    st.sidebar.title("Data Engine Intake")
    uploaded_file = st.sidebar.file_uploader(
        label="Upload Traffic Telemetry CSV File",
        type=["csv"],
        help="Provide the synthetic_telemetry_21_days.csv file here to feed the pipeline indices."
    )
    
    # Guard clause: Stop processing if a data asset is not supplied to the cloud engine
    if uploaded_file is None:
        st.info("ℹ️ Application Awaiting Dataset Ingestion. Please upload 'synthetic_telemetry_21_days.csv' via the sidebar menu panel to run the analytics.")
        return

    # Ingest the file into memory via standard pandas
    try:
        df_fetched = pd.read_csv(uploaded_file)
        
        # Global standardization formatting enforcements across all telemetry slices
        df_fetched['shapefile_segment_name'] = df_fetched['shapefile_segment_name'].astype(str).str.upper()
        
        # FIXED PARSING LAYER: Enforced dayfirst parsing with mixed format fallback strategies
        if 'execution_timestamp' in df_fetched.columns:
            df_fetched['execution_timestamp'] = pd.to_datetime(
                df_fetched['execution_timestamp'], 
                format='mixed', 
                dayfirst=True
            )
            df_fetched['derived_hour'] = df_fetched['execution_timestamp'].dt.hour
        elif 'hour_of_day' in df_fetched.columns:
            df_fetched['derived_hour'] = df_fetched['hour_of_day'].astype(int)
        elif 'execution_hour' in df_fetched.columns:
            df_fetched['derived_hour'] = df_fetched['execution_hour'].astype(int)
        else:
            df_fetched['derived_hour'] = 8 
            
    except Exception as err:
        st.error("Failed to parse the uploaded CSV file. Verify it matches the standard CUMTA telemetry structure.")
        with st.expander("Expand Traceback Logistics"):
            st.code(traceback.format_exc())
        return

    # =============================================================================
    # 3. SIDEBAR NAVIGATION TAB MENU CONTROL PANEL
    # =============================================================================
    st.sidebar.write("---")
    st.sidebar.title("Network Modules Menu")
    
    selected_tab = st.sidebar.radio(
        label="Select Diagnostic Framework",
        options=[
            "Dataset Overview & Audit Table",
            "Hypothesis 1: Systemic Bottleneck Localization",
            "Hypothesis 2: Temporal Peak Profiling",
            "Hypothesis 3: Geometric Constraints",
            "Hypothesis 4: Weather-Driven Variance",
            "Hypothesis 5: Tidal Flow Asymmetry",
            "Hypothesis 6: Commuter Uncertainty",
            "Hypothesis 7: The Flyover Exit & Gradients",
            "Hypothesis 8: Spatial Length Dilution Bias",
            "Hypothesis 9: Unsupervised Taxonomy Clustering",
            "Hypothesis 10: Traffic Volume via AQI Proxy"
        ],
        index=0
    )
    
    st.sidebar.write("---")
    st.sidebar.success(f"Dataset active: {uploaded_file.name}\n\nRow Count Ingested: {len(df_fetched):,}")

    # =============================================================================
    # MODULE TAB 0: DATASET OVERVIEW & AUDIT MATRIX TABLES
    # =============================================================================
    if selected_tab == "Dataset Overview & Audit Table":
        st.header("Telemetry Stream Overview & Pavement Integrity Audit Matrix")
        st.write("Provides a real-time macroscopic review of columns, data structures, and spatial configurations.")
        
        kpi_col1, kpi_col2, kpi_col3 = st.columns(3)
        with kpi_col1:
            st.metric(label="Total Network Ingested Rows", value=f"{len(df_fetched):,}")
        with kpi_col2:
            unique_corr = df_fetched['corridor_name'].nunique() if 'corridor_name' in df_fetched.columns else 0
            st.metric(label="Active High-Priority Corridors", value=unique_corr)
        with kpi_col3:
            unique_seg = df_fetched['shapefile_segment_name'].nunique() if 'shapefile_segment_name' in df_fetched.columns else 0
            st.metric(label="Monitored Shapefile Links", value=unique_seg)
            
        st.write("### Ingested CSV Table View Slice (First 100 Records)")
        st.dataframe(df_fetched.head(100), use_container_width=True)
        
        st.write("### Metadata Data Column Profiles & Operational Summary Specs")
        buffer_summary = pd.DataFrame({
            'Data Column Type': df_fetched.dtypes.astype(str),
            'Non-Null Observations Counts': df_fetched.count(),
            'Missing Fields Null Density (%)': (df_fetched.isnull().sum() / len(df_fetched)) * 100
        })
        st.table(buffer_summary)

    # =============================================================================
    # MODULE TAB 1: HYPOTHESIS 1 - SYSTEMIC BOTTLENECK LOCALIZATION
    # =============================================================================
    elif selected_tab == "Hypothesis 1: Systemic Bottleneck Localization":
    
        st.header("Hypothesis 1: Systemic Bottleneck Localization (True vs. Spillover Traffic)")
    
        # ==============================================================================
        # 1. EXTENDED BUSINESS FRAMING & GRANULAR ENGINEERING LOGIC
        # ==============================================================================
        st.error(
            "###  The Business Question & Operational Context\n\n"
            "**Which specific micro-segments act as 'root cause' structural bottlenecks that generate cascading "
            "spillover queues across a transit corridor, and where should engineering interventions be prioritized first?**\n\n"
            "In urban traffic networks managed by CUMTA, macroscopic congestion symptoms often appear identical on dashboards: "
            "multiple contiguous road links show a drop in operating speed and a corresponding spike in travel times. However, "
            "the underlying physics driving these delays are fundamentally disparate:\n\n"
            "* **True (Root-Cause) Bottlenecks:** Induced directly by hyper-localized geometric anomalies, lane drops, poorly "
            "optimized intersection signal timings, or permanent physical friction (e.g., bus-loading zones blockades). These "
            "require direct, capital-intensive on-site engineering adjustments (geometry corrections, physical lane separation, signal retiming).\n"
            "* **Victim (Spillover) Segments:** Physically free-flowing infrastructure links that exhibit zero structural defects, "
            "but are experiencing artificial capacity degradation simply because an intense downstream queue has backed up, "
            "physically blocking the upstream link's exit merge. Deploying field crews to alter a victim segment's layout is a "
            "misallocation of municipal resources; the true intervention must be applied exclusively at the downstream catalyst link."
        )
        
        st.success(
            "###  The Engineering Action & Causal Tracking Logic\n\n"
            "To systematically isolate structural friction from ambient commuter volume waves, this analytics engine calculates the "
            "**Travel Time Index (TTI)** at a high sub-1-kilometer resolution. Rather than implementing an arbitrary, flat, city-wide "
            "threshold—which naturally biases metrics against inherently high-volume commercial trunks—the framework calculates "
            "dynamic baseline parameters unique to each corridor's individual distribution.\n\n"
            "By mapping spatial configurations (`sequence_order`) concurrently with discrete asynchronous time steps (`execution_timestamp`), "
            "we construct a localized network direction matrix. A segment is mathematically flagged as a **Causal Root Cause Point** if "
            "it transitions into deep congestion independently of its immediate upstream physical neighbor, yet successfully "
            "propagates that failure forward into subsequent temporal observation intervals. This methodology isolates the exact "
            "genesis point of backward queue propagation waves."
        )
        
        st.info(
            "###  Expected Engineering Artifacts & Operational Outputs\n\n"
            "1. **Macroscopic Corridor Performance Rankings:** Aggregated baseline metrics to assess systemic regional strain.\n"
            "2. **Priority Root-Cause Bottleneck Inventory:** An un-biased, multi-criteria ranked inventory separating true causal agents from victims.\n"
            "3. **MCBI Score Decomposition Analysis:** Granular bar charting revealing the exact mathematical drivers behind each segment's rank.\n"
            "4. **Spatiotemporal Congestion Heatmaps:** High-fidelity visual matrices mapping diurnal wave evolution.\n"
            "5. **Worked Empirical Causal Charts:** Direct proof mapping localized anomaly occurrences where upstream inputs remain clear."
        )
        st.write("---")
    
        # ==============================================================================
        # 2. ADVANCED INGESTION CLEANING & ASYNC POLL AUDIT MATRIX
        # ==============================================================================
        df_analyzed = df_fetched.copy()
        df_analyzed['execution_timestamp'] = pd.to_datetime(
            df_analyzed['execution_timestamp'], format='mixed', dayfirst=True, errors='coerce'
        )
        df_analyzed = df_analyzed.dropna(subset=['execution_timestamp'])
    
        # Track duplicates that physically corrupt the .shift() sequence evaluation
        n_before = len(df_analyzed)
        df_analyzed = df_analyzed.sort_values(
            by=['corridor_name', 'execution_timestamp', 'sequence_order']
        ).reset_index(drop=True)
        
        df_analyzed = df_analyzed.drop_duplicates(
            subset=['segment_uid', 'execution_timestamp'], keep='first'
        )
        n_after = len(df_analyzed)
        n_removed = n_before - n_after
    
        if n_removed > 0:
            st.warning(
                f"###  Data Quality Ingestion Audit\n\n"
                f"**Pre-Processing Flag:** Detected and purged **{n_removed:,}** duplicate (Segment UID + Timestamp) entries "
                f"({n_removed / n_before * 100:.2f}% of the total telemetry pool). These artifacts are caused by asynchronous cloud pooling "
                f"overlapping across narrow collection intervals.\n\n"
                f"**Engineering Consequence:** If left uncleaned, a duplicate record for Segment A at timestamp T would be interpreted "
                f"by the `.shift(1)` lookback operator as a separate, phantom 'upstream segment' at that exact same timestamp. This "
                f"mathematical artifact would permanently corrupt the spillover tracking matrix, manufacturing false causal events on single-segment corridors."
            )
    
        # Standardize column constraints safely across scope
        if 'hour_of_day' not in df_analyzed.columns:
            df_analyzed['hour_of_day'] = df_analyzed['derived_hour']
        if 'segment_uid' not in df_analyzed.columns:
            df_analyzed['segment_uid'] = df_analyzed['shapefile_segment_name']
        if 'is_weekend' not in df_analyzed.columns:
            df_analyzed['is_weekend'] = 0
    
        # ==============================================================================
        # 3. COMPREHENSIVE METHODOLOGY DEEP-DIVE (EXPANDED DETAIL)
        # ==============================================================================
        with st.expander(" Deep-Dive Mathematical Methodology & Weighting Rationale", expanded=False):
            st.markdown(
                """
            ### Step 1: Dynamic Corridor-Relative Thresholding
            To control for varying baseline designs (e.g., standard at-grade links vs. express grade-separated structures), congestion is defined relative to each unique corridor's data distribution:
            $$\\text{Congestion Threshold}_{\\text{Corridor}} = P_{90}\\left(\\text{TTI}_{\\text{Corridor}}\\right)$$
            A segment is flagged as active when:
            $$\\text{is\\_congested} = \\text{TTI}_{\\text{Segment}, t} > \\text{Congestion Threshold}_{\\text{Corridor}}$$
            This isolates structural anomalies from expected background baseline volume.
    
            ### Step 2: Spatiotemporal Spatial Shifting Matrix
            Using bounded data sorting, the immediate upstream link position is identified chronologically for every discrete polling moment using a directional index shift:
            $$\\text{upstream\\_is\\_congested} = \\text{Shift}_{\\text{spatial}}(\\text{is\\_congested}, \\text{offset}=1)$$
            $$\\text{next\\_interval\\_congested} = \\text{Shift}_{\\text{temporal}}(\\text{is\\_congested}, \\text{offset}=-1)$$
    
            ### Step 3: Causal Root-Cause Classification Constraint
            A specific segment interval is classified as a genuine infrastructure breakdown origin point if and only if it satisfies three strict Boolean conditions concurrently:
            $$\\text{root\\_cause\\_event} = (\\text{is\\_congested} == \\text{True}) \\land (\\text{upstream\\_is\\_congested} == \\text{False}) \\land (\\text{next\\_interval\\_congested} == \\text{True})$$
            * **Condition 1:** The link must be in active failure status.
            * **Condition 2:** The upstream link must remain free-flowing (proving the delay did not spill backward from an external source).
            * **Condition 3:** The failure must persist into the next time step (filtering out random transient telemetry anomalies).
    
            ### Step 4: Diurnal Breakdown Onset Tracking
            For each individual calendar date, the framework evaluates the exact initial hour within commuter peak windows (`[7, 8, 9, 10, 17, 18, 19, 20]`) where structural capacity breakdown occurs:
            $$\\text{Daily Breakdown Hour} = \\min \\left( \\text{hour\\_of\\_day} \\mid \\text{is\\_congested} == \\text{True} \\right)$$
            The arithmetic mean across the full 21-day timeline yields the `mean_onset_hour`. A lower average onset score indicates a segment that breaks down ahead of normal commuter volume growth, pointing to structural capacity deficits.
    
            ### Step 5: Composite Multi-Criteria Bottleneck Index (MCBI) Formulation
            Four independent normalized indices are computed using MinMax scaling:
            $$I_x = \\frac{X - X_{\\min}}{X_{\\max} - X_{\\min}}$$
            The global prioritization rank is governed by a weighted linear combination:
            $$\\text{MCBI Score} = (0.25 \\cdot I_{\\text{P90 TTI}}) + (0.20 \\cdot I_{\\text{Congestion Frequency}}) + (0.25 \\cdot (1 - I_{\\text{Mean Onset}})) + (0.30 \\cdot I_{\\text{Root Cause Events}})$$
    
            **Weight Redistribution Protocol for Single-Segment Corridors:**
            If a corridor contains only one monitored link ($N_{\\text{segs}} = 1$), calculating upstream causal relationships is physically impossible. Rather than inputting an arbitrary zero value (which would artificially reward the segment by lowering its risk profile), the missing component's weight ($0.30$) is omitted, and the remaining three parameters are proportionally rescaled to sum to $1.0$:
            $$\\text{Rescaled MCBI} = \\frac{(0.25 \\cdot I_{\\text{P90 TTI}}) + (0.20 \\cdot I_{\\text{Congestion Frequency}}) + (0.25 \\cdot (1 - I_{\\text{Mean Onset}}))}{0.25 + 0.20 + 0.25}$$
            This ensures cross-network alignment on a consistent $[0,1]$ scale, while explicitly labeling single-segment links as untestable for causal behavior under current sensor deployment layout.
            """
            )
    
        # ==============================================================================
        # 4. DATA ENGINE LOGIC & SCALING COMPUTATION
        # ==============================================================================
        corridor_bounds = df_analyzed.groupby('corridor_name')['travel_time_index_tti'].transform(lambda x: x.quantile(0.90))
        df_analyzed['congestion_threshold'] = corridor_bounds
        df_analyzed['is_congested'] = df_analyzed['travel_time_index_tti'] > corridor_bounds
    
        seg_count_per_corridor = df_analyzed.groupby('corridor_name')['segment_uid'].transform('nunique')
        df_analyzed['multi_segment_corridor'] = seg_count_per_corridor > 1
    
        df_analyzed['upstream_is_congested'] = df_analyzed.groupby(
            ['corridor_name', 'execution_timestamp']
        )['is_congested'].shift(1)
    
        df_analyzed['next_interval_congested'] = df_analyzed.groupby(
            ['corridor_name', 'segment_uid']
        )['is_congested'].shift(-1)
    
        df_analyzed['root_cause_event'] = np.where(
            df_analyzed['multi_segment_corridor'],
            (df_analyzed['is_congested'] == True) &
            (df_analyzed['upstream_is_congested'] == False) &
            (df_analyzed['next_interval_congested'] == True),
            np.nan
        )
    
        peak_hours = df_analyzed[df_analyzed['hour_of_day'].isin([7, 8, 9, 10, 17, 18, 19, 20])].copy()
        peak_hours['date'] = peak_hours['execution_timestamp'].dt.date
        congested_peaks = peak_hours[peak_hours['is_congested'] == True]
    
        if len(congested_peaks) > 0:
            earliest_breakdown = congested_peaks.groupby(['date', 'segment_uid'])['hour_of_day'].min().reset_index()
            avg_onset = earliest_breakdown.groupby('segment_uid')['hour_of_day'].mean().reset_index().rename(
                columns={'hour_of_day': 'mean_onset_hour'}
            )
        else:
            avg_onset = pd.DataFrame(columns=['segment_uid', 'mean_onset_hour'])
    
        metrics = df_analyzed.groupby(
            ['segment_uid', 'corridor_name', 'shapefile_segment_name', 'multi_segment_corridor']
        ).agg(
            p90_tti=('travel_time_index_tti', lambda x: x.quantile(0.90)),
            mean_tti=('travel_time_index_tti', 'mean'),
            total_intervals=('is_congested', 'count'),
            total_congested_intervals=('is_congested', 'sum'),
            root_cause_events=('root_cause_event', lambda x: x.sum() if x.notna().any() else np.nan),
        ).reset_index()
    
        metrics = pd.merge(metrics, avg_onset, on='segment_uid', how='left')
        metrics['mean_onset_hour'] = metrics['mean_onset_hour'].fillna(24.0)
        metrics['pct_time_congested'] = (metrics['total_congested_intervals'] / metrics['total_intervals']) * 100
    
        def _minmax(series: pd.Series) -> pd.Series:
            if series.max() == series.min():
                return series * 0.0
            return (series - series.min()) / (series.max() - series.min())
    
        metrics['n_p90'] = _minmax(metrics['p90_tti'])
        metrics['n_pct_congested'] = _minmax(metrics['pct_time_congested'])
        metrics['n_onset'] = 1.0 - _minmax(metrics['mean_onset_hour'])
    
        has_root_cause_data = metrics['root_cause_events'].notna()
        metrics['n_root_cause'] = np.nan
        if has_root_cause_data.any():
            metrics.loc[has_root_cause_data, 'n_root_cause'] = _minmax(
                metrics.loc[has_root_cause_data, 'root_cause_events']
            )
            if metrics.loc[has_root_cause_data, 'root_cause_events'].nunique() == 1:
                metrics.loc[has_root_cause_data, 'n_root_cause'] = 1.0
    
        W_P90, W_PCT, W_ONSET, W_RC = 0.25, 0.20, 0.25, 0.30
        mcbi_scores = []
        for _, row in metrics.iterrows():
            base = row['n_p90'] * W_P90 + row['n_pct_congested'] * W_PCT + row['n_onset'] * W_ONSET
            if pd.notna(row['n_root_cause']):
                score = base + (row['n_root_cause'] * W_RC)
            else:
                score = base / (W_P90 + W_PCT + W_ONSET)
            mcbi_scores.append(score)
        metrics['mcbi_score'] = mcbi_scores
    
        metrics['root_cause_display'] = metrics['root_cause_events'].apply(
            lambda v: "N/A (Untestable)" if pd.isna(v) else f"{int(v)} Events"
        )
    
        top_priority_metrics = metrics.sort_values(by='mcbi_score', ascending=False).reset_index(drop=True)
        top_priority_metrics.insert(0, 'priority_rank', top_priority_metrics.index + 1)
        top_5_segments = top_priority_metrics.head(5)
    
        # ==============================================================================
        # 5. TECHNICAL DATA TABLES & REPORT GENERATION
        # ==============================================================================
        st.write("### [1] Macroscopic Corridor Congestion Analysis Matrix")
        corridor_rankings = df_analyzed.groupby('corridor_name').agg(
            mean_tti=('travel_time_index_tti', 'mean'),
            max_tti=('travel_time_index_tti', 'max'),
            segments_monitored=('segment_uid', 'nunique'),
            congested_intervals=('is_congested', 'sum'),
        ).sort_values(by='mean_tti', ascending=False).reset_index()
        st.dataframe(corridor_rankings.style.format({'mean_tti': '{:.3f}', 'max_tti': '{:.2f}'}), use_container_width=True)
        st.caption(
            "**Table Interpretive Engineering Footnote:** This high-level summary logs baseline corridor stress. Corridors with a "
            "`segments_monitored` index of 1 are strictly bounded single-link domains, meaning downstream spillover cannot "
            "be cross-verified with upstream metrics due to spatial data gaps."
        )
    
        st.write("### [2] Priority Root-Cause Bottleneck Inventory (Ranked via Composite MCBI)")
        display_cols = [
            'priority_rank', 'shapefile_segment_name', 'corridor_name', 'p90_tti',
            'pct_time_congested', 'mean_onset_hour', 'root_cause_display', 'mcbi_score'
        ]
        st.dataframe(
            top_5_segments[display_cols].rename(columns={
                'priority_rank': 'Rank', 'shapefile_segment_name': 'Segment ID Link Name',
                'corridor_name': 'Corridor Domain', 'p90_tti': 'P90 Peak TTI',
                'pct_time_congested': 'Congestion Density (%)', 'mean_onset_hour': 'Avg Onset Time',
                'root_cause_display': 'Causal Diagnostics', 'mcbi_score': 'Composite MCBI Score'
            }).style.format({'P90 Peak TTI': '{:.2f}', 'Congestion Density (%)': '{:.2f}%', 'Avg Onset Time': '{:.1f}:00', 'Composite MCBI Score': '{:.4f}'}),
            use_container_width=True
        )
        st.caption(
            "**Table Interpretive Engineering Footnote:** The `Composite MCBI Score` uniquely weights absolute operational "
            "severity alongside causal evidence. Links displaying 'N/A (Untestable)' highlight high-stress segments where "
            "expanding the local sensor footprint is required to confirm whether the delay is self-generated or absorbed from downstream."
        )
    
        # ==============================================================================
        # 6. CHART 1: MCBI PRIORITY DECOMPOSITION (STACKED CONTRIBUTION)
        # ==============================================================================
        st.write("### [3] MCBI Score Decomposition Matrix")
        decomp = top_priority_metrics.copy()
        decomp['contrib_p90'] = decomp['n_p90'] * W_P90
        decomp['contrib_pct'] = decomp['n_pct_congested'] * W_PCT
        decomp['contrib_onset'] = decomp['n_onset'] * W_ONSET
        decomp['contrib_rc'] = decomp['n_root_cause'].fillna(0) * W_RC
        
        no_rc_mask = decomp['n_root_cause'].isna()
        rescale = 1.0 / (W_P90 + W_PCT + W_ONSET)
        decomp.loc[no_rc_mask, ['contrib_p90', 'contrib_pct', 'contrib_onset']] *= rescale
    
        fig1, ax1 = plt.subplots(figsize=(12, 5.0))
        labels = decomp['shapefile_segment_name']
        bottom = np.zeros(len(decomp))
        components = [
            ('contrib_p90', 'Tail Severity Factor (P90 TTI)', '#e67e22'),
            ('contrib_pct', 'Temporal Congestion Density (%)', '#f1c40f'),
            ('contrib_onset', 'Early Diurnal Failure Onset', '#2980b9'),
            ('contrib_rc', 'Verified Upstream Causal Event', '#c0392b'),
        ]
        for col, label, color in components:
            ax1.bar(labels, decomp[col], bottom=bottom, label=label, color=color, edgecolor='white', linewidth=0.5)
            bottom += decomp[col].values
            
        ax1.set_ylabel("Stacked Priority Score Weights (MCBI Scale)", fontweight='bold', fontsize=9)
        ax1.set_xlabel("Monitored Link Code Reference ID", fontweight='bold', fontsize=9)
        ax1.set_title("H1 Diagnostic Component Attribution Vector per Asset", fontsize=11, fontweight='bold', pad=12)
        ax1.set_ylim(0, 1.05)
        ax1.grid(axis='y', linestyle=':', alpha=0.4)
        ax1.legend(loc='upper right', fontsize=8.5, frameon=True, facecolor='white', edgecolor='none')
        plt.xticks(rotation=15, ha='right', fontsize=8)
        plt.yticks(fontsize=8)
        st.pyplot(fig1)
        st.caption(
            "**Visual Chart Interpretive Footnote:** This chart unpacks the internal variables driving each link's macro-priority rating. "
            "A segment dominated by the dark-red block indicates verified infrastructure breakdown originating independently of "
            "upstream inputs. Conversely, segments dominated by orange, yellow, and blue are experiencing high operational stress "
            "but are currently unconfirmed as root causes due to spatial data limitations."
        )
    
        # ==============================================================================
        # 7. CHART 2: CONSOLIDATED SPATIOTEMPORAL DASHBOARD GRID
        # ==============================================================================
        st.write("### [4] Integrated System-Wide Spatiotemporal Performance Grid")
        num_corridors = len(df_analyzed['corridor_name'].unique())
        mean_failure_line = corridor_bounds.mean()
        total_grid_rows = max(num_corridors, 5)
        
        fig2 = plt.figure(figsize=(22, 4.2 * total_grid_rows))
        gs = fig2.add_gridspec(total_grid_rows, 2, width_ratios=[1.2, 1.0], hspace=0.55, wspace=0.25)
    
        unique_corridors = df_analyzed['corridor_name'].unique()
        for i, corr_name in enumerate(unique_corridors):
            ax_heat = fig2.add_subplot(gs[i, 0])
            corridor_subset = df_analyzed[df_analyzed['corridor_name'] == corr_name]
            heatmap_data = corridor_subset.groupby(
                ['shapefile_segment_name', 'hour_of_day']
            )['travel_time_index_tti'].mean().unstack(level=1)
            
            sns.heatmap(
                heatmap_data, cmap='YlOrRd', ax=ax_heat, cbar_kws={'label': 'Mean TTI Scale'},
                linewidths=0.2, linecolor='#f8fafc'
            )
            ax_heat.set_xlabel('Diurnal Clock Interval (24hr Loop)', fontweight='bold', fontsize=8)
            ax_heat.set_ylabel('Asset Segment Alignment Identifier', fontsize=8, fontweight='bold')
            n_segs = corridor_subset['segment_uid'].nunique()
            inst_tag = "Multi-Segment: Causal Track Enabled" if n_segs > 1 else "Single-Segment Data Boundary"
            ax_heat.set_title(f'Spatiotemporal Profile: Matrix [{corr_name}] ({inst_tag})', fontsize=10, fontweight='bold', pad=8)
            ax_heat.tick_params(axis='both', labelsize=8)
    
        for rank, (_, row) in enumerate(top_5_segments.iterrows()):
            ax_trend = fig2.add_subplot(gs[rank, 1])
            curr_uid = row['segment_uid']
            seg_name = row['shapefile_segment_name']
            c_name = row['corridor_name']
            seg_data = df_analyzed[df_analyzed['segment_uid'] == curr_uid]
    
            weekday_profile = seg_data[seg_data['is_weekend'] == 0].groupby('hour_of_day')['travel_time_index_tti'].mean()
            weekend_profile = seg_data[seg_data['is_weekend'] == 1].groupby('hour_of_day')['travel_time_index_tti'].mean()
    
            ax_trend.plot(weekday_profile.index, weekday_profile.values, color='#1f77b4', marker='o', markersize=4, linewidth=1.8, label='Weekday Profiling')
            if not weekend_profile.empty:
                ax_trend.plot(weekend_profile.index, weekend_profile.values, color='#ff7f0e', marker='s', markersize=4, linestyle='--', linewidth=1.5, label='Weekend Elasticity')
    
            ax_trend.axhline(y=mean_failure_line, color='crimson', linestyle=':', linewidth=1.5,
                             label=f'Global Critical Alert Cap ({mean_failure_line:.2f})')
            ax_trend.set_title(f"Intervention Rank #{rank + 1}: {seg_name} ({c_name})", fontsize=9.5, fontweight='bold', pad=8)
            ax_trend.set_xlabel("Hour Range Matrix", fontsize=8)
            ax_trend.set_ylabel("Calculated TTI Value", fontsize=8)
            ax_trend.set_xlim(0, 23)
            ax_trend.set_xticks(range(0, 24, 2))
            ax_trend.grid(True, linestyle=':', alpha=0.5)
            ax_trend.legend(loc='upper left', fontsize=8, frameon=True, facecolor='white')
            ax_trend.tick_params(axis='both', labelsize=8)
    
        plt.tight_layout()
        st.pyplot(fig2)
        st.caption(
            "**Visual Dashboard Interpretive Engineering Footnotes:**\n\n"
            "**Left Column Matrix:** Visualizes the evolution of structural bottleneck queues. Darker areas pinpoint severe, "
            "recurrent bottlenecks. Comparing rows vertically within a panel reveals whether adjacent segments collapse simultaneously "
            "(shared peak demand volume) or sequentially with a distinct time lag (confirming downstream queue propagation).\n\n"
            "**Right Column Profiles:** Profiles operational breakdown duration. Continuous traces remaining above the "
            "red horizontal capacity alert line indicate localized structural layout constraints, rather than normal, transient peak commuter volume."
        )
    
        # ==============================================================================
        # 8. CHART 3: EMPIRICAL DIAGNOSED CASE-STUDY GRAPH
        # ==============================================================================
        multi_corridors = metrics.loc[metrics['multi_segment_corridor'], 'corridor_name'].unique()
        if len(multi_corridors) > 0:
            st.write("### [5] Empirical Verification Case Study (Multi-Segment Domain)")
            for corr in multi_corridors:
                case_df = df_analyzed[df_analyzed['corridor_name'] == corr]
                fig3, ax3 = plt.subplots(figsize=(12, 5.0))
                
                for seg_uid, seg_sub in case_df.groupby('segment_uid'):
                    seg_label = seg_sub['shapefile_segment_name'].iloc[0]
                    hourly = seg_sub.groupby('hour_of_day')['travel_time_index_tti'].mean()
                    ax3.plot(hourly.index, hourly.values, marker='o', markersize=4, linewidth=1.5, alpha=0.7, label=f"Link Line Profile: {seg_label}")
    
                    rc_events = seg_sub[seg_sub['root_cause_event'] == True]
                    if len(rc_events) > 0:
                        rc_hourly = rc_events.groupby('hour_of_day')['travel_time_index_tti'].mean()
                        ax3.scatter(
                            rc_hourly.index, rc_hourly.values,
                            color='#2c3e50', zorder=6, s=120, marker='X', edgecolors='white', linewidths=1.0,
                            label=f"Verified Breakdown Origin Moment ({seg_label})"
                        )
                        
                ax3.set_title(f"H1 Empirical Causal Validation Profiling Map: Corridor Context Domain [{corr}]", fontsize=11, fontweight='bold', pad=12)
                ax3.set_xlabel("Diurnal Metric Hour Segment (Temporal Sweep)", fontweight='bold', fontsize=9)
                ax3.set_ylabel("Observed Mean Travel Time Index (TTI)", fontweight='bold', fontsize=9)
                ax3.set_xlim(0, 23)
                ax3.set_xticks(range(0, 24, 2))
                ax3.grid(True, linestyle=':', alpha=0.4)
                ax3.legend(loc='upper right', fontsize=8.5, frameon=True, facecolor='white')
                plt.xticks(fontsize=8)
                plt.yticks(fontsize=8)
                st.pyplot(fig3)
                
                n_rc_total = int(case_df['root_cause_event'].sum(skipna=True))
                st.caption(
                    f"**Verification Interpretive Engineering Footnote:** The dark 'X' targets represent historical
