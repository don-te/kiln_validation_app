"""
Temporal Validation App for Brick Kiln Images
Multi-user support with progress tracking and keyboard shortcuts
Usage: streamlit run temporal_validation_app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
from pathlib import Path
import json
import random
from datetime import datetime
import fcntl  # For file locking

# =============================================================================
# PAGE CONFIG & THEME (clean black & white, minimal)
# =============================================================================
st.set_page_config(page_title="Kiln Validation", page_icon="⬛", layout="wide", initial_sidebar_state="expanded")

st.markdown("""<style>
/* ---- typography & layout ---- */
html, body, [data-testid="stAppViewContainer"] {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Inter", Roboto, sans-serif;
}
.block-container, div[data-testid="stMainBlockContainer"], div[data-testid="block-container"] {
    padding-top: 5rem !important;
    padding-bottom: 3rem !important;
    max-width: 1600px !important;
}
header[data-testid="stHeader"], [data-testid="stHeader"] {
    background: transparent !important;
    pointer-events: none;
}
header[data-testid="stHeader"] * {
    pointer-events: auto;
}
hr { margin: 0.6rem 0; border-color: #ececec; }

/* ---- buttons: monochrome, consistent ---- */
.stButton button { border-radius: 6px; font-weight: 500; }
.stButton button[kind="primary"] { background: #111; color: #fff; border: 1px solid #111; }
.stButton button[kind="primary"]:hover { background: #333; border-color: #333; }
.stButton button[kind="secondary"] { background: #fff; color: #111; border: 1px solid #d6d6d6; }
.stButton button[kind="secondary"]:hover { border-color: #111; color: #000; }

/* ---- segmented controls: tighter, selected option in green ---- */
div[data-testid="stSegmentedControl"] { margin-top: -0.4rem; }
div[data-testid="stSegmentedControl"] button { font-weight: 500; }
button[kind="segmented_controlActive"], button[data-testid="stBaseButton-segmented_controlActive"],
div[data-testid="stSegmentedControl"] button[aria-checked="true"], div[data-testid="stButtonGroup"] button[aria-checked="true"] {
    background: #16a34a !important; color: #fff !important; border-color: #16a34a !important; }
button[data-testid="stBaseButton-segmented_controlActive"] * { color: #fff !important; }

/* ---- images ---- */
.stImage img { border: 1px solid #e4e4e4; border-radius: 6px; transition: box-shadow .15s; }
.stImage img:hover { box-shadow: 0 2px 10px rgba(0,0,0,.18); }
.stImage figcaption { color: #555; font-weight: 600; font-size: 0.85rem; }

/* ---- annotation card ---- */
div[data-testid="stVerticalBlockBorderWrapper"] { border-color: #ececec; border-radius: 10px; }

/* ---- slim progress bar ---- */
div[data-testid="stProgress"] div[role="progressbar"] { height: 5px; }

/* ---- slim alerts / banners ---- */
div[data-testid="stAlert"] { padding: 0.35rem 0.75rem; border-radius: 6px; }
div[data-testid="stAlert"] p { font-size: 0.9rem; }

/* ---- inputs ---- */
div[data-testid="stTextInput"] input, div[data-testid="stNumberInput"] input { border-radius: 6px; }

/* ---- sidebar ---- */
section[data-testid="stSidebar"] { background: #fafafa; border-right: 1px solid #ececec; }
section[data-testid="stSidebar"] .block-container { padding-top: 1rem; }

/* ---- kbd hint styling ---- */
kbd {
    background: #f2f2f2; border: 1px solid #d6d6d6; border-bottom-width: 2px;
    border-radius: 4px; padding: 0px 5px; font-size: 0.78rem; color: #111;
    font-family: ui-monospace, monospace;
}
</style>""", unsafe_allow_html=True)

# =============================================================================
# LIGHT / DARK BACKGROUND TOGGLE
# =============================================================================
DARK_CSS = """<style>
[data-testid="stAppViewContainer"], [data-testid="stBottom"] { background: #101010 !important; }
header[data-testid="stHeader"], [data-testid="stHeader"] { background: transparent !important; }
.stApp, [data-testid="stMarkdownContainer"], [data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li { color: #e6e6e6; }
h1, h2, h3, h4, h5, h6 { color: #f2f2f2 !important; }
[data-testid="stCaptionContainer"] { color: #9a9a9a !important; }
section[data-testid="stSidebar"] { background: #161616 !important; border-right: 1px solid #262626 !important; }
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"],
section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] p { color: #d8d8d8 !important; }
.stButton button[kind="secondary"] { background: #1c1c1c !important; color: #e6e6e6 !important; border: 1px solid #3a3a3a !important; }
.stButton button[kind="secondary"]:hover { border-color: #fff !important; color: #fff !important; }
.stButton button[kind="primary"] { background: #f5f5f5 !important; color: #111 !important; border-color: #f5f5f5 !important; }
.stButton button[kind="primary"] p, .stButton button[data-testid="stBaseButton-primary"] p { color: #111 !important; }
.stButton button[data-testid="stBaseButton-primary"] { background: #f5f5f5 !important; color: #111 !important; border-color: #f5f5f5 !important; }
.stButton button[data-testid="stBaseButton-secondary"] { background: #1c1c1c !important; color: #e6e6e6 !important; border: 1px solid #3a3a3a !important; }
.stButton button[data-testid="stBaseButton-secondary"] p { color: inherit !important; }
button[kind="segmented_control"], button[data-testid="stBaseButton-segmented_control"],
div[data-testid="stSegmentedControl"] button, div[data-testid="stButtonGroup"] button {
    background: #1c1c1c !important; color: #d8d8d8 !important; border-color: #3a3a3a !important; }
button[kind="segmented_control"] *, button[data-testid="stBaseButton-segmented_control"] *,
div[data-testid="stSegmentedControl"] button *, div[data-testid="stButtonGroup"] button * { color: inherit !important; }
button[data-testid="stBaseButton-segmented_control"]:hover { background: #2a2a2a !important; color: #fff !important; }
button[kind="segmented_controlActive"], button[data-testid="stBaseButton-segmented_controlActive"],
div[data-testid="stSegmentedControl"] button[aria-checked="true"], div[data-testid="stButtonGroup"] button[aria-checked="true"] {
    background: #16a34a !important; color: #fff !important; border-color: #16a34a !important; }
button[data-testid="stBaseButton-segmented_controlActive"] * { color: #fff !important; }
div[data-testid="stTextInput"] input, div[data-testid="stNumberInput"] input {
    background: #1c1c1c !important; color: #e6e6e6 !important; border-color: #3a3a3a !important; }
div[data-testid="stNumberInput"] button { background: #1c1c1c !important; color: #e6e6e6 !important; }
div[data-testid="stAlert"] { background: #1b1f24 !important; }
div[data-testid="stAlert"] p { color: #dbe4ee !important; }
[data-testid="stMetricValue"], [data-testid="stMetricLabel"] { color: #eee !important; }
.stImage img { border-color: #333 !important; }
.stImage figcaption { color: #aaa !important; }
hr { border-color: #2a2a2a !important; }
kbd { background: #222 !important; border-color: #444 !important; color: #eee !important; }
label[data-testid="stWidgetLabel"] p { color: #d8d8d8 !important; }
div[data-testid="stVerticalBlockBorderWrapper"] { border-color: #2a2a2a !important; }
.stImage img:hover { box-shadow: 0 2px 10px rgba(255,255,255,.12) !important; }
</style>"""

with st.sidebar:
    st.toggle("🌙 Dark background", key="dark_mode")
if st.session_state.get("dark_mode", False):
    st.markdown(DARK_CSS, unsafe_allow_html=True)

# =============================================================================
# PATHS
# =============================================================================
PROJECT_ROOT = Path("/home/rishabh.mondal/Brick-Kilns-project/ijcai_2025_kilns/temporal-analysis")
IMAGE_PATH = PROJECT_ROOT / "new_downloaded_all_year_data"
PREDICTION_FILE = PROJECT_ROOT / "model_prediction_csv" / "gemini-3m-pro_kiln_sentinelklindb_and_beyond_with_bbox_from_csv_clean.csv"
OUTPUT_PATH = Path("/home/thejastg/validation_app/temporal_validation_results.json")

YEAR_FOLDERS = {
    2014: "all_kilns_2014-03-26_zoom17_buffer25", 2015: "all_kilns_2015-03-18_zoom17_buffer25",
    2016: "all_kilns_2016-03-16_zoom17_buffer25", 2017: "all_kilns_2017-03-15_zoom17_buffer25",
    2018: "all_kilns_2018-03-14_zoom17_buffer25", 2019: "all_kilns_2019-03-13_zoom17_buffer25",
    2020: "all_kilns_2020-03-23_zoom17_buffer25", 2021: "all_kilns_2021-03-17_zoom17_buffer25",
    2022: "all_kilns_2022-03-16_zoom17_buffer25", 2023: "all_kilns_2023-03-15_zoom17_buffer25",
    2024: "all_kilns_2024-03-28_zoom17_buffer25", 2025: "all_kilns_2025-03-27_zoom17_buffer25",
    2026: "all_kilns_2026-03-26_zoom17_buffer25",
}
YEARS = [2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026]
TYPES = ["FCBK", "CFCBK", "Zigzag", "Other"]

# Recently submitted locations stay in the Unvalidated / Needs Review queue so quick
# mistakes can be corrected; an item leaves on the REVIEW_WINDOW-th submit (counting its own).
REVIEW_WINDOW = 5
PENDING_QUEUES = ("⚡ Only Unvalidated", "⚠ Needs Review")

# =============================================================================
# REGIONS (geojson boundaries for region-wise validation)
# =============================================================================
REGION_DIR = PROJECT_ROOT.parent / "regions" / "shapes"

# Countries with flags, pinned to the top of the dropdown
_COUNTRIES = {
    "🇧🇩 Bangladesh": "bangladesh.geojson",
    "🇮🇳 India": "india.geojson",
    "🇵🇰 Pakistan": "pakistan_admin0.geojson",
    "🇳🇵 Nepal": "nepal.geojson",
    "🇦🇫 Afghanistan": "afghanistan.geojson",
}

def _discover_regions():
    """All remaining .geojson files in the shapes dir -> {pretty name: filename}."""
    taken = set(_COUNTRIES.values())
    regions = {}
    for f in sorted(REGION_DIR.glob("*.geojson"), key=lambda p: p.stem.lower()):
        if f.name in taken:
            continue
        name = f.stem.replace("_", " ").strip().title()
        regions.setdefault(name, f.name)
    return regions

REGIONS = {"🌍 All Regions": None,
           **{k: v for k, v in _COUNTRIES.items() if (REGION_DIR / v).exists()},
           **_discover_regions()}

# =============================================================================
# FUNCTIONS
# =============================================================================
@st.cache_data
def load_data():
    df = pd.read_csv(PREDICTION_FILE, low_memory=False)
    return df

@st.cache_data(show_spinner="🌍 Filtering locations by region…")
def filter_by_region(region_file, locations):
    """Point-in-polygon filter of lat_lon strings against a region geojson.
    Cached: the spatial test runs once per region, then it's a dict lookup."""
    import geopandas as gpd
    import shapely
    import numpy as np
    gdf = gpd.read_file(REGION_DIR / region_file)
    geom = gdf.geometry.union_all() if hasattr(gdf.geometry, 'union_all') else gdf.geometry.unary_union
    shapely.prepare(geom)
    lats = np.array([float(l.split('_')[0]) for l in locations])
    lons = np.array([float(l.split('_')[1]) for l in locations])
    mask = shapely.covers(geom, shapely.points(lons, lats))
    return [l for l, m in zip(locations, mask) if m]

@st.cache_data(show_spinner=False)
def load_country_location_dict(all_locations_tuple):
    """Precompute country -> location list mappings for the World View."""
    import geopandas as gpd
    import shapely
    import numpy as np
    lats = np.array([float(l.split('_')[0]) for l in all_locations_tuple])
    lons = np.array([float(l.split('_')[1]) for l in all_locations_tuple])
    points = shapely.points(lons, lats)
    country_locs = {}
    for name, f in _COUNTRIES.items():
        p = REGION_DIR / f
        if not p.exists():
            continue
        try:
            gdf = gpd.read_file(p)
            geom = gdf.geometry.union_all() if hasattr(gdf.geometry, 'union_all') else gdf.geometry.unary_union
            shapely.prepare(geom)
            mask = shapely.covers(geom, points)
            country_locs[name] = [l for l, m in zip(all_locations_tuple, mask) if m]
        except Exception:
            pass
    return country_locs

def render_world_view(df, validated):
    st.markdown("## 🗺️ Kiln Validation World Overview")
    st.caption("Track validated vs. unvalidated brick kilns across regions in real time.")

    total_kilns = len(st.session_state.all_locations)
    val_set = set(validated.keys())
    val_total = len(val_set)
    doubt_set = {k for k, v in validated.items() if v.get('needs_expert_review', False)}
    doubt_total = len(doubt_set)
    conf_total = val_total - doubt_total
    unval_total = total_kilns - val_total
    pct = (val_total / total_kilns * 100) if total_kilns else 0.0

    # Summary metrics
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Total Kilns", f"{total_kilns:,}")
    m2.metric("Validated", f"{val_total:,}", f"{pct:.1f}%")
    m3.metric("Remaining Unvalidated", f"{unval_total:,}")
    m4.metric("Confident ✓", f"{conf_total:,}")
    m5.metric("Needs Review ⚠", f"{doubt_total:,}")
    st.progress(val_total / total_kilns if total_kilns else 0)

    st.markdown("---")

    # Map section
    st.markdown("### 🌐 Subcontinent Spatial Coverage")
    mc1, mc2 = st.columns([1.5, 1.5])
    with mc1:
        map_status = st.selectbox(
            "Filter map points",
            ["All Points", "⚡ Unvalidated Only", "✅ Validated Only", "⚠ Doubtful Only"],
            key="world_map_status"
        )
    with mc2:
        country_keys = ["🌍 All Regions"] + list(_COUNTRIES.keys())
        focus_country = st.selectbox("Focus Region", country_keys, key="world_map_focus")

    # Prepare map dataframe
    map_df = df[['lat', 'lon', 'lat_lon']].copy()

    country_dict = load_country_location_dict(tuple(st.session_state.all_locations))
    if focus_country != "🌍 All Regions" and focus_country in country_dict:
        c_set = set(country_dict[focus_country])
        map_df = map_df[map_df['lat_lon'].isin(c_set)]

    # Assign status & colors
    conf_set = val_set - doubt_set
    status_arr = np.where(map_df['lat_lon'].isin(conf_set), 'Validated',
                 np.where(map_df['lat_lon'].isin(doubt_set), 'Doubtful', 'Unvalidated'))
    map_df['status'] = status_arr

    # Filter by map status
    if map_status == "⚡ Unvalidated Only":
        map_df = map_df[map_df['status'] == 'Unvalidated']
    elif map_status == "✅ Validated Only":
        map_df = map_df[map_df['status'] == 'Validated']
    elif map_status == "⚠ Doubtful Only":
        map_df = map_df[map_df['status'] == 'Doubtful']

    # RGBA color mapping
    color_map = {
        'Validated': [34, 197, 94, 210],
        'Doubtful': [249, 115, 22, 230],
        'Unvalidated': [239, 68, 68, 150]
    }
    if not map_df.empty:
        colors = np.array([color_map[s] for s in map_df['status']])
        map_df['r'] = colors[:, 0]
        map_df['g'] = colors[:, 1]
        map_df['b'] = colors[:, 2]
        map_df['a'] = colors[:, 3]

        map_df['validator_name'] = map_df['lat_lon'].map(lambda l: validated.get(l, {}).get('validator', 'None'))

        COUNTRY_CENTERS = {
            "🌍 All Regions": (24.5, 80.5, 4.2),
            "🇧🇩 Bangladesh": (23.7, 90.3, 6.6),
            "🇮🇳 India": (23.5, 80.0, 4.5),
            "🇵🇰 Pakistan": (30.5, 71.5, 5.2),
            "🇳🇵 Nepal": (28.2, 84.0, 6.6),
            "🇦🇫 Afghanistan": (33.8, 66.0, 5.6),
        }
        center_lat, center_lon, zoom_level = COUNTRY_CENTERS.get(focus_country, (24.5, 80.5, 4.2))

        layer = pdk.Layer(
            'ScatterplotLayer',
            data=map_df,
            get_position='[lon, lat]',
            get_fill_color='[r, g, b, a]',
            get_radius=2200 if focus_country == "🌍 All Regions" else 1200,
            pickable=True,
        )
        view_state = pdk.ViewState(latitude=center_lat, longitude=center_lon, zoom=zoom_level, pitch=0)
        tooltip = {
            "html": "<b>Location:</b> {lat_lon}<br/>"
                    "<b>Status:</b> {status}<br/>"
                    "<b>Validator:</b> {validator_name}",
            "style": {"backgroundColor": "#18181b", "color": "#f4f4f5", "fontSize": "12px", "borderRadius": "4px", "padding": "6px"}
        }
        st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view_state, tooltip=tooltip), height=520)
        st.markdown(
            "<div style='display:flex;gap:1.5rem;font-size:0.85rem;margin-top:-0.5rem;margin-bottom:1rem;color:#777;'>"
            "<span><span style='color:#22c55e;'>●</span> Validated Confident</span>"
            "<span><span style='color:#f97316;'>●</span> Needs Review / Doubt</span>"
            "<span><span style='color:#ef4444;'>●</span> Unvalidated (Remaining)</span>"
            f"<span style='margin-left:auto;'>Showing {len(map_df):,} points</span>"
            "</div>",
            unsafe_allow_html=True
        )
    else:
        st.info("No points match the selected filters.")

    st.markdown("---")

    # Regional progress table
    st.markdown("### 📊 Regional Progress Breakdown")
    st.caption("Select any region below to immediately jump into validating its remaining unvalidated kilns.")

    rows = []
    for c_name in _COUNTRIES.keys():
        if c_name not in country_dict:
            continue
        c_locs = country_dict[c_name]
        c_tot = len(c_locs)
        c_val = sum(1 for l in c_locs if l in val_set)
        c_rem = c_tot - c_val
        c_doubt = sum(1 for l in c_locs if l in doubt_set)
        c_pct = (c_val / c_tot * 100) if c_tot else 0.0
        rows.append({
            "Region": c_name,
            "Total Kilns": c_tot,
            "Validated": c_val,
            "Remaining": c_rem,
            "Doubtful": c_doubt,
            "Progress": f"{c_pct:.1f}%",
        })

    if rows:
        t_cols = st.columns([2.5, 1.2, 1.2, 1.2, 1.2, 1.5])
        t_cols[0].markdown("**Region**")
        t_cols[1].markdown("**Total**")
        t_cols[2].markdown("**Validated**")
        t_cols[3].markdown("**Remaining**")
        t_cols[4].markdown("**Doubtful**")
        t_cols[5].markdown("**Progress**")
        st.markdown("<hr style='margin:0.2rem 0 0.5rem 0;'>", unsafe_allow_html=True)

        for r in rows:
            rc = st.columns([2.5, 1.2, 1.2, 1.2, 1.2, 1.5])
            rc[0].markdown(f"**{r['Region']}**")
            rc[1].markdown(f"{r['Total Kilns']:,}")
            rc[2].markdown(f"<span style='color:#16a34a;font-weight:600;'>{r['Validated']:,}</span>", unsafe_allow_html=True)
            rc[3].markdown(f"<span style='color:{'#ef4444' if r['Remaining'] > 0 else '#888'};font-weight:600;'>{r['Remaining']:,}</span>", unsafe_allow_html=True)
            rc[4].markdown(f"<span style='color:#f59e0b;'>{r['Doubtful']:,}</span>", unsafe_allow_html=True)
            rc[5].markdown(f"**{r['Progress']}**")

        st.markdown("<br>", unsafe_allow_html=True)
        q1, q2 = st.columns([3, 2])
        with q1:
            jump_region = st.selectbox(
                "Select a region to validate:",
                list(_COUNTRIES.keys()),
                key="jump_region_select"
            )
        with q2:
            st.markdown("<div style='height:1.75rem'></div>", unsafe_allow_html=True)
            if st.button("Start Validating Region ➜", type="primary", width="stretch"):
                st.session_state.region = jump_region
                st.session_state.active_region = None
                st.session_state.queue_filter = "⚡ Only Unvalidated"
                st.session_state.app_mode = "✍️ Validate"
                st.session_state.idx = 0
                st.rerun()

@st.cache_resource(show_spinner=False)
def _country_outlines():
    """Simplified country boundaries for the static report map."""
    import geopandas as gpd
    outlines = []
    for name, f in _COUNTRIES.items():
        p = REGION_DIR / f
        if p.exists():
            try:
                outlines.append(gpd.read_file(p).to_crs(4326).geometry.simplify(0.02))
            except Exception:
                pass
    return outlines

def build_status_report(df, validated, all_locations):
    """One-page status snapshot (map + progress + breakdowns) as PNG and PDF bytes."""
    import io
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.gridspec import GridSpec
    from datetime import timedelta

    GREEN, ORANGE, RED, INK, MUTED, GRID = "#16a34a", "#f97316", "#ef4444", "#111111", "#6b7280", "#e5e7eb"

    total = len(all_locations)
    val_set = set(validated)
    doubt_set = {k for k, v in validated.items() if v.get('needs_expert_review', False)}
    n_val, n_doubt = len(val_set), len(doubt_set)
    pct = n_val / total * 100 if total else 0.0

    fig = plt.figure(figsize=(16, 10), dpi=110, facecolor="white")
    gs = GridSpec(12, 16, figure=fig, left=0.03, right=0.98, top=0.95, bottom=0.04, hspace=1.4, wspace=1.2)

    # --- header ---
    fig.text(0.03, 0.965, "Brick Kiln Temporal Validation — Status", fontsize=21, weight="bold", color=INK)
    fig.text(0.98, 0.965, datetime.now().strftime("Snapshot: %d %b %Y, %H:%M"), fontsize=11, color=MUTED, ha="right")

    # --- KPI tiles ---
    kpis = [("Total kilns", f"{total:,}", INK), ("Validated", f"{n_val:,}  ({pct:.1f}%)", GREEN),
            ("Remaining", f"{total - n_val:,}", RED), ("Needs expert review", f"{n_doubt:,}", ORANGE)]
    for i, (label, value, color) in enumerate(kpis):
        ax = fig.add_subplot(gs[0:2, i * 4:(i + 1) * 4])
        ax.axis("off")
        ax.text(0, 0.75, label.upper(), fontsize=10, color=MUTED, weight="bold", transform=ax.transAxes)
        ax.text(0, 0.3, value, fontsize=22, color=color, weight="bold", transform=ax.transAxes)

    # --- progress bar ---
    ax = fig.add_subplot(gs[2, :])
    conf_frac = (n_val - n_doubt) / total if total else 0
    doubt_frac = n_doubt / total if total else 0
    ax.barh(0, 1, color=GRID, height=0.6)
    ax.barh(0, conf_frac, color=GREEN, height=0.6)
    ax.barh(0, doubt_frac, left=conf_frac, color=ORANGE, height=0.6)
    ax.set_xlim(0, 1)
    ax.axis("off")

    # --- map ---
    ax = fig.add_subplot(gs[3:12, 0:9])
    for g in _country_outlines():
        g.boundary.plot(ax=ax, color="#9ca3af", linewidth=0.6)
    pts = df[['lat', 'lon', 'lat_lon']]
    is_doubt = pts['lat_lon'].isin(doubt_set)
    is_conf = pts['lat_lon'].isin(val_set) & ~is_doubt
    is_unval = ~pts['lat_lon'].isin(val_set)
    for mask, color, size, alpha, label in [(is_unval, RED, 1.2, 0.35, "Unvalidated"),
                                            (is_conf, GREEN, 1.5, 0.6, "Validated"),
                                            (is_doubt, ORANGE, 5, 0.9, "Needs review")]:
        sub = pts[mask]
        ax.scatter(sub['lon'], sub['lat'], s=size, c=color, alpha=alpha, linewidths=0,
                   label=f"{label} ({mask.sum():,})", rasterized=True)
    ax.set_xlim(60, 98)
    ax.set_ylim(6, 38)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_color(GRID)
    ax.set_title("Spatial coverage", loc="left", fontsize=13, weight="bold", color=INK)
    leg = ax.legend(loc="lower left", fontsize=10, frameon=True)
    leg.get_frame().set_edgecolor(GRID)
    for h in leg.legend_handles:
        h.set_sizes([30])
        h.set_alpha(1)

    # --- region table ---
    ax = fig.add_subplot(gs[3:7, 9:16])
    ax.axis("off")
    ax.set_title("Progress by country", loc="left", fontsize=13, weight="bold", color=INK)
    country_dict = load_country_location_dict(tuple(all_locations))
    rows, covered = [], set()
    for name, locs_c in country_dict.items():
        covered.update(locs_c)
        c_val = sum(1 for l in locs_c if l in val_set)
        rows.append((name.split(" ", 1)[-1], len(locs_c), c_val))
    other = [l for l in all_locations if l not in covered]
    if other:
        rows.append(("Other", len(other), sum(1 for l in other if l in val_set)))
    rows.sort(key=lambda r: -r[1])
    y = 0.86
    for x, h in [(0.0, "Country"), (0.34, "Validated / Total")]:
        ax.text(x, y, h, fontsize=10, color=MUTED, weight="bold", transform=ax.transAxes)
    for name, c_tot, c_val in rows:
        y -= 0.14
        frac = c_val / c_tot if c_tot else 0
        ax.text(0.0, y, name, fontsize=11, color=INK, transform=ax.transAxes)
        ax.text(0.34, y, f"{c_val:,} / {c_tot:,}", fontsize=11, color=INK, transform=ax.transAxes)
        ax.add_patch(plt.Rectangle((0.66, y + 0.01), 0.26, 0.06, color=GRID, transform=ax.transAxes))
        ax.add_patch(plt.Rectangle((0.66, y + 0.01), 0.26 * frac, 0.06, color=GREEN, transform=ax.transAxes))
        ax.text(0.94, y, f"{frac * 100:.0f}%", fontsize=10, color=MUTED, transform=ax.transAxes)

    # --- validators (case-insensitive merge, most common spelling shown) ---
    ax = fig.add_subplot(gs[7:12, 9:12])
    counts, spellings = {}, {}
    for e in validated.values():
        v = str(e.get('validator', 'Unknown')).strip()
        k = v.lower()
        counts[k] = counts.get(k, 0) + 1
        spellings.setdefault(k, {}).setdefault(v, 0)
        spellings[k][v] += 1
    top = sorted(counts.items(), key=lambda x: -x[1])[:6][::-1]
    names = [max(spellings[k], key=spellings[k].get) for k, _ in top]
    vals = [c for _, c in top]
    ax.barh(names, vals, color=INK, height=0.6)
    for i, v in enumerate(vals):
        ax.text(v, i, f" {v:,}", va="center", fontsize=9, color=INK)
    ax.set_title("By validator", loc="left", fontsize=13, weight="bold", color=INK)
    ax.set_xlim(0, max(vals) * 1.35 if vals else 1)
    ax.set_xticks([])
    ax.tick_params(axis="y", labelsize=10, length=0)
    for s in ["top", "right", "bottom"]:
        ax.spines[s].set_visible(False)

    # --- daily pace (last 14 days) + model agreement ---
    ax = fig.add_subplot(gs[7:10, 12:16])
    today = datetime.now().date()
    days = [today - timedelta(days=i) for i in range(13, -1, -1)]
    per_day = {d: 0 for d in days}
    for e in validated.values():
        try:
            d = datetime.fromisoformat(str(e.get('timestamp', ''))).date()
        except ValueError:
            continue
        if d in per_day:
            per_day[d] += 1
    ax.bar(range(len(days)), [per_day[d] for d in days], color=GREEN, width=0.7)
    ax.set_xticks([0, len(days) - 1], [days[0].strftime("%d %b"), days[-1].strftime("%d %b")], fontsize=9)
    ax.tick_params(axis="y", labelsize=8)
    ax.set_title(f"Daily validations · last 7 days: {sum(per_day[d] for d in days[-7:]):,}",
                 loc="left", fontsize=11, weight="bold", color=INK)
    for s in ["top", "right"]:
        ax.spines[s].set_visible(False)

    ax = fig.add_subplot(gs[10:12, 12:16])
    ax.axis("off")
    mc = {"Yes": 0, "Partial": 0, "No": 0}
    for e in validated.values():
        if e.get('model_correct') in mc:
            mc[e['model_correct']] += 1
    n_mc = sum(mc.values()) or 1
    ax.text(0, 0.8, "Model prediction agreement", fontsize=11, weight="bold", color=INK, transform=ax.transAxes)
    left = 0
    for k, color in [("Yes", GREEN), ("Partial", ORANGE), ("No", RED)]:
        w = mc[k] / n_mc
        ax.add_patch(plt.Rectangle((left, 0.35), w, 0.25, color=color, transform=ax.transAxes))
        left += w
    ax.text(0, 0.0, "   ".join(f"{k}: {mc[k] / n_mc * 100:.0f}%" for k in mc),
            fontsize=10, color=MUTED, transform=ax.transAxes)

    out = {}
    for fmt in ("png", "pdf"):
        buf = io.BytesIO()
        fig.savefig(buf, format=fmt, facecolor="white")
        out[fmt] = buf.getvalue()
    plt.close(fig)
    return out

def render_share_report(df, validated):
    """Sidebar block: build a shareable snapshot on demand and offer PNG / PDF downloads."""
    st.markdown("#### 📤 Share Status")
    st.caption("One-page snapshot (map, progress, breakdowns) to send on Slack / email.")
    if st.button("Generate report", width="stretch"):
        with st.spinner("Rendering report…"):
            st.session_state.share_report = build_status_report(df, validated, st.session_state.all_locations)
    report = st.session_state.get("share_report")
    if report:
        stamp = datetime.now().strftime("%Y%m%d")
        c1, c2 = st.columns(2)
        c1.download_button("🖼️ PNG", report["png"], f"kiln_validation_status_{stamp}.png", "image/png", width="stretch")
        c2.download_button("📄 PDF", report["pdf"], f"kiln_validation_status_{stamp}.pdf", "application/pdf", width="stretch")

@st.cache_data(show_spinner=False)
def find_images(lat_lon):
    images = {}
    for year, folder in YEAR_FOLDERS.items():
        img_path = IMAGE_PATH / folder / f"{lat_lon}_{year}.png"
        if img_path.exists():
            images[year] = str(img_path)
    return images

@st.cache_data(show_spinner=False, max_entries=1000)
def load_image_bytes(path):
    """Read PNG once, recompress to JPEG in-memory: ~5x smaller network transfer."""
    try:
        from PIL import Image
        import io
        img = Image.open(path)
        buf = io.BytesIO()
        img.convert("RGB").save(buf, "JPEG", quality=88)
        return buf.getvalue()
    except Exception:
        return Path(path).read_bytes()

@st.cache_data(show_spinner=False, max_entries=4)
def _load_results_cached(mtime):
    """Parse results JSON only when the file actually changed (mtime keyed)."""
    try:
        with open(OUTPUT_PATH, 'r') as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_SH)
            data = json.load(f)
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
            return data
    except:
        return {'validated': {}}

def load_results():
    """Load results with file locking for multi-user safety"""
    if OUTPUT_PATH.exists():
        return _load_results_cached(OUTPUT_PATH.stat().st_mtime)
    return {'validated': {}}

def save_results(entry, loc, validator):
    """Save single entry with file locking for multi-user safety"""
    try:
        if OUTPUT_PATH.exists():
            with open(OUTPUT_PATH, 'r+') as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                try:
                    data = json.load(f)
                except:
                    data = {'validated': {}}
                data.setdefault('validated', {})[loc] = entry
                f.seek(0)
                f.truncate()
                json.dump(data, f, indent=2, default=str)
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        else:
            with open(OUTPUT_PATH, 'w') as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                json.dump({'validated': {loc: entry}}, f, indent=2, default=str)
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        return True
    except Exception as e:
        st.error(f"Save error: {e}")
        return False

def get_default_year(year_val):
    try:
        if pd.isna(year_val) or year_val == 0 or year_val is None:
            return None
        y = int(year_val)
        return y if y in YEARS else None
    except:
        return None

def get_default_type(type_val):
    try:
        if pd.isna(type_val) or type_val is None:
            return "FCBK"
        t = str(type_val)
        return t if t in TYPES else "FCBK"
    except:
        return "FCBK"

def fmt_year(v):
    """Short label for year options: 2014 -> '14; strings pass through."""
    return f"'{str(v)[2:]}" if isinstance(v, int) else str(v)

# =============================================================================
# VALIDATOR LOGIN
# =============================================================================
if 'validator' not in st.session_state:
    st.session_state.validator = None

if st.session_state.validator is None:
    st.markdown("# ⬛ Kiln Temporal Validation")
    st.caption("Enter your name to start validating. Multiple people can validate simultaneously.")
    col1, col2 = st.columns([2, 1])
    with col1:
        name = st.text_input("Your Name", placeholder="e.g., Rishabh, Priya, John...")
    with col2:
        st.markdown("<div style='height:1.7rem'></div>", unsafe_allow_html=True)
        if st.button("Start Validating →", type="primary", width="stretch") and name.strip():
            st.session_state.validator = name.strip()
            st.rerun()
    st.markdown("---")
    st.markdown("#### Current Progress")
    results = load_results()
    validated = results.get('validated', {})
    if validated:
        by_validator = {}
        for loc, entry in validated.items():
            v = entry.get('validator', 'Unknown')
            by_validator[v] = by_validator.get(v, 0) + 1
        cols = st.columns(min(len(by_validator) + 1, 6))
        cols[0].metric("Total Validated", len(validated))
        for i, (v, count) in enumerate(sorted(by_validator.items(), key=lambda x: -x[1])):
            cols[(i + 1) % len(cols)].metric(v, count)
    else:
        st.info("No validations yet. Be the first!")
    st.stop()

# =============================================================================
# LOAD DATA
# =============================================================================
if 'df' not in st.session_state:
    st.session_state.df = load_data()
    st.session_state.all_locations = st.session_state.df['lat_lon'].unique().tolist()
    st.session_state.region_locations = st.session_state.all_locations
    st.session_state.idx = 0

df = st.session_state.df
results = load_results()
validated = results.get('validated', {})

# =============================================================================
# VIEW MODE (Sidebar: Validate vs World View)
# =============================================================================
with st.sidebar:
    st.markdown(f"**👤 Validator:** `{st.session_state.validator}`")
    app_mode = st.radio(
        "Navigation Mode",
        ["✍️ Validate", "🗺️ World View"],
        key="app_mode",
        horizontal=True,
        label_visibility="collapsed"
    )
    st.markdown("---")

if app_mode == "🗺️ World View":
    render_world_view(df, validated)
    with st.sidebar:
        st.markdown("#### 📊 Global Progress")
        col1, col2 = st.columns(2)
        col1.metric("Validated", len(validated))
        col2.metric("Remaining", len(st.session_state.all_locations) - len(validated))
        st.progress(len(validated) / len(st.session_state.all_locations) if st.session_state.all_locations else 0)

        st.markdown("##### By Validator")
        by_validator = {}
        for loc_v, entry in validated.items():
            v = entry.get('validator', 'Unknown')
            by_validator[v] = by_validator.get(v, 0) + 1
        for v, count in sorted(by_validator.items(), key=lambda x: -x[1]):
            v_doubtful = sum(1 for e in validated.values() if e.get('validator') == v and e.get('needs_expert_review', False))
            marker = "→ " if v == st.session_state.validator else ""
            st.markdown(f"{marker}**{v}**: {count} (⚠ {v_doubtful})")

        st.markdown("---")
        render_share_report(df, validated)
        if st.button("🔄 Refresh stats", width="stretch"):
            st.rerun()
        if validated:
            csv = pd.DataFrame.from_dict(validated, orient='index').to_csv()
            st.download_button("📥 Download CSV", csv, "validation_results.csv", "text/csv", width="stretch")

        with st.expander("📤 Restore from CSV Backup", expanded=False):
            st.caption("Upload your downloaded `validation_results.csv` to restore progress stats.")
            uploaded_backup = st.file_uploader("Upload CSV", type=["csv"], key="restore_csv_uploader_world", label_visibility="collapsed")
            if uploaded_backup is not None:
                if st.button("Apply & Restore Backup", type="primary", width="stretch"):
                    try:
                        from restore_from_csv import parse_csv_text, merge_and_save
                        raw_text = uploaded_backup.getvalue().decode("utf-8", errors="replace")
                        entries = parse_csv_text(raw_text)
                        if entries:
                            target_paths = [OUTPUT_PATH, Path(__file__).resolve().parent / "temporal_validation_results.json"]
                            success, msg = merge_and_save(entries, target_paths=target_paths)
                            if success:
                                _load_results_cached.clear()
                                st.toast(f"✅ Restored {len(entries):,} records!", icon="✅")
                                st.success(f"Restored {len(entries):,} records! Reloading...")
                                st.rerun()
                            else:
                                st.error(msg)
                        else:
                            st.error("No valid entries could be parsed from the uploaded CSV.")
                    except Exception as e:
                        st.error(f"Error restoring CSV: {e}")
    st.stop()

# =============================================================================
# REGION & QUEUE SELECTOR (sidebar top)
# =============================================================================
with st.sidebar:
    region = st.selectbox("📍 Validation Region", list(REGIONS.keys()), key="region",
                          help="Only locations inside the selected boundary are shown")
    queue_filter = st.selectbox(
        "🎯 Queue Filter",
        ["⚡ Only Unvalidated", "⚠ Needs Review", "✅ Validated", "🌐 All Locations"],
        key="queue_filter",
        help="Filter the queue so you only iterate through the points you need"
    )

if st.session_state.get('active_region') != region:
    st.session_state.active_region = region
    fname = REGIONS[region]
    if fname is None:
        st.session_state.region_locations = st.session_state.all_locations
    else:
        st.session_state.region_locations = filter_by_region(fname, tuple(st.session_state.all_locations))
    st.session_state.idx = 0
    st.session_state.recent_submits = []

region_locs = st.session_state.get('region_locations', st.session_state.all_locations)
if not region_locs:
    st.warning(f"No kiln locations found inside **{region}**. Choose another region.")
    st.stop()

# Reset index when filter changes
prev_filter = st.session_state.get('prev_queue_filter')
if prev_filter != queue_filter:
    st.session_state.prev_queue_filter = queue_filter
    st.session_state.idx = 0
    st.session_state.recent_submits = []  # saved already; they just join their real queue now

# Region-scoped validation stats
region_validated = {l: validated[l] for l in region_locs if l in validated}
region_doubt_count = sum(1 for e in region_validated.values() if e.get('needs_expert_review', False))

# Active queue based on filter (recent submits stay in place until they leave the window)
pending = st.session_state.setdefault('recent_submits', [])
pending_set = set(pending)
if queue_filter == "⚡ Only Unvalidated":
    locs = [l for l in region_locs if l not in validated or l in pending_set]
elif queue_filter == "⚠ Needs Review":
    locs = [l for l in region_locs if (l in validated and validated[l].get('needs_expert_review', False))
            or l in pending_set]
elif queue_filter == "✅ Validated":
    locs = [l for l in region_locs if l in validated]
else:  # "🌐 All Locations"
    locs = region_locs

if not locs:
    if queue_filter == "⚡ Only Unvalidated":
        st.success(f"🎉 **All {len(region_locs):,} kilns in {region} have been validated!**")
        col_a, col_b = st.columns(2)
        with col_a:
            if region_doubt_count > 0:
                if st.button(f"Review {region_doubt_count} Doubtful Kilns ⚠", width="stretch"):
                    st.session_state.queue_filter = "⚠ Needs Review"
                    st.session_state.idx = 0
                    st.rerun()
        with col_b:
            if st.button("View Validated Kilns ✓", width="stretch"):
                st.session_state.queue_filter = "✅ Validated"
                st.session_state.idx = 0
                st.rerun()
    elif queue_filter == "⚠ Needs Review":
        st.info(f"✨ No kilns currently flagged for review in **{region}**.")
        if st.button("Switch to Unvalidated Queue", width="stretch"):
            st.session_state.queue_filter = "⚡ Only Unvalidated"
            st.session_state.idx = 0
            st.rerun()
    elif queue_filter == "✅ Validated":
        st.info(f"⚪ No kilns validated yet in **{region}**.")
        if st.button("Start Validating", width="stretch"):
            st.session_state.queue_filter = "⚡ Only Unvalidated"
            st.session_state.idx = 0
            st.rerun()
    st.stop()

# After a submit, jump to the intended location by name (the list may have shifted)
goto_loc = st.session_state.pop('goto_loc', None)
if goto_loc in locs:
    st.session_state.idx = locs.index(goto_loc)

if st.session_state.idx >= len(locs):
    st.session_state.idx = max(0, len(locs) - 1)

# =============================================================================
# CURRENT LOCATION DATA
# =============================================================================
loc = locs[st.session_state.idx]
lat, lon = map(float, loc.split('_'))
images = find_images(loc)
pred = df[df['lat_lon'] == loc].iloc[0] if loc in df['lat_lon'].values else None

# Get defaults - prefer validated values, fallback to model predictions
is_validated_data = loc in validated

if is_validated_data:
    prev_val = validated[loc]
    default_presence = prev_val.get('presence', True)
    default_appear = get_default_year(prev_val.get('appearance_year'))
    default_type = get_default_type(prev_val.get('kiln_type', 'FCBK'))
    default_trans = get_default_year(prev_val.get('transition_year'))
    default_demolished = prev_val.get('demolished', False)
    default_demo_year = get_default_year(prev_val.get('demolished_year'))
    default_notes = prev_val.get('notes', '')
    model_note = pred.get('monitoring_note_one_line', '') if pred is not None else ''
elif pred is not None:
    default_presence = bool(pred.get('presence', True))
    default_appear = get_default_year(pred.get('appearance_year'))
    default_type = get_default_type(pred.get('appearance_type'))
    default_trans = get_default_year(pred.get('type_transition_year_after'))
    default_demolished = bool(pred.get('demolished', False))
    default_demo_year = get_default_year(pred.get('demolished_year'))
    default_notes = ''
    model_note = pred.get('monitoring_note_one_line', '')
else:
    default_presence, default_appear, default_type = True, 2014, "FCBK"
    default_trans, default_demolished, default_demo_year = None, False, None
    default_notes = ''
    model_note = ''

# Per-location widget keys - reset when navigating to a new location
loc_key = f"k_{loc}"
if st.session_state.get('prev_loc') != loc or f"{loc_key}_init" not in st.session_state:
    st.session_state.prev_loc = loc
    st.session_state[f"{loc_key}_presence"] = default_presence
    st.session_state[f"{loc_key}_appear"] = default_appear
    st.session_state[f"{loc_key}_type"] = default_type
    st.session_state[f"{loc_key}_trans"] = default_trans if default_trans else "None"
    st.session_state[f"{loc_key}_demo"] = default_demo_year if (default_demolished and default_demo_year) else "No"
    st.session_state[f"{loc_key}_correct"] = "✓"
    st.session_state[f"{loc_key}_notes"] = default_notes
    st.session_state[f"{loc_key}_init"] = True

# =============================================================================
# HEADER: location + status + navigation in two compact rows
# =============================================================================
h1, h2, h3, h4 = st.columns([2.6, 2.2, 1.6, 0.8])
with h1:
    st.markdown(f"#### ⬛ `{loc}`")
with h2:
    if loc in pending_set and loc in validated:
        left = (REVIEW_WINDOW - 1) - (len(pending) - 1 - pending.index(loc))
        st.markdown(f"✏️ **Submitted — still editable** · leaves queue in {left} submit{'s' if left != 1 else ''}")
    elif loc in validated:
        prev = validated[loc]
        if prev.get('needs_expert_review', False):
            st.markdown(f"🔴 **Needs review** — {prev.get('validator', '?')} · {prev.get('timestamp', '?')[:10]}")
        else:
            st.markdown(f"✅ **Validated** — {prev.get('validator', '?')} · {prev.get('timestamp', '?')[:10]}")
    else:
        st.markdown("⚪ **Unvalidated** — defaults are model predictions")
with h3:
    if queue_filter == "⚡ Only Unvalidated":
        st.markdown(f"**Unval {st.session_state.idx + 1} / {len(locs)}** · ✓ {len(region_validated)} / {len(region_locs)}"
                    f"<br><span style='font-size:0.75rem;color:#999'>{region}</span>",
                    unsafe_allow_html=True)
    else:
        st.markdown(f"**{st.session_state.idx + 1} / {len(locs)}** · ✓ {len(region_validated)} / {len(region_locs)}"
                    f"<br><span style='font-size:0.75rem;color:#999'>{region} ({queue_filter})</span>",
                    unsafe_allow_html=True)
with h4:
    if st.button("Logout", width="stretch"):
        st.session_state.validator = None
        st.rerun()

n1, n2, n3, n4, n5, n6 = st.columns([1, 1, 1.6, 1, 1.4, 1.1])
with n1:
    if st.button("◀ Prev", width="stretch", help="Shortcut: A") and st.session_state.idx > 0:
        st.session_state.idx -= 1
        st.rerun()
with n2:
    if st.button("Next ▶", width="stretch", help="Shortcut: D") and st.session_state.idx < len(locs) - 1:
        st.session_state.idx += 1
        st.rerun()
with n3:
    new_idx = st.number_input("Go to", 1, len(locs), st.session_state.idx + 1, label_visibility="collapsed")
    if new_idx - 1 != st.session_state.idx:
        st.session_state.idx = new_idx - 1
        st.rerun()
with n4:
    if st.button("Random", width="stretch", help="Shortcut: R"):
        st.session_state.idx = random.randint(0, len(locs) - 1)
        st.rerun()
with n5:
    if queue_filter == "⚡ Only Unvalidated":
        if st.button("Shuffle 🔀", width="stretch", help="Jump to random unvalidated item"):
            st.session_state.idx = random.randint(0, len(locs) - 1)
            st.rerun()
    else:
        if st.button("Unvalidated ⏭", width="stretch", help="Jump to next unvalidated · Shortcut: U"):
            for i in range(st.session_state.idx + 1, len(locs)):
                if locs[i] not in validated:
                    st.session_state.idx = i
                    st.rerun()
                    break
with n6:
    if st.button("Review ⚠", width="stretch", help="Jump to first item flagged for expert review"):
        for i in range(len(locs)):
            if locs[i] in validated and validated[locs[i]].get('needs_expert_review', False):
                st.session_state.idx = i
                st.rerun()
                break

# Thin overall-progress bar (region-scoped)
st.progress(len(region_validated) / len(region_locs) if region_locs else 0)

# =============================================================================
# IMAGES (TOP, always visible first)
# =============================================================================
def location_status_html():
    """Status of the CURRENT location: validated (by whom) or pending."""
    if loc in validated:
        entry = validated[loc]
        name = entry.get('validator', '?')
        date = str(entry.get('timestamp', ''))[:10]
        if entry.get('needs_expert_review', False):
            icon, label, color = "⚠", f"Doubt ({name})", "#b45309"
        else:
            icon, label, color = "✓", f"Validated ({name})", "#15803d"
        sub = date
    else:
        icon, label, color = "○", "Pending", "#999"
        sub = "not validated yet"
    return (f"<div style='font-size:0.85rem;line-height:1.6;padding:0.4rem 0.7rem;"
            f"border-left:3px solid {color};margin-top:0.5rem'>"
            f"<span style='color:{color};font-weight:600'>{icon} {label}</span><br>"
            f"<span style='color:#999;font-size:0.75rem'>{sub}</span></div>")

if images:
    years_list = sorted(images.keys())
    rows = [years_list[i:i+7] for i in range(0, len(years_list), 7)]
    for r, row in enumerate(rows):
        pad = 7 - len(row)
        is_last = r == len(rows) - 1
        # last row: merge the empty slots into one wide column for the validator summary
        cols = st.columns([1] * len(row) + [pad]) if (is_last and pad > 0) else st.columns(7)
        for j, y in enumerate(row):
            cols[j].image(load_image_bytes(images[y]), caption=str(y), width="stretch")
        if is_last and pad > 0:
            cols[-1].markdown(location_status_html(), unsafe_allow_html=True)
else:
    st.warning("No images found")

st.markdown("---")

# =============================================================================
# ANNOTATION CONTROLS (two compact rows) - fragment: no image re-render
# =============================================================================
@st.fragment
def validation_controls():
    with st.container(border=True):
        # --- Row 1: Present | Type | Appearance Year ---
        c1, c2, c3 = st.columns([1.1, 1.9, 4.5])
        with c1:
            st.segmented_control("**Present?** · :gray[Y/N]", [True, False],
                                 format_func=lambda v: "✓ Yes" if v else "✗ No",
                                 key=f"{loc_key}_presence")
        with c2:
            st.segmented_control("**Kiln Type** · :gray[1-4]", TYPES, key=f"{loc_key}_type")
        with c3:
            st.segmented_control("**Appearance Year**", YEARS,
                                 format_func=fmt_year, key=f"{loc_key}_appear")

        # --- Row 2: Transition | Demolished ---
        c1, c2 = st.columns(2)
        with c1:
            st.segmented_control("**Transition Year**", ["None"] + YEARS,
                                 format_func=fmt_year, key=f"{loc_key}_trans")
        with c2:
            st.segmented_control("**Demolished Year**", ["No"] + YEARS,
                                 format_func=fmt_year, key=f"{loc_key}_demo")

    # --- Action row: model verdict | notes | submit / doubt / skip ---
    c1, c2, c3, c4, c5 = st.columns([1.4, 3, 1.1, 1.1, 1.1])
    with c1:
        st.segmented_control("Model prediction OK?", ["✓", "~", "✗"],
                             key=f"{loc_key}_correct", label_visibility="collapsed",
                             help="Was the model prediction correct? ✓ yes · ~ partially · ✗ no")
    with c2:
        st.text_input("Notes", key=f"{loc_key}_notes",
                      label_visibility="collapsed", placeholder="Notes (optional)...")

    def build_entry(needs_review):
        trans = st.session_state[f"{loc_key}_trans"]
        demo = st.session_state[f"{loc_key}_demo"]
        presence = st.session_state[f"{loc_key}_presence"]
        return {
            'lat': lat, 'lon': lon,
            'validator': st.session_state.validator,
            'presence': bool(presence) if presence is not None else None,
            'appearance_year': st.session_state[f"{loc_key}_appear"],
            'kiln_type': st.session_state[f"{loc_key}_type"],
            'transition_year': trans if isinstance(trans, int) else None,
            'demolished': isinstance(demo, int),
            'demolished_year': demo if isinstance(demo, int) else None,
            'model_correct': {"✓": "Yes", "~": "Partial", "✗": "No"}.get(st.session_state[f"{loc_key}_correct"], "Yes"),
            'needs_expert_review': needs_review,
            'notes': st.session_state[f"{loc_key}_notes"],
            'timestamp': datetime.now().isoformat()
        }

    def submit(needs_review):
        if st.session_state[f"{loc_key}_presence"] is None:
            st.toast("⚠️ Select kiln presence (Y/N) before submitting", icon="⚠️")
            return
        if save_results(build_entry(needs_review), loc, st.session_state.validator):
            del st.session_state[f"{loc_key}_init"]
            if queue_filter in PENDING_QUEUES:
                # Re-submitting a correction keeps its original place in the window
                recent = st.session_state.recent_submits
                if loc not in recent:
                    recent.append(loc)
                keep = REVIEW_WINDOW - 1
                st.session_state.recent_submits = recent[-keep:] if keep > 0 else []
            idx = st.session_state.idx
            st.session_state.goto_loc = locs[idx + 1] if idx < len(locs) - 1 else loc
            st.rerun(scope="app")

    with c3:
        if st.button("Submit ✓", type="primary", width="stretch", help="Save & next · Shortcut: S"):
            submit(False)
    with c4:
        if st.button("Doubt ⚠", width="stretch", help="Save flagged for expert review & next · Shortcut: X"):
            submit(True)
    with c5:
        if st.button("Skip ▷", width="stretch", help="Next without saving · Shortcut: W"):
            del st.session_state[f"{loc_key}_init"]
            if st.session_state.idx < len(locs) - 1:
                st.session_state.idx += 1
            else:
                st.session_state.idx = 0
            st.rerun(scope="app")

validation_controls()

# =============================================================================
# KEYBOARD SHORTCUTS (global, disabled while typing in inputs)
# =============================================================================
st.iframe("""<script>
const P = window.parent;
const D = P.document;
function clickBtn(txt, exact) {
    const btns = Array.from(D.querySelectorAll('button'));
    const b = btns.find(el => {
        const t = (el.innerText || '').trim();
        return exact ? t === txt : t.includes(txt);
    });
    if (b) b.click();
}
if (P.__kilnKeyHandler) D.removeEventListener('keydown', P.__kilnKeyHandler, true);
P.__kilnKeyHandler = function(e) {
    if (e.ctrlKey || e.metaKey || e.altKey) return;
    const t = e.target;
    if (t && (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA' || t.isContentEditable)) return;
    const map = {
        'y': ['✓ Yes', true],  'n': ['✗ No', true],
        '1': ['FCBK', true], '2': ['CFCBK', true], '3': ['Zigzag', true], '4': ['Other', true],
        's': ['Submit', false], 'x': ['Doubt', false], 'w': ['Skip', false],
        'a': ['◀ Prev', false], 'd': ['Next ▶', false],
        'u': ['Unvalidated', false], 'r': ['Random', false],
    };
    const m = map[e.key.toLowerCase()];
    if (m) { e.preventDefault(); clickBtn(m[0], m[1]); }
};
D.addEventListener('keydown', P.__kilnKeyHandler, true);
</script>""", height=1)

# =============================================================================
# SIDEBAR: model note first, then progress & shortcuts
# =============================================================================
with st.sidebar:
    st.markdown(f"**Validator:** {st.session_state.validator}")
    st.markdown("---")

    st.markdown("#### 🤖 Model Note")
    if model_note:
        st.info(model_note)
    else:
        st.caption("No model note for this location.")

    st.markdown("#### ⌨️ Shortcuts")
    st.markdown(
        "<kbd>Y</kbd>/<kbd>N</kbd> present · <kbd>1</kbd>–<kbd>4</kbd> type<br>"
        "<kbd>S</kbd> submit · <kbd>X</kbd> doubt · <kbd>W</kbd> skip<br>"
        "<kbd>A</kbd>/<kbd>D</kbd> prev/next · <kbd>U</kbd> unvalidated · <kbd>R</kbd> random",
        unsafe_allow_html=True)

    if pending:
        st.markdown("---")
        st.markdown("#### ✏️ Recent submits")
        st.caption(f"Saved, but kept in this queue for corrections. "
                   f"The oldest moves on after {REVIEW_WINDOW - 1} newer submits.")
        for p in reversed(pending):
            if p not in locs:
                continue
            flag = " ⚠" if validated.get(p, {}).get('needs_expert_review', False) else ""
            if st.button(f"↩ {p}{flag}", key=f"recent_{p}", width="stretch",
                         type="primary" if p == loc else "secondary"):
                st.session_state.idx = locs.index(p)
                st.rerun()

    st.markdown("---")
    st.markdown(f"#### 📊 Progress · :gray[{region}]")
    doubtful_entries = {k: v for k, v in region_validated.items() if v.get('needs_expert_review', False)}
    col1, col2 = st.columns(2)
    col1.metric("Validated", len(region_validated))
    col2.metric("Remaining", len(region_locs) - len(region_validated))
    col1, col2 = st.columns(2)
    col1.metric("⚠ Doubtful", len(doubtful_entries))
    col2.metric("✓ Confident", len(region_validated) - len(doubtful_entries))
    st.progress(len(region_validated) / len(region_locs) if region_locs else 0)
    if REGIONS[region] is not None:
        st.caption(f"Overall (all regions): {len(validated)} / {len(st.session_state.all_locations)} validated")

    st.markdown("##### By Validator")
    by_validator = {}
    for loc_v, entry in region_validated.items():
        v = entry.get('validator', 'Unknown')
        by_validator[v] = by_validator.get(v, 0) + 1
    for v, count in sorted(by_validator.items(), key=lambda x: -x[1]):
        v_doubtful = sum(1 for e in region_validated.values() if e.get('validator') == v and e.get('needs_expert_review', False))
        marker = "→ " if v == st.session_state.validator else ""
        st.markdown(f"{marker}**{v}**: {count} (⚠ {v_doubtful})")

    st.markdown("---")
    render_share_report(df, validated)
    if st.button("🔄 Refresh stats", width="stretch"):
        st.rerun()
    if validated:
        csv = pd.DataFrame.from_dict(validated, orient='index').to_csv()
        st.download_button("📥 Download CSV", csv, "validation_results.csv", "text/csv", width="stretch")

    with st.expander("📤 Restore from CSV Backup", expanded=False):
        st.caption("Upload your downloaded `validation_results.csv` to restore progress stats.")
        uploaded_backup = st.file_uploader("Upload CSV", type=["csv"], key="restore_csv_uploader", label_visibility="collapsed")
        if uploaded_backup is not None:
            if st.button("Apply & Restore Backup", type="primary", width="stretch"):
                try:
                    from restore_from_csv import parse_csv_text, merge_and_save
                    raw_text = uploaded_backup.getvalue().decode("utf-8", errors="replace")
                    entries = parse_csv_text(raw_text)
                    if entries:
                        target_paths = [OUTPUT_PATH, Path(__file__).resolve().parent / "temporal_validation_results.json"]
                        success, msg = merge_and_save(entries, target_paths=target_paths)
                        if success:
                            _load_results_cached.clear()
                            st.toast(f"✅ Restored {len(entries):,} records!", icon="✅")
                            st.success(f"Restored {len(entries):,} records! Reloading...")
                            st.rerun()
                        else:
                            st.error(msg)
                    else:
                        st.error("No valid entries could be parsed from the uploaded CSV.")
                except Exception as e:
                    st.error(f"Error restoring CSV: {e}")

# =============================================================================
# PREFETCH: warm the image cache for the next location so "Next" is instant
# =============================================================================
if 'locs' in locals() and locs and st.session_state.idx < len(locs) - 1:
    try:
        for p in find_images(locs[st.session_state.idx + 1]).values():
            load_image_bytes(p)
    except Exception:
        pass
