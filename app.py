import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sqlalchemy import create_engine
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
    .reportview-container { background: #f5f7f9; }
    .main .block-container { padding-top: 2rem; }
    h1, h2, h3 { font-weight: 700 !important; color: #1e293b; }
    div.stButton > button:first-child {
        background-color: #1f77b4; color: white; border-radius: 6px; font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# =============================================================================
# 2. HIGH-PERFORMANCE DATABASE POOLING PIPELINE
# =============================================================================
@st.cache_resource
def get_database_engine():
    """
    Establishes a reusable, cached connection pool to the PostgreSQL backend database asset.
    """
    DB_USER = "postgres"          
    DB_PASSWORD = "-"  
    DB_HOST = "localhost"
    DB_PORT = "5432"
    DB_NAME = "cumta_traffic_synthetic"
    
    connection_string = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    return create_engine(connection_string)

@st.cache_data(ttl=600)  # Cache query arrays for 10 minutes to protect DB throughput limits
def fetch_telemetry_matrix(query):
    """
    Executes raw extraction string query statements and passes outputs straight into DataFrame.
    """
    engine = get_database_engine()
    with engine.connect() as conn:
        df = pd.read_sql(query, con=conn)
    return df

# =============================================================================
# 3. EXECUTIVE MASTER INTERFACE CONTROLLER
# =============================================================================
def main():
    st.title("CUMTA Core Transit Network Diagnostics Cockpit")
    st.markdown("### Integrated 3D Spatial-Temporal Network Performance & Anomaly Analytics Framework")
    st.write("---")
    
    # Initialization and Extraction Checks
    table_name = "synthetic_telemetry"
    
    with st.spinner("Extracting operational core dataset from PostgreSQL server pipeline..."):
        try:
            query_str = f"SELECT * FROM {table_name};"
            df_fetched = fetch_telemetry_matrix(query_str)
            
            # Global standardization formatting enforcements across all telemetry slices
            df_fetched['shapefile_segment_name'] = df_fetched['shapefile_segment_name'].astype(str).str.upper()
            
            # Normalize timestamp field and extract hour safely
            if 'execution_timestamp' in df_fetched.columns:
                df_fetched['execution_timestamp'] = pd.to_datetime(df_fetched['execution_timestamp'])
                df_fetched['derived_hour'] = df_fetched['execution_timestamp'].dt.hour
            elif 'hour_of_day' in df_fetched.columns:
                df_fetched['derived_hour'] = df_fetched['hour_of_day']
            else:
                df_fetched['derived_hour'] = 8 # Fallback safe clock anchor
                
        except Exception as err:
            st.error("Structural database connection drop or pipeline execution block encountered.")
            with st.expander("Expand Traceback Logistics"):
                st.code(traceback.format_exc())
            return

    # =============================================================================
    # 4. SIDEBAR VERTICAL NAVIGATION TAB STRUCTURE CONTROL PANEL
    # =============================================================================
    st.sidebar.title("Network Modules Menu")
    st.sidebar.write("Navigate analytical segments below:")
    
    selected_tab = st.sidebar.radio(
        label="Select Diagnostic Framework",
        options=[
            "Dataset Overview & Audit Table",
            "Hypothesis 2: Peak Profiles & Failure Rates",
            "Hypothesis 4: Weather Sensitivity Slopes",
            "Hypothesis 7: 3D Topographical Gradients",
            "Hypothesis 8: Spatial Length Dilution Bias"
        ],
        index=0
    )
    
    st.sidebar.write("---")
    st.sidebar.info(f"Connected to: localhost/{table_name}\n\nRow Count Extracted: {len(df_fetched)}")

    # =============================================================================
    # MODULE TAB 1: DATASET OVERVIEW & AUDIT MATRIX TABLES
    # =============================================================================
    if selected_tab == "Dataset Overview & Audit Table":
        st.header("Telemetry Stream Overview & Pavement Integrity Audit Matrix")
        st.write("Provides a real-time macroscopic review of columns, data structures, and spatial configurations.")
        
        # Display high-level KPI cards at the top
        kpi_col1, kpi_col2, kpi_col3 = st.columns(3)
        with kpi_col1:
            st.metric(label="Total Network Scanned Rows", value=f"{len(df_fetched):,}")
        with kpi_col2:
            unique_corr = df_fetched['corridor_name'].nunique() if 'corridor_name' in df_fetched.columns else 0
            st.metric(label="Active High-Priority Corridors", value=unique_corr)
        with kpi_col3:
            unique_seg = df_fetched['shapefile_segment_name'].nunique() if 'shapefile_segment_name' in df_fetched.columns else 0
            st.metric(label="Monitored Shapefile Links", value=unique_seg)
            
        st.write("### Raw Database Table View Slice (First 100 Observed Records)")
        st.dataframe(df_fetched.head(100), use_container_width=True)
        
        st.write("### Metadata Data Column Profiles & Operational Summary Specs")
        buffer_summary = pd.DataFrame({
            'Data Column Type': df_fetched.dtypes.astype(str),
            'Non-Null Observations Counts': df_fetched.count(),
            'Missing Fields Null Density (%)': (df_fetched.isnull().sum() / len(df_fetched)) * 100
        })
        st.table(buffer_summary)

    # =============================================================================
    # MODULE TAB 2: TEMPORAL PEAK PROFILES & FAILURE RATE COMPARATIVE MATRIX
    # =============================================================================
    elif selected_tab == "Hypothesis 2: Peak Profiles & Failure Rates":
        st.header("Hypothesis 2: Temporal Peak Profiling & Infrastructure Failure Rates")
        st.write("Tracks 15-minute operational clock cycles to pinpoint the exact sequence of capacity breakdowns.")
        
        # Check for weekend mapping markers
        if 'is_weekend' not in df_fetched.columns:
            st.warning("Warning: Column tracker 'is_weekend' absent in database telemetry array. Applying logic layer mapping...")
            df_fetched['is_weekend'] = 0
            
        # Re-apply the dynamic context-aware failure calculations (90th Percentile)
        df_fetched['failure_threshold'] = df_fetched.groupby('corridor_name')['travel_time_index_tti'].transform(lambda x: x.quantile(0.90))
        df_fetched['is_failed'] = df_fetched['travel_time_index_tti'] > df_fetched['failure_threshold']
        
        # Build comparative table summary profiles
        corridor_records = []
        unique_corridors = df_fetched['corridor_name'].unique()
        
        for corr in unique_corridors:
            corr_df = df_fetched[df_fetched['corridor_name'] == corr]
            for is_we in [0, 1]:
                day_type = "Weekend" if is_we == 1 else "Weekday"
                sub_df = corr_df[corr_df['is_weekend'] == is_we]
                if len(sub_df) == 0: continue
                
                base_failure_rate = sub_df['is_failed'].mean()
                corridor_records.append({
                    'Corridor': corr, 'Day Profile': day_type, 'Calculated Failure Rate (%)': round(base_failure_rate * 100, 2)
                })
        
        report_df = pd.DataFrame(corridor_records)
        
        # RENDER GRAPH PANEL 1: Re-established Side-by-Side Comparative Bar Chart
        st.write("### Network Failure Rates: Weekdays vs. Weekends")
        
        fig, ax = plt.subplots(figsize=(10, 4.5))
        wd_data = report_df[report_df['Day Profile'] == 'Weekday']
        we_data = report_df[report_df['Day Profile'] == 'Weekend']
        
        x_indices = np.arange(len(wd_data))
        bar_width = 0.35
        
        ax.bar(x_indices - bar_width/2, wd_data['Calculated Failure Rate (%)'], bar_width, label='Weekday Failure %', color='#1f77b4', edgecolor='black')
        ax.bar(x_indices + bar_width/2, we_data['Calculated Failure Rate (%)'], bar_width, label='Weekend Failure %', color='#ff7f0e', edgecolor='black')
        
        ax.set_xticks(x_indices)
        ax.set_xticklabels(wd_data['Corridor'], rotation=10, ha='center', fontsize=9)
        ax.set_ylabel("Operating Windows in Breakdown State (%)", fontweight='bold')
        ax.grid(axis='y', linestyle=':', alpha=0.5)
        ax.legend(loc='upper right')
        plt.tight_layout()
        st.pyplot(fig)
        
        st.write("### System Failure Data Table View Summary")
        st.dataframe(report_df, use_container_width=True)

    # =============================================================================
    # MODULE TAB 3: WEATHER INTERACTION SENSITIVITY SLOPES
    # =============================================================================
    elif selected_tab == "Hypothesis 4: Weather Sensitivity Slopes":
        st.header("Hypothesis 4: Measuring Weather-Driven Environmental Variance")
        st.write("Calculates exactly how much rainfall intensity and drop in visibility degrade network capacity compared to a dry baseline.")
        
        # Enforce simulated or actual columns layers check
        if 'rainfall_intensity_mm_hr' not in df_fetched.columns:
            np.random.seed(42)
            df_fetched['rainfall_intensity_mm_hr'] = np.random.choice([0.0, 2.5, 8.0, 25.0], size=len(df_fetched), p=[0.75, 0.15, 0.07, 0.03])
            df_fetched['visibility_meters'] = np.where(df_fetched['rainfall_intensity_mm_hr'] == 0, 6000, 
                                               np.where(df_fetched['rainfall_intensity_mm_hr'] == 2.5, 3000,
                                               np.where(df_fetched['rainfall_intensity_mm_hr'] == 8.0, 1200, 400)))
            
        # Segment data records into strict meteorological states
        conditions = [
            (df_fetched['rainfall_intensity_mm_hr'] == 0.0),
            (df_fetched['rainfall_intensity_mm_hr'] > 0.0) & (df_fetched['rainfall_intensity_mm_hr'] <= 4.0),
            (df_fetched['rainfall_intensity_mm_hr'] > 4.0) & (df_fetched['rainfall_intensity_mm_hr'] <= 16.0),
            (df_fetched['rainfall_intensity_mm_hr'] > 16.0)
        ]
        choices = ['0_Dry Baseline', '1_Light Rain', '2_Moderate Rain', '3_Heavy Monsoon Anomaly']
        df_fetched['weather_state'] = np.select(conditions, choices, default='0_Dry Baseline')

        st.write("### Network Capacity Degradation Under Varying Weather States")
        pivot_weather = df_fetched.pivot_table(values='travel_time_index_tti', index='corridor_name', columns='weather_state', Turk='mean')
        st.dataframe(pivot_weather, use_container_width=True)
        
        # Plot continuous rain cascades distributions
        fig, ax = plt.subplots(figsize=(10, 4))
        pivot_weather.plot(kind='bar', ax=ax, edgecolor='black', cmap='viridis')
        ax.set_ylabel("Mean Travel Time Index (TTI)", fontweight='bold')
        ax.set_xlabel("Transit Corridor Name", fontweight='bold')
        plt.xticks(rotation=15)
        st.pyplot(fig)

    # =============================================================================
    # MODULE TAB 4: 3D TOPOGRAPHICAL GRADIENTS & INCLINE PENALTY MODELLING
    # =============================================================================
    elif selected_tab == "Hypothesis 7: 3D Topographical Gradients":
        st.header("Hypothesis 7: The 'Flyover Exit' & Uphill Gradient Penalties")
        st.write("Separates heavy fleet climb crawl limitations from elevated high-speed bottlenecks relocation anomalies.")
        
        # Structural Wildcard Engine Processing Layer
        df_fetched['network_layer_type'] = 'Standard At-Grade Link'
        df_fetched['elevation_gradient'] = 0.2
        
        ramp_mask = df_fetched['shapefile_segment_name'].str.contains('RAMP|ATGRADE|PUZHAL.*002|002')
        df_fetched.loc[ramp_mask, 'network_layer_type'] = 'At-Grade Off-Ramp Junction'
        df_fetched.loc[ramp_mask, 'elevation_gradient'] = -3.5
        
        flyover_mask = df_fetched['shapefile_segment_name'].str.contains('FLYOVER|ELEVATED|OMR|005') & ~ramp_mask
        df_fetched.loc[flyover_mask, 'network_layer_type'] = 'Elevated Flyover Mainline'
        df_fetched.loc[flyover_mask, 'elevation_gradient'] = 0.0
        
        incline_mask = df_fetched['shapefile_segment_name'].str.contains('INCLINE|UPHILL|KILAMBAKKAM|LITTLEMOUNT|018')
        df_fetched.loc[incline_mask, 'network_layer_type'] = 'Steep Incline Link'
        df_fetched.loc[incline_mask, 'elevation_gradient'] = 6.2

        segment_profiles = df_fetched.groupby(['corridor_name', 'shapefile_segment_name', 'network_layer_type', 'elevation_gradient']).agg(
            mean_tti=('travel_time_index_tti', 'mean'),
            max_tti=('travel_time_index_tti', 'max')
        ).reset_index()

        st.write("### Topographical Spatial Profiling Diagnostics Table")
        st.dataframe(segment_profiles, use_container_width=True)
        
        # Render bubble map distributions scatter profiles
        fig, ax = plt.subplots(figsize=(10, 4.5))
        sns.scatterplot(
            data=segment_profiles, x='elevation_gradient', y='mean_tti', 
            hue='network_layer_type', s=200, edgecolor='black', ax=ax
        )
        ax.set_xlabel("Physical Elevation Gradient Vector (%)", fontweight='bold')
        ax.set_ylabel("Mean Operating TTI", fontweight='bold')
        st.pyplot(fig)

    # =============================================================================
    # MODULE TAB 5: SPATIAL SLICING ACCURACY & LENGTH DILUTION ERROR ELIMINATION
    # =============================================================================
    elif selected_tab == "Hypothesis 8: Spatial Length Dilution Bias":
        st.header("Hypothesis 8: Spatial Slicing Accuracy & 'Length Dilution' Bias Eradication")
        st.write("Proves that long corridor tracking models artificially hide extreme localized bottlenecks by spatial smoothing.")
        
        if 'true_driving_distance_meters' not in df_fetched.columns:
            distance_map = {
                'PUZHAL_CENTRAL_ATGRADE_002': 450.0, 'CENTRAL_PUZHAL_021': 850.0,           
                'OMR_THIRUVANMIYUR_005': 600.0, 'KILAMBAKKAM_LITTLEMOUNT_018': 2400.0, 
                'TAMBARAM_GUINDY_025': 4800.0          
            }
            df_fetched['true_driving_distance_meters'] = df_fetched['shapefile_segment_name'].map(distance_map).fillna(1200.0)
        
        # Categorize spatial resolution groupings indices
        conditions = [
            (df_fetched['true_driving_distance_meters'] < 600),
            (df_fetched['true_driving_distance_meters'] >= 600) & (df_fetched['true_driving_distance_meters'] < 1500),
            (df_fetched['true_driving_distance_meters'] >= 1500)
        ]
        bins = ['High Resolution (<600m)', 'Medium Resolution (600m-1.5km)', 'Low Resolution (>=1.5km)']
        df_fetched['spatial_resolution_class'] = np.select(conditions, bins, default='Medium Resolution (600m-1.5km)')
        
        # Isolate peak hours using the derived hour field populated via extraction steps
        peak_df = df_fetched[df_fetched['derived_hour'].isin([8, 9, 17, 18, 19])].copy()
        
        st.write("### Advanced Spatial Frequency Signal Variance Collapse Profiles")
        fig, ax = plt.subplots(figsize=(10, 5))
        sns.boxplot(
            data=peak_df, x='spatial_resolution_class', y='travel_time_index_tti',
            hue='spatial_resolution_class', palette='Set2', ax=ax, legend=False
        )
        ax.set_ylabel("Observed Travel Time Index (TTI Spectrum)", fontweight='bold')
        ax.set_xlabel("Spatial Slicing Tracking Resolution Class", fontweight='bold')
        st.pyplot(fig)

if __name__ == "__main__":
    main()
