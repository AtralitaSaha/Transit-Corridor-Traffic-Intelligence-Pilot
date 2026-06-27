# ============================================================
# utils/data_loader.py
# CUMTA Traffic Intelligence — Data Loading & Validation
#
# Supports three ingestion modes:
#   1. Demo (synthetic)  — runs immediately, no setup needed
#   2. CSV Upload        — any exported flat-file from the DB
#   3. PostgreSQL        — live connection via SQLAlchemy
# ============================================================

import io
import pandas as pd
import numpy as np
import streamlit as st


# ── Column registry ───────────────────────────────────────────────────────────
CORE_COLS = [
    "shapefile_segment_name",
    "travel_time_index_tti",
    "current_travel_time_seconds",
    "free_flow_travel_time_seconds",
    "hour_of_day",
    "is_weekend",
]
MODULE_COLS = {
    "H1": CORE_COLS,
    "H2": CORE_COLS,
    "H4": CORE_COLS + ["precipitation_intensity_mm_h", "visibility_meters"],
    "H7": CORE_COLS + ["segment_slope_grade", "network_layer_type"],
    "H8": CORE_COLS + ["true_driving_distance_meters"],
}

TYPE_MAP = {
    "hour_of_day"                   : "int",
    "is_weekend"                    : "int",
    "travel_time_index_tti"         : "float",
    "current_travel_time_seconds"   : "float",
    "free_flow_travel_time_seconds" : "float",
    "true_driving_distance_meters"  : "float",
    "precipitation_intensity_mm_h"  : "float",
    "visibility_meters"             : "float",
    "segment_slope_grade"           : "float",
    "topographic_elevation_meters"  : "float",
}


# ── Type casting ──────────────────────────────────────────────────────────────
def _cast(df: pd.DataFrame) -> pd.DataFrame:
    """Coerce columns to the correct numeric types without raising errors."""
    for col, dtype in TYPE_MAP.items():
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


# ── Validation ────────────────────────────────────────────────────────────────
def validate(df: pd.DataFrame) -> dict:
    """
    Return which analysis modules can run on this DataFrame.

    Returns
    -------
    dict with keys:
        core_ok          : bool — minimum columns present
        missing_core     : list of missing core columns
        available_modules: list of module codes that can run (e.g. ['H1','H2'])
    """
    missing_core = [c for c in CORE_COLS if c not in df.columns]
    available    = []
    for mod, cols in MODULE_COLS.items():
        if all(c in df.columns for c in cols):
            available.append(mod)
    return {
        "core_ok"          : len(missing_core) == 0,
        "missing_core"     : missing_core,
        "available_modules": available,
    }


# ── CSV loader ────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def load_csv(file_bytes: bytes) -> pd.DataFrame | None:
    """Read a CSV uploaded through the Streamlit file-uploader widget."""
    try:
        df = pd.read_csv(io.BytesIO(file_bytes))
        return _cast(df)
    except Exception as exc:
        st.error(f"CSV read failed: {exc}")
        return None


# ── PostgreSQL loader ─────────────────────────────────────────────────────────
@st.cache_data(ttl=120, show_spinner=False)
def load_postgres(
    host: str, port: int, dbname: str,
    user: str, password: str, query: str
) -> pd.DataFrame | None:
    """
    Connect to a PostgreSQL instance and run a SQL query.
    Requires sqlalchemy + psycopg2-binary to be installed.

    The connection string is built from the parameters so Streamlit
    can hash and cache the result properly.
    """
    try:
        from sqlalchemy import create_engine, text  # lazy import
        conn_str = (
            f"postgresql+psycopg2://{user}:{password}"
            f"@{host}:{port}/{dbname}?sslmode=disable"
        )
        engine = create_engine(conn_str, pool_pre_ping=True)
        with engine.connect() as conn:
            df = pd.read_sql(text(query), conn)
        return _cast(df)
    except ImportError:
        st.error("psycopg2-binary or sqlalchemy not installed. Run: pip install sqlalchemy psycopg2-binary")
        return None
    except Exception as exc:
        st.error(f"PostgreSQL connection failed: {exc}")
        return None


# ── Synthetic data generator ──────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def generate_demo(n_rows: int = 7000, n_segs: int = 40, seed: int = 42) -> pd.DataFrame:
    """
    Generate a synthetic traffic dataset that mirrors CUMTA's real schema.

    Segment names are modelled after the actual corridors seen in the
    pilot output (OMR_Corridor, GST_Corridor, Mount_Road_Corridor).
    TTI values follow realistic peak/off-peak patterns.
    """
    rng = np.random.default_rng(seed)

    # ── Segment master ──
    corridors = ["OMR_Corridor", "GST_Corridor", "Mount_Road_Corridor",
                 "Anna_Salai_Seg", "ECR_Corridor", "Poonamallee_Seg"]
    seg_names, seg_types, seg_fft, seg_dist, seg_slope, seg_elev = [], [], [], [], [], []

    for i in range(n_segs):
        corr = corridors[i % len(corridors)]
        seg_names.append(f"{corr}_{i+1:02d}")
        seg_types.append(rng.choice(["At-Grade", "Express"], p=[0.80, 0.20]))
        seg_fft.append(float(rng.uniform(30, 180)))
        seg_dist.append(float(rng.uniform(300, 1500)))
        seg_slope.append(float(rng.uniform(-0.07, 0.07)))
        seg_elev.append(float(rng.uniform(10, 120)))

    # ── Row-level data ──
    seg_idx  = rng.integers(0, n_segs, n_rows)
    hour     = rng.integers(0, 24, n_rows)
    weekend  = rng.binomial(1, 0.286, n_rows)   # 2 out of 7 days

    # Base TTI — realistic peak shapes
    tti = np.ones(n_rows, dtype=float)
    # Morning peak 08–10 (weekday)
    mp = (hour >= 8)  & (hour <= 10) & (weekend == 0)
    tti[mp] += rng.uniform(0.5, 2.5, mp.sum())
    # Evening peak 17–20 (weekday)
    ep = (hour >= 17) & (hour <= 20) & (weekend == 0)
    tti[ep] += rng.uniform(0.8, 3.2, ep.sum())
    # Midday weekend 12–16
    wp = (hour >= 12) & (hour <= 16) & (weekend == 1)
    tti[wp] += rng.uniform(0.3, 1.2, wp.sum())
    # Express segments slightly more congested (flyover exit effect)
    exp_mask = np.array([seg_types[i] == "Express" for i in seg_idx])
    tti[exp_mask] *= rng.uniform(1.0, 1.4, exp_mask.sum())
    # Random noise
    tti += rng.exponential(0.15, n_rows)
    tti = np.clip(tti, 1.0, 8.0)

    # Precipitation (15% chance per observation)
    precip = np.zeros(n_rows)
    rain   = rng.binomial(1, 0.15, n_rows).astype(bool)
    precip[rain] = rng.exponential(3.5, rain.sum())
    tti[rain] *= rng.uniform(1.03, 1.30, rain.sum())
    tti = np.clip(tti, 1.0, 8.0)

    # Visibility drops during rain
    vis = rng.uniform(3000, 10000, n_rows)
    vis[rain] = rng.uniform(200, 3000, rain.sum())

    df = pd.DataFrame({
        "shapefile_segment_name"       : [seg_names[i] for i in seg_idx],
        "direction_track"              : rng.choice(["Eastbound","Westbound","Northbound","Southbound"], n_rows),
        "network_layer_type"           : [seg_types[i] for i in seg_idx],
        "true_driving_distance_meters" : [seg_dist[i] for i in seg_idx],
        "free_flow_travel_time_seconds": [seg_fft[i] for i in seg_idx],
        "current_travel_time_seconds"  : [seg_fft[i] for i in seg_idx] * tti,
        "travel_time_index_tti"        : tti,
        "hour_of_day"                  : hour,
        "is_weekend"                   : weekend,
        "road_width_lanes"             : rng.choice([2, 3, 4, 6], n_rows),
        "segment_slope_grade"          : [seg_slope[i] for i in seg_idx],
        "topographic_elevation_meters" : [seg_elev[i] for i in seg_idx],
        "precipitation_intensity_mm_h" : precip,
        "visibility_meters"            : vis,
    })

    return _cast(df)
