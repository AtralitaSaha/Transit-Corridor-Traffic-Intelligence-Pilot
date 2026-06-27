# 🚦 CUMTA Traffic Intelligence — Streamlit App
### Complete Setup & Usage Guide for First-Time Users

---

## What This App Does

This is a **multi-page interactive web dashboard** built with Streamlit that turns your
CUMTA PostgreSQL traffic database (or any exported CSV) into a live analytical tool.
It covers all five Atralita hypotheses:

| Module | Question it Answers |
|--------|---------------------|
| 🔴 H1 — Bottleneck Map | Which segments are root-cause bottlenecks vs spillover victims? |
| 🕒 H2 — Temporal Peaks | When exactly does the network fail and how long does recovery take? |
| 🌧️ H4 — Weather Impact | How much does rain degrade capacity vs a dry day? |
| 🛣️ H7 — Flyover & Slope | Do flyovers move congestion or eliminate it? Do inclines penalise heavy fleets? |
| 📐 H8 — Length Dilution | Are long segments hiding severe micro-congestion behind averages? |

Every chart is **interactive** — hover for values, zoom in/out, click legend items to toggle,
and download filtered data as CSV.

---

## Project File Structure

After following this guide, your folder will look like this:

```
cumta_app/                        ← Your project folder
│
├── app.py                        ← Main Streamlit app (entry point)
├── requirements.txt              ← Python packages list
├── README.md                     ← This file
│
└── utils/                        ← Analysis helper modules
    ├── __init__.py               ← Makes utils a Python package
    ├── data_loader.py            ← CSV / PostgreSQL / Demo data loaders
    └── analysis.py               ← All 5 hypothesis computation functions
```

---

## STEP 1 — Install Python (if you haven't already)

You need **Python 3.10 or higher**.

**Check if you already have it:**
```bash
python --version
# or
python3 --version
```
If the output shows `Python 3.10.x` or higher, you are good. Skip to Step 2.

**If not installed:**
- Go to https://www.python.org/downloads/
- Download the latest 3.x installer for your OS (Windows / macOS / Linux)
- During installation on **Windows**, tick ✅ **"Add Python to PATH"** before clicking Install
- Restart your terminal after installation

---

## STEP 2 — Download the App Files

You should already have the `cumta_app/` folder with all the files listed above.

**Confirm they are all present:**
```bash
# On macOS / Linux
ls cumta_app/
ls cumta_app/utils/

# On Windows (Command Prompt)
dir cumta_app\
dir cumta_app\utils\
```
You should see: `app.py`, `requirements.txt`, `README.md`, and inside `utils/`:
`__init__.py`, `data_loader.py`, `analysis.py`.

---

## STEP 3 — Create a Virtual Environment

A **virtual environment** is an isolated Python sandbox just for this project.
It prevents your project's packages from conflicting with other Python projects on your machine.

```bash
# Navigate into your project folder first
cd cumta_app

# Create the virtual environment (named 'venv')
python -m venv venv
```

This creates a new folder called `venv/` inside `cumta_app/`. You only do this **once**.

---

## STEP 4 — Activate the Virtual Environment

You must activate the environment **every time** you open a new terminal to work on this project.

**On macOS / Linux:**
```bash
source venv/bin/activate
```

**On Windows (Command Prompt):**
```bash
venv\Scripts\activate.bat
```

**On Windows (PowerShell):**
```bash
venv\Scripts\Activate.ps1
```

✅ You'll know it's active when your terminal prompt starts with `(venv)`:
```
(venv) your-computer:cumta_app $
```

---

## STEP 5 — Install All Dependencies

With the virtual environment active, install everything from `requirements.txt`:

```bash
pip install -r requirements.txt
```

This downloads and installs: Streamlit, Pandas, NumPy, Plotly, SciPy, SQLAlchemy,
and the PostgreSQL driver. It takes about 2–3 minutes the first time.

**Verify the install worked:**
```bash
streamlit --version
# Should print: Streamlit, version 1.3x.x
```

---

## STEP 6 — Run the App

Make sure you are inside the `cumta_app/` folder with the virtual environment active, then:

```bash
streamlit run app.py
```

Streamlit will print something like:
```
  You can now view your Streamlit app in your browser.

  Local URL:  http://localhost:8501
  Network URL: http://192.168.x.x:8501
```

Your **browser will open automatically** at `http://localhost:8501`.
If it doesn't open, copy-paste that URL into Chrome or Firefox.

**To stop the app:** press `Ctrl + C` in the terminal.

---

## STEP 7 — Choose Your Data Source

In the left sidebar, you will see **📂 Data Source** with three options:

### Option A: 🧪 Demo Data (Recommended for first run)
- Click **"Demo Data"** — it's selected by default
- The app instantly generates realistic synthetic traffic data (7,000 rows)
- Segment names mirror the actual CUMTA corridors: `OMR_Corridor_01`, `GST_Corridor_02`, etc.
- Use the slider to increase/decrease dataset size
- Click **"🔄 Regenerate"** to get a fresh random dataset

### Option B: 📄 Upload CSV
- Export your traffic table from your database as a CSV file
- Click **"Upload CSV"** in the sidebar
- Drag and drop (or browse to) your CSV file
- The app validates the columns automatically and tells you which modules are available

**Minimum columns your CSV must have:**
```
shapefile_segment_name
travel_time_index_tti
current_travel_time_seconds
free_flow_travel_time_seconds
hour_of_day
is_weekend
```

**Additional columns unlock more modules:**
```
precipitation_intensity_mm_h  →  unlocks H4 Weather
visibility_meters             →  unlocks H4 Weather
segment_slope_grade           →  unlocks H7 Flyover
network_layer_type            →  unlocks H7 Flyover
true_driving_distance_meters  →  unlocks H8 Length Dilution
```

### Option C: 🗄️ PostgreSQL (Production mode)
- Click **"PostgreSQL"** in the sidebar
- Fill in your database connection details:

```
Host     : localhost          (or your DB server IP)
Port     : 5432               (default PostgreSQL port)
Database : cumta_traffic       (your database name)
Username : postgres            (your DB username)
Password : ••••••••           (your DB password)
```

- Edit the SQL query to pull your data (default pulls 10,000 rows):
```sql
SELECT * FROM traffic_metrics ORDER BY RANDOM() LIMIT 10000;
```
- Click **"🔗 Connect & Load"**

> **💡 Tip for the team:** If you get an SSL error on the PostgreSQL connection,
> the app already appends `?sslmode=disable` to the connection string automatically.
> If you still see errors, check that PostgreSQL is running and the port is open.

---

## STEP 8 — Navigate the Analysis Pages

Once data is loaded, use the **🗂️ Analysis Modules** section in the sidebar to switch pages.

### 🏠 Dashboard
Your entry point. Shows:
- 5 top-level KPI cards (observation count, segments, mean TTI, max TTI, rainy %)
- Network-wide TTI distribution histogram
- Segment class donut chart
- Module readiness status (green = all required columns found)

### 🔴 H1 — Bottleneck Map
**What to do:**
1. Use the **"Root Cause TTI Threshold"** slider — raise it to be more conservative,
   lower it to flag more segments as bottlenecks
2. Use the **"Spillover TTI Threshold"** slider — segments between this and the root threshold
   are flagged as spillover victims
3. Use the **"Top N"** slider to show more or fewer segments in the ranking chart
4. Switch to the **"Priority Table"** tab to see a sortable, filterable table
5. Click **"⬇️ Download Priority List"** to export the ranked CSV for engineering handoff

**What the colours mean:**
- 🔴 Red bar = Root Cause Bottleneck (intervention target #1)
- 🟠 Orange bar = Spillover Victim (absorbing queue from root causes)
- 🟢 Green bar = Free Flow (operationally acceptable)

### 🕒 H2 — Temporal Peaks
**What to do:**
1. Adjust the **"Failure TTI Threshold"** — this defines what % of segments are
   "failing" at any given hour
2. Adjust the **"Clearance Baseline TTI"** — the app automatically finds the
   first hour after the peak where TTI drops back below this value
3. On the **"24-Hour TTI Profile"** tab, hover over the chart lines to see exact TTI
   values for each hour. The shaded band = ±1 standard deviation
4. On the **"Segment × Hour Heatmap"** tab, look for dark red squares — those are the
   worst segment+hour combinations

**Key things to look for:**
- If the Weekday line never drops below the clearance baseline → the network is in
  permanent congestion throughout the day
- Compare peak hour and clearance hour gap → this is your "recovery window"

### 🌧️ H4 — Weather Impact
**What to do:**
1. Adjust the **"Anomaly TTI Multiplier"** — raise it to flag only extreme weather events,
   lower it to flag more events as weather-driven
2. On the **"Rain Sensitivity Regression"** tab, look at the OLS slope:
   - `slope > 0` and `p < 0.05` → rain is statistically proven to worsen congestion
   - The slope value tells you: *"for every extra mm/hr of rain, TTI increases by X"*
3. On the **"Anomaly Segments"** tab — these are your most rain-vulnerable locations

### 🛣️ H7 — Flyover & Slope
**What to do:**
1. Check the Welch t-test result on the **"Layer Type Comparison"** tab:
   - `p < 0.05` → Express and At-Grade segments are statistically different in TTI
2. Look at the **"Exit Queue Candidates"** table — these At-Grade segments have
   suspiciously high TTI and likely sit directly after a flyover discharge point
3. On the **"Interaction Heatmap"** tab, find the darkest cell — that is the
   worst-performing infrastructure+slope combination in the network

### 📐 H8 — Length Dilution
**What to do:**
1. On the **"Length vs Peak TTI"** scatter, look at the regression line direction:
   - **Negative slope** = longer segments have lower detectable peak TTI → dilution confirmed
2. Switch to **"Quartile Analysis"** — if Q4 (longest segments) has the lowest
   Mean Peak TTI but the highest Dilution Gap %, the hypothesis is supported
3. The **"Dilution Gap Ranking"** tab lists segments where the gap between their
   absolute worst hour and their average is largest — these need sub-1km re-segmentation

### 📊 Raw Data Explorer
- Use the multiselect, sliders, and day-type filter to cut the raw data
- Click **"⬇️ Download Filtered Dataset"** to export any slice as CSV

---

## STEP 9 — Making Changes to the App

The app uses **hot-reload** — any time you save a `.py` file, Streamlit automatically
refreshes the browser. You do not need to restart the server.

### Changing TTI thresholds permanently
In `utils/analysis.py`, find the function `run_h1()` and change the default parameter values:
```python
def run_h1(df, root_thresh: float = 2.0, spillover_thresh: float = 1.5):
                              # ^^^^ change this      # ^^^^ and this
```

### Adding a new chart to a page
Open `app.py`, find the page section (look for `elif page == "h1":`) and add a
new `with tab4:` block with any Plotly chart.

### Changing the SQL query permanently
In `app.py`, find the `pg_query` text area and change the default value string.

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'streamlit'"
Your virtual environment is not activated. Run:
```bash
source venv/bin/activate     # macOS/Linux
venv\Scripts\activate.bat    # Windows
```
Then try again.

### "Address already in use" / port 8501 error
Another Streamlit instance is already running. Either:
- Stop it with `Ctrl + C` in the other terminal, or
- Run on a different port: `streamlit run app.py --server.port 8502`

### PostgreSQL connection error: "could not connect to server"
Check these in order:
1. Is PostgreSQL running? (`pg_ctl status` or check Services on Windows)
2. Is the port correct? (default is 5432)
3. Is the username/password correct?
4. If the DB is on a remote server, is your IP whitelisted in `pg_hba.conf`?

### "DtypeWarning" or NaN values appearing in charts
Your CSV has mixed data types in a column. The app auto-coerces numerics, but
if you see unexpected NaN rows, check the raw data in the **📊 Raw Data Explorer** page
and filter for rows where TTI is null.

### Charts appear blank / empty
This usually means the column used for that chart is missing or all-null in your dataset.
Check the **🏠 Dashboard → Module Readiness** section — it tells you which
modules have all required columns.

### App is slow on large datasets (>50,000 rows)
The app caches data loading with `@st.cache_data`. If you reload data frequently,
clear the cache by clicking **"🔄 Regenerate"** on the Demo page, or restart the app.
For very large datasets, add a `LIMIT` clause to your SQL query.

---

## Quick Command Reference

```bash
# First time setup (run once)
cd cumta_app
python -m venv venv
source venv/bin/activate      # Mac/Linux
pip install -r requirements.txt

# Every time you want to run the app
cd cumta_app
source venv/bin/activate      # Mac/Linux  |  venv\Scripts\activate.bat on Windows
streamlit run app.py

# Stop the app
Ctrl + C

# Update packages later
pip install -r requirements.txt --upgrade
```

---

## Data Column Quick Reference

| Column Name | Type | Used By | Description |
|-------------|------|---------|-------------|
| `shapefile_segment_name` | String | All | Unique segment identifier |
| `travel_time_index_tti` | Float | All | current_time / free_flow_time |
| `current_travel_time_seconds` | Float | H1 | Live traversal time |
| `free_flow_travel_time_seconds` | Float | H1 | Ideal traversal time |
| `hour_of_day` | Int [0–23] | H2 | Hour extracted from timestamp |
| `is_weekend` | Int [0 or 1] | H2 | 1 = Weekend, 0 = Weekday |
| `precipitation_intensity_mm_h` | Float | H4 | Rain intensity in mm/hr |
| `visibility_meters` | Float | H4 | Atmospheric visibility |
| `segment_slope_grade` | Float | H7 | ΔElevation / distance |
| `network_layer_type` | String | H7 | "Express" or "At-Grade" |
| `true_driving_distance_meters` | Float | H8 | Physical segment length |

---

*CUMTA Traffic Intelligence Pilot —  Analysis Module v1.0*
*All column names follow the Data Source & API Mapping Directory v1.*
