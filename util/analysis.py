# ============================================================
# utils/analysis.py
# CUMTA Traffic Intelligence — Core Analysis Engine
#
# scipy has been removed intentionally — Streamlit Cloud's
# Python 3.14 environment has no pre-built scipy wheel.
# All statistics are implemented with pure numpy so the
# app deploys on any Python version without C compilation.
# ============================================================

import pandas as pd
import numpy as np
import math


# ── Internal numpy-only stat helpers ─────────────────────────────────────────

def _norm_cdf(x: float) -> float:
    """Standard normal CDF using math.erfc (no scipy needed)."""
    return 0.5 * math.erfc(-x / math.sqrt(2))


def _pearsonr(x, y):
    """
    Pearson correlation coefficient + two-tailed p-value.
    Replaces scipy.stats.pearsonr.
    p-value uses normal approximation — valid for n > 30.
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    n = len(x)
    if n < 3:
        return 0.0, 1.0
    r = float(np.corrcoef(x, y)[0, 1])
    if abs(r) >= 1.0:
        return r, 0.0
    t = r * math.sqrt(n - 2) / math.sqrt(max(1 - r ** 2, 1e-12))
    p = 2 * (1 - _norm_cdf(abs(t)))
    return r, p


def _linregress(x, y):
    """
    OLS linear regression returning (slope, intercept, r, p, stderr).
    Replaces scipy.stats.linregress.
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    n = len(x)
    if n < 3:
        return 0.0, float(np.mean(y)), 0.0, 1.0, 0.0

    coeffs       = np.polyfit(x, y, 1)
    slope        = float(coeffs[0])
    intercept    = float(coeffs[1])
    y_pred       = np.polyval(coeffs, x)
    ss_res       = float(np.sum((y - y_pred) ** 2))
    ss_tot       = float(np.sum((y - np.mean(y)) ** 2))
    r2           = 1.0 - ss_res / max(ss_tot, 1e-12)
    r_val        = math.copysign(math.sqrt(max(r2, 0.0)), slope)
    x_demeaned   = x - np.mean(x)
    stderr       = math.sqrt(ss_res / max(n - 2, 1)) / math.sqrt(
                       max(float(np.sum(x_demeaned ** 2)), 1e-12))
    t            = slope / max(stderr, 1e-12)
    p            = 2 * (1 - _norm_cdf(abs(t)))
    return slope, intercept, r_val, p, stderr


def _welch_ttest(a, b):
    """
    Welch's independent-samples t-test returning (t, p).
    Replaces scipy.stats.ttest_ind(equal_var=False).
    """
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    na, nb = len(a), len(b)
    if na < 2 or nb < 2:
        return 0.0, 1.0
    va   = float(np.var(a, ddof=1))
    vb   = float(np.var(b, ddof=1))
    se   = math.sqrt(va / na + vb / nb + 1e-12)
    t    = (float(np.mean(a)) - float(np.mean(b))) / se
    p    = 2 * (1 - _norm_cdf(abs(t)))
    return t, p


# ── HYPOTHESIS 1 ─────────────────────────────────────────────────────────────
def run_h1(df: pd.DataFrame, root_thresh: float = 2.0,
           spillover_thresh: float = 1.5) -> dict:
    """
    Systemic Bottleneck Localization (True vs. Spillover Traffic)

    Groups all observations by segment and computes TTI statistics.
    Classifies each segment into Root Cause / Spillover / Free Flow.
    """
    seg = (
        df.groupby("shapefile_segment_name")
        .agg(
            mean_tti             = ("travel_time_index_tti", "mean"),
            max_tti              = ("travel_time_index_tti", "max"),
            p90_tti              = ("travel_time_index_tti",
                                    lambda x: x.quantile(0.90)),
            std_tti              = ("travel_time_index_tti", "std"),
            mean_current_time_s  = ("current_travel_time_seconds", "mean"),
            mean_free_flow_s     = ("free_flow_travel_time_seconds", "mean"),
            observation_count    = ("travel_time_index_tti", "count"),
        )
        .reset_index()
    )

    seg["mean_absolute_delay_s"] = (
        seg["mean_current_time_s"] - seg["mean_free_flow_s"]
    )

    def classify(tti):
        if tti >= root_thresh:
            return "Root Cause Bottleneck"
        elif tti >= spillover_thresh:
            return "Spillover Victim"
        return "Free Flow"

    seg["congestion_class"] = seg["mean_tti"].apply(classify)
    seg = seg.sort_values("mean_tti", ascending=False).reset_index(drop=True)
    seg["priority_rank"] = seg.index + 1

    return {
        "segment_tti"     : seg,
        "class_counts"    : seg["congestion_class"].value_counts().to_dict(),
        "top_bottlenecks" : seg[seg["congestion_class"] == "Root Cause Bottleneck"],
        "root_thresh"     : root_thresh,
        "spillover_thresh": spillover_thresh,
    }


# ── HYPOTHESIS 2 ─────────────────────────────────────────────────────────────
def run_h2(df: pd.DataFrame, failure_thresh: float = 2.0,
           clear_baseline: float = 1.2) -> dict:
    """
    Temporal Peak Profiling & Network Failure Rates

    Aggregates TTI by hour × day_type, computes a per-hour network
    failure rate, and detects peak and clearance windows.
    """
    hourly = (
        df.groupby(["hour_of_day", "is_weekend"])
        .agg(
            mean_tti          = ("travel_time_index_tti", "mean"),
            max_tti           = ("travel_time_index_tti", "max"),
            std_tti           = ("travel_time_index_tti", "std"),
            median_tti        = ("travel_time_index_tti", "median"),
            observation_count = ("travel_time_index_tti", "count"),
        )
        .reset_index()
    )
    hourly["day_type"] = hourly["is_weekend"].map({0: "Weekday", 1: "Weekend"})

    fail_rate = (
        df.assign(is_failed=(df["travel_time_index_tti"] >= failure_thresh))
        .groupby(["hour_of_day", "is_weekend"])
        .agg(failure_rate_pct=("is_failed", lambda x: x.mean() * 100))
        .reset_index()
    )
    hourly = hourly.merge(fail_rate, on=["hour_of_day", "is_weekend"])

    def peak_stats(sub: pd.DataFrame, label: str) -> dict:
        sub = sub.sort_values("hour_of_day")
        if sub.empty:
            return {}
        peak_row  = sub.loc[sub["mean_tti"].idxmax()]
        peak_hour = int(peak_row["hour_of_day"])
        peak_tti  = round(float(peak_row["mean_tti"]), 3)
        post_peak = sub[sub["hour_of_day"] > peak_hour]
        clr_rows  = post_peak[post_peak["mean_tti"] < clear_baseline]
        clear_hr  = int(clr_rows["hour_of_day"].iloc[0]) if not clr_rows.empty else -1
        congested = int((sub["mean_tti"] >= 1.5).sum())
        return {
            "label"          : label,
            "peak_hour"      : peak_hour,
            "peak_tti"       : peak_tti,
            "clear_hour"     : clear_hr,
            "congested_hours": congested,
        }

    heatmap = None
    try:
        heatmap = (
            df.groupby(["shapefile_segment_name", "hour_of_day"])
            ["travel_time_index_tti"].mean()
            .unstack("hour_of_day")
        )
    except Exception:
        pass

    return {
        "hourly_profile": hourly,
        "weekday_stats" : peak_stats(hourly[hourly["is_weekend"] == 0], "Weekday"),
        "weekend_stats" : peak_stats(hourly[hourly["is_weekend"] == 1], "Weekend"),
        "heatmap_data"  : heatmap,
        "failure_thresh": failure_thresh,
    }


# ── HYPOTHESIS 4 ─────────────────────────────────────────────────────────────
def run_h4(df: pd.DataFrame, anomaly_mult: float = 1.4,
           rain_thresh: float = 2.5) -> dict:
    """
    Weather-Driven Environmental Variance

    Bins precipitation into WMO tiers, computes TTI uplift vs dry
    baseline, OLS rain-sensitivity slope, and visibility correlation.
    Uses pure numpy — no scipy required.
    """
    df = df.copy()
    bins   = [-np.inf, 0.5, 2.5, 7.6, np.inf]
    labels = ["Dry", "Light Rain", "Moderate Rain", "Heavy Rain"]
    df["weather_condition"] = pd.cut(
        df["precipitation_intensity_mm_h"], bins=bins, labels=labels
    )

    wi = (
        df.groupby("weather_condition", observed=True)
        .agg(
            mean_tti     = ("travel_time_index_tti", "mean"),
            median_tti   = ("travel_time_index_tti", "median"),
            std_tti      = ("travel_time_index_tti", "std"),
            max_tti      = ("travel_time_index_tti", "max"),
            sample_count = ("travel_time_index_tti", "count"),
        )
        .reindex(labels)
        .reset_index()
    )

    dry_vals = wi[wi["weather_condition"] == "Dry"]["mean_tti"].values
    dry_base = float(dry_vals[0]) if (len(dry_vals) > 0
                                       and not np.isnan(dry_vals[0])) else 1.0
    wi["tti_uplift_abs"] = wi["mean_tti"] - dry_base
    wi["tti_uplift_pct"] = (wi["tti_uplift_abs"] / dry_base) * 100

    # OLS rain-sensitivity slope (numpy only)
    rain_df = df[df["precipitation_intensity_mm_h"] > 0].dropna(
        subset=["precipitation_intensity_mm_h", "travel_time_index_tti"]
    )
    if len(rain_df) >= 10:
        slope_r, intercept_r, r_r, p_r, _ = _linregress(
            rain_df["precipitation_intensity_mm_h"].values,
            rain_df["travel_time_index_tti"].values,
        )
    else:
        slope_r, intercept_r, r_r, p_r = 0.0, dry_base, 0.0, 1.0

    # Visibility correlation (numpy only)
    vis_clean = df.dropna(subset=["visibility_meters", "travel_time_index_tti"])
    if len(vis_clean) >= 10:
        vis_r, vis_p = _pearsonr(
            vis_clean["visibility_meters"].values,
            vis_clean["travel_time_index_tti"].values,
        )
    else:
        vis_r, vis_p = 0.0, 1.0

    # Weather anomaly events per segment
    df["is_anomaly"] = (
        (df["travel_time_index_tti"] >= dry_base * anomaly_mult)
        & (df["precipitation_intensity_mm_h"] >= rain_thresh)
    )
    anomaly_by_seg = (
        df.groupby("shapefile_segment_name")["is_anomaly"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
        .rename(columns={"is_anomaly": "anomaly_event_count"})
    )

    return {
        "weather_impact": wi,
        "dry_base"      : dry_base,
        "slope_r"       : slope_r,
        "intercept_r"   : intercept_r,
        "r_r"           : r_r,
        "p_r"           : p_r,
        "vis_r"         : vis_r,
        "vis_p"         : vis_p,
        "anomaly_by_seg": anomaly_by_seg,
        "df_tagged"     : df,
    }


# ── HYPOTHESIS 7 ─────────────────────────────────────────────────────────────
def run_h7(df: pd.DataFrame) -> dict:
    """
    Flyover Exit & Uphill Gradient Penalties

    Bins segment_slope_grade into 5 directional categories, compares
    TTI across Express vs At-Grade infrastructure, runs a Welch t-test,
    and identifies exit-queue candidate segments.
    Uses pure numpy — no scipy required.
    """
    df = df.copy()
    slope_bins   = [-np.inf, -0.04, -0.02, 0.02, 0.04, np.inf]
    slope_labels = ["Steep Downhill", "Mild Downhill",
                    "Flat", "Mild Uphill", "Steep Uphill"]
    df["slope_category"] = pd.cut(
        df["segment_slope_grade"], bins=slope_bins, labels=slope_labels
    )

    layer_tti = (
        df.groupby("network_layer_type")
        .agg(
            mean_tti = ("travel_time_index_tti", "mean"),
            max_tti  = ("travel_time_index_tti", "max"),
            std_tti  = ("travel_time_index_tti", "std"),
            count    = ("travel_time_index_tti", "count"),
        )
        .reset_index()
    )

    slope_tti = (
        df.groupby("slope_category", observed=True)
        .agg(
            mean_tti = ("travel_time_index_tti", "mean"),
            max_tti  = ("travel_time_index_tti", "max"),
            std_tti  = ("travel_time_index_tti", "std"),
            count    = ("travel_time_index_tti", "count"),
        )
        .reset_index()
    )

    # Welch's t-test (numpy only)
    exp_vals = df[df["network_layer_type"] == "Express"][
        "travel_time_index_tti"].dropna().values
    agr_vals = df[df["network_layer_type"] == "At-Grade"][
        "travel_time_index_tti"].dropna().values
    t_stat, t_pval = (_welch_ttest(exp_vals, agr_vals)
                      if len(exp_vals) >= 5 and len(agr_vals) >= 5
                      else (0.0, 1.0))

    agr_seg = (
        df[df["network_layer_type"] == "At-Grade"]
        .groupby("shapefile_segment_name")["travel_time_index_tti"]
        .mean()
        .sort_values(ascending=False)
        .reset_index()
        .rename(columns={"travel_time_index_tti": "mean_tti"})
    )
    exit_thresh = float(agr_seg["mean_tti"].quantile(0.80)) if len(agr_seg) > 0 else 2.0
    exit_cands  = agr_seg[agr_seg["mean_tti"] >= exit_thresh]

    pivot = None
    try:
        pivot = (
            df.groupby(["network_layer_type", "slope_category"], observed=True)
            ["travel_time_index_tti"].mean()
            .unstack("slope_category")
        )
    except Exception:
        pass

    return {
        "layer_tti" : layer_tti,
        "slope_tti" : slope_tti,
        "t_stat"    : t_stat,
        "t_pval"    : t_pval,
        "exit_cands": exit_cands,
        "exit_thresh": exit_thresh,
        "pivot"     : pivot,
        "df_tagged" : df,
    }


# ── HYPOTHESIS 8 ─────────────────────────────────────────────────────────────
def run_h8(df: pd.DataFrame, n_quartiles: int = 4) -> dict:
    """
    Spatial Slicing Accuracy & "Length Dilution"

    Computes per-segment max peak TTI and the dilution gap.
    Tests whether longer segments hide severe micro-congestion.
    Uses pure numpy — no scipy required.
    """
    seg = (
        df.groupby("shapefile_segment_name")
        .agg(
            true_driving_distance_meters = ("true_driving_distance_meters", "first"),
            mean_tti                     = ("travel_time_index_tti", "mean"),
            max_peak_tti                 = ("travel_time_index_tti", "max"),
            p90_tti                      = ("travel_time_index_tti",
                                            lambda x: x.quantile(0.90)),
            std_tti                      = ("travel_time_index_tti", "std"),
            observation_count            = ("travel_time_index_tti", "count"),
        )
        .reset_index()
    )

    seg["dilution_gap"]     = seg["max_peak_tti"] - seg["mean_tti"]
    seg["dilution_gap_pct"] = (seg["dilution_gap"] / seg["mean_tti"]) * 100

    # Pearson r + OLS slope (numpy only)
    clean = seg.dropna(subset=["true_driving_distance_meters", "max_peak_tti"])
    if len(clean) >= 5:
        corr_r, corr_p = _pearsonr(
            clean["true_driving_distance_meters"].values,
            clean["max_peak_tti"].values,
        )
        sl, ic, r_v, p_v, _ = _linregress(
            clean["true_driving_distance_meters"].values,
            clean["max_peak_tti"].values,
        )
    else:
        corr_r, corr_p = 0.0, 1.0
        sl, ic, r_v, p_v = 0.0, 0.0, 0.0, 1.0

    quartile_stats = pd.DataFrame()
    try:
        q_labels = [f"Q{i + 1}" for i in range(n_quartiles)]
        seg["length_quartile"] = pd.qcut(
            seg["true_driving_distance_meters"],
            q=n_quartiles, labels=q_labels, duplicates="drop",
        )
        quartile_stats = (
            seg.groupby("length_quartile", observed=True)
            .agg(
                avg_length_m          = ("true_driving_distance_meters", "mean"),
                mean_of_max_peak_tti  = ("max_peak_tti", "mean"),
                mean_dilution_gap     = ("dilution_gap", "mean"),
                mean_dilution_gap_pct = ("dilution_gap_pct", "mean"),
                segment_count         = ("max_peak_tti", "count"),
            )
            .reset_index()
        )
    except Exception:
        pass

    return {
        "segment_spatial": seg.sort_values("dilution_gap", ascending=False),
        "corr_r"         : corr_r,
        "corr_p"         : corr_p,
        "slope"          : sl,
        "intercept"      : ic,
        "r_val"          : r_v,
        "p_val"          : p_v,
        "quartile_stats" : quartile_stats,
    }
