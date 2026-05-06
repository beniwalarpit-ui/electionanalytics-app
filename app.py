import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import geopandas as gpd

px.defaults.template = "plotly_dark"

# =========================================================
# PLOTLY CONFIG
# =========================================================

PLOT_CONFIG = {
    "scrollZoom": False,
    "displaylogo": False,
    "modeBarButtonsToRemove": [
        "zoom",
        "pan",
        "select",
        "lasso2d",
        "zoomIn",
        "zoomOut",
        "autoScale",
        "resetScale"
    ]
}

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    layout="wide",
    page_title="State Elections 2026 Analytics"
)

# =========================================================
# CSS / SPACE OPTIMIZATION
# =========================================================
st.markdown("""
<style>

/* overall page */
.block-container {
    padding-top: 0.8rem;
    padding-bottom: 0rem;
    padding-left: 1rem;
    padding-right: 1rem;
}

/* remove huge gaps */
.element-container {
    margin-bottom: 0rem !important;
}

/* headings */
h1, h2, h3 {
    margin-top: 0rem !important;
    margin-bottom: 0rem !important;
    padding-bottom: 0rem !important;
}

/* plot containers */
.js-plotly-plot,
.plotly,
.stPlotlyChart {
    background: transparent !important;
    padding: 0 !important;
    margin: 0 !important;
}

/* chart spacing */
div[data-testid="stPlotlyChart"] {
    padding: 0 !important;
    margin: 0 !important;
}

/* metric cards */
[data-testid="metric-container"] {
    background-color: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.05);
    padding: 0.4rem 0.7rem;
    border-radius: 10px;
}

/* sidebar */
section[data-testid="stSidebar"] {
    width: 250px !important;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# TITLE
# =========================================================
st.markdown("# 🇮🇳 State Elections 2026 Analytics")

# =========================================================
# LOAD DATA
# =========================================================
@st.cache_data
def load_data():
    return pd.read_csv(
    "2001_2026_5_States_AC_Data.csv"
    )
   
# =========================================================
# CLEAN
# =========================================================
def clean_data(df):

    df.columns = df.columns.str.strip().str.lower()

    df['state'] = df['state'].astype(str).str.strip().str.title()
    df['party'] = df['party'].astype(str).str.strip().str.upper()
    df['ac_name'] = df['ac_name'].astype(str).str.strip().str.title()

    for col in ['votes','electors','pollers','margin']:

        if col in df.columns:

            df[col] = pd.to_numeric(
                df[col].astype(str).str.replace(',', ''),
                errors='coerce'
            )

    for col in ['votes_pct','poll_pct','margin_pct']:

        if col in df.columns:

            df[col] = pd.to_numeric(
                df[col].astype(str).str.replace('%', ''),
                errors='coerce'
            )

    return df

df = clean_data(load_data())


# =========================================================
# MANUAL 2026 TURNOUT OVERRIDE
# =========================================================

turnout_2026 = {

    "West-Bengal": 92.47,
    "Assam": 85.38,
    "Kerala": 78.03,
    "Puducherry": 89.83,
    "Tamil-Nadu": 85.05
}

for state_name, turnout in turnout_2026.items():

    mask = (
        (df["year"] == 2026) &
        (df["state"] == state_name)
    )

    df.loc[mask, "poll_pct"] = turnout

# =========================================================
# REMOVE FULL DUPLICATE ROWS
# =========================================================

initial_rows = len(df)

df = df.drop_duplicates().copy()

removed_rows = initial_rows - len(df)

print(f"Removed {removed_rows} fully duplicate rows")

# =========================================================
# FILTERS
# =========================================================
st.sidebar.markdown("## Filters")

state_options = sorted(df['state'].dropna().unique())

default_state_index = (
    state_options.index("Tamil-Nadu")
    if "Tamil-Nadu" in state_options
    else 0
)

state = st.sidebar.selectbox(
    "State",
    state_options,
    index=default_state_index
)

year_options = sorted(
    df[df['state'] == state]['year'].dropna().unique()
)

default_year_index = (
    year_options.index(2026)
    if 2026 in year_options
    else len(year_options) - 1
)

year = st.sidebar.selectbox(
    "Year",
    year_options,
    index=default_year_index
)

df_filtered = df[
    (df['state'] == state) &
    (df['year'] == year)
]

# =========================================================
# WINNERS
# =========================================================
winners = df_filtered[
    df_filtered['candidate_rank'] == 1
].copy()

winners['ac_no'] = pd.to_numeric(
    winners['ac_no'],
    errors='coerce'
)

winners = winners.drop_duplicates(subset=['ac_no'])

# =========================================================
# PARTY SHORT
# =========================================================
party_alias = {

    # NATIONAL
    "BHARATIYA JANTA PARTY": "BJP",
    "BHARATIYA JANATA PARTY": "BJP",
    "INDIAN NATIONAL CONGRESS": "INC",
    "COMMUNIST PARTY OF INDIA": "CPI",
    "COMMUNIST PARTY OF INDIA (MARXIST)": "CPM",
    "NATIONALIST CONGRESS PARTY": "NCP",
    "SAMAJWADI PARTY": "SP",
    "RASHTRIYA JANATA DAL": "RJD",
    "JANATA DAL (SECULAR)": "JDS",
    "LOKTANTRIK JANTA DAL": "LJD",

    # TAMIL NADU
    "DRAVIDA MUNETRA KAZHAGAM": "DMK",
    "DRAVIDA MUNNETRA KAZHAGAM":"DMK",
    "ALL INDIA ANNA DRAVIDA MUNNETRA KAZHAGAM": "AIADMK",
    "PATTALI MAKKAL KATCHI": "PMK",
    "DESIYA MURPOKKU DRAVIDA KAZHAGAM": "DMDK",
    "VIDUTHALAI CHIRUTHAIGAL KATCHI": "VCK",
    "MARUMALARCHI DRAVIDA MUNNETRA KAZHAGAM": "MDMK",
    "TAMIL MAANILA CONGRESS (MOOPANAR)": "TMC",
    "MANITHANEYA MAKKAL KATCHI": "MMK",
    "PUTHIYA TAMILAGAM": "PT",
    "M.G.R.ANNA D.M.KAZHAGAM": "MGR-ADMK",
    "TAMILAGA VETTRI KAZHAGAM":"TVK",
    "AMMA MAKKAL MUNNETTRA KAZAGAM":"AMMK",

    # WEST BENGAL
    "ALL INDIA TRINAMOOL CONGRESS": "AITC",
    "ALL INDIA FORWARD BLOC": "AIFB",
    "REVOLUTIONARY SOCIALIST PARTY": "RSP",
    "WEST BENGAL SOCIALIST PARTY": "WBSP",
    "GORKHA JANMUKTI MORCHA": "GJM",
    "GORKHA NATIONAL LIBERATION FRONT": "GNLF",
    "SOCIALIST UNITY CENTRE OF INDIA (COMMUNIST)": "SUCI(C)",
    "REVOLUTIONARY MARXIST PARTY OF INDIA": "RMPI",
    "AAM JANATA UNNAYAN PARTY": "AJUP",
    "ALL INDIA SECULAR FRONT": "AISF",

    # ASSAM / NORTH EAST
    "ASOM GANA PARISAD": "AGP",
    "ASOM GANA PARISHAD": "AGP",
    "ASOM GANA PARISHAD PRAGTISHEEL": "AGP-P",
    "ALL INDIA UNITED DEMOCRATIC FRONT": "AIUDF",
    "ASSAM UNITED DEMOCRATIC FRONT": "AUDF",
    "BODOLAND PEOPLES FRONT": "BPF",
    "BODALAND PEOPLES FRONT": "BPF",
    "UNITED PEOPLES PARTY LIBERAL": "UPPL",
    "AUTONOMOUS STATE DEMAND COMMITTEE": "ASDC",
    "AUTONOMOUS STATE DEMAND COMMITTEE (UNITED)": "ASDC(U)",
    "LOKO SANMILON": "LS",
    "JHARKHAND PARTY (NOREN)": "JPN",

    # KERALA
    "INDIAN UNION MUSLIM LEAGUE": "IUML",
    "MUSLIM LEAGUE KERALA STATE COMMITTEE": "MLKSC",
    "KERALA CONGRESS": "KC",
    "KERALA CONGRESS(M)": "KC(M)",
    "KERALA CONGRESS (B)": "KC(B)",
    "KERALA CONGRESS (JACOB)": "KC(J)",
    "KERALA CONGRESS SECULAR": "KC(S)",
    "JANADHIPATHIYA KERALA CONGRESS": "JKC",
    "COMMUNIST MARXIST PARTY KERALA STATE COMMITTEE": "CMPKSC",
    "KERALA REVOLUTIONARY SOCIALIST PARTY(BABY JOHN)": "KRSP(BJ)",
    "REVOLUTIONARY SOCIALIST PARTY OF KERALA (BOLSHEVIK)": "RSP(B)",
    "JANADHIPATHIYA SAMREKSHNA SAMITI": "JSS",
    "CONGRESS (SECULAR)": "CS",
    "DEMOCRATIC INDIRA CONGRESS (KARUNAKARAN)": "DIC(K)",

    # PUDUCHERRY
    "ALL INDIA N.R. CONGRESS": "AINRC",
    "PUDHUCHERRY MAKKAL CONGRESS": "PMC",
    "PUDHUCHERRY MUNNETRA CONGRESS": "PUMC",
    "LATCHIYA JANANAYAKA KATCHI (LJK)":"LJK",
    "NEYAM MAKKAL KAZHAGAM":"NMK",

    # OTHER
    "NATIONAL SECULAR CONFERENCE": "NSC",
    "SOCIALIST JANTA (DEMOCRATIC)": "SJD",
    "SAMATA PARTY": "SAP",
    "INDIAN NATIONAL LEAGUE": "INL",
    "RASHTRIYA SECULAR MAJLIS PARTY": "RSMP",
    "DEMOCRATIC SOCIALIST PARTY (PRABODH CHANDRA)": "DSP",

    # INDEPENDENT
    "INDEPENDENT": "IND"
}

# =========================================================
# PARTY SHORT FOR FULL DATASET
# =========================================================

df['party_short'] = (
    df['party']
    .map(party_alias)
    .fillna(df['party'])
)

winners['party_short'] = (
    winners['party']
    .map(party_alias)
    .fillna(winners['party'])
)

df_filtered['party_short'] = (
    df_filtered['party']
    .map(party_alias)
    .fillna(df_filtered['party'])
)

# =========================================================
# PARTY COLORS
# =========================================================

party_colors = {

    # =====================================================
    # NATIONAL
    # =====================================================

    "BJP": "#FF9933",          # saffron
    "INC": "#3498DB",          # congress blue
    "CPI": "#E53935",          # communist red
    "CPM": "#8B0000",          # deep marxist red
    "NCP": "#00B894",          # green-blue
    "SP": "#E74C3C",           # socialist red
    "RJD": "#2ECC71",          # green
    "JDS": "#27AE60",          # karnataka green
    "LJD": "#16A085",

    # =====================================================
    # TAMIL NADU
    # =====================================================

    "DMK": "#D71920",          # rising sun red
    "AIADMK": "#138808",       # tamil green
    "PMK": "#F39C12",          # yellow-orange
    "DMDK": "#7F8C8D",         # grey
    "VCK": "#2980B9",          # blue
    "MDMK": "#C0392B",         # dark red
    "TMC": "#1ABC9C",          # teal
    "MMK": "#16A085",          # green-teal
    "PT": "#8E44AD",           # purple
    "MGR-ADMK": "#2ECC71",
    "TVK":"#CCC42E",

    # =====================================================
    # WEST BENGAL
    # =====================================================

    "AITC": "#2ECC71",         # trinamool grass green
    "AIFB": "#B03A2E",         # left red
    "RSP": "#922B21",          # socialist dark red
    "WBSP": "#884EA0",         # purple
    "GJM": "#F1C40F",          # hill yellow
    "GNLF": "#D4AC0D",
    "SUCI(C)": "#E74C3C",
    "RMPI": "#7B241C",

    # =====================================================
    # ASSAM / NORTH EAST
    # =====================================================

    "AGP": "#FFD700",          # assamese yellow
    "AGP-P": "#F4D03F",
    "AIUDF": "#27AE60",        # muslim league style green
    "AUDF": "#239B56",
    "BPF": "#8E44AD",          # bodo purple
    "UPPL": "#AF7AC5",
    "ASDC": "#5DADE2",         # tribal blue
    "ASDC(U)": "#2E86C1",
    "LS": "#52BE80",
    "JPN": "#A569BD",

    # =====================================================
    # KERALA
    # =====================================================

    "IUML": "#2ECC71",         # league green
    "MLKSC": "#27AE60",
    "KC": "#A04000",           # kerala congress earthy brown
    "KC(M)": "#BA4A00",
    "KC(B)": "#CA6F1E",
    "KC(J)": "#DC7633",
    "KC(S)": "#AF601A",
    "JKC": "#873600",

    "CMPKSC": "#C0392B",
    "KRSP(BJ)": "#922B21",
    "RSP(B)": "#7B241C",

    "JSS": "#5B2C6F",
    "CS": "#5DADE2",
    "DIC(K)": "#2874A6",

    # =====================================================
    # PUDUCHERRY
    # =====================================================

    "AINRC": "#34495E",        # dark blue-grey
    "PMC": "#117A65",
    "PUMC": "#148F77",

    # =====================================================
    # OTHER SMALL PARTIES
    # =====================================================

    "NSC": "#566573",
    "SJD": "#AF601A",
    "SAP": "#7D6608",
    "INL": "#1E8449",
    "RSMP": "#7D3C98",
    "DSP": "#CD6155",

    # =====================================================
    # INDEPENDENTS / FALLBACK
    # =====================================================

    "IND": "#95A5A6",

    # fallback for unseen parties
    "OTHERS": "#7F8C8D"
}

# =========================================================
# FEATURE ENGINEERING
# =========================================================
df_filtered['vote_share_frac'] = (
    df_filtered['votes_pct'] / 100
)

enp_df = (
    df_filtered
    .groupby('ac_name')['vote_share_frac']
    .apply(lambda x: 1/(x**2).sum())
    .reset_index(name='ENP')
)

hhi_df = (
    df_filtered
    .groupby('ac_name')['vote_share_frac']
    .apply(lambda x: (x**2).sum())
    .reset_index(name='HHI')
)

winners = winners.merge(enp_df, on='ac_name', how='left')
winners = winners.merge(hhi_df, on='ac_name', how='left')

winners['margin_ratio'] = (
    winners['margin'] / winners['votes']
)

# =========================================================
# TRUE VOTE GAP + TRUE MARGIN %
# =========================================================

top2 = df_filtered.copy()

# ---------------------------------------------------------
# CLEAN RANK
# ---------------------------------------------------------

top2['candidate_rank'] = pd.to_numeric(
    top2['candidate_rank'],
    errors='coerce'
)

# ---------------------------------------------------------
# KEEP TOP 2
# ---------------------------------------------------------

top2 = top2[
    top2['candidate_rank'] <= 2
].copy()

# ---------------------------------------------------------
# CLEAN NUMERIC FIELDS
# ---------------------------------------------------------

top2['votes'] = pd.to_numeric(
    top2['votes'],
    errors='coerce'
)

# ---------------------------------------------------------
# SORT
# ---------------------------------------------------------

top2 = top2.sort_values(
    ['ac_no', 'candidate_rank']
)

# =========================================================
# CONSTITUENCY METRICS
# =========================================================

metrics = []

for ac_no, grp in top2.groupby('ac_no'):

    grp = grp.sort_values('candidate_rank')

    if len(grp) < 2:
        continue

    winner_votes = grp.iloc[0]['votes']
    runner_votes = grp.iloc[1]['votes']

    total_votes = grp['votes'].sum()

    vote_gap = winner_votes - runner_votes

    # -----------------------------------------------------
    # TRUE ELECTORAL MARGIN %
    # -----------------------------------------------------

    margin_pct = (
        vote_gap / total_votes
    ) * 100 if total_votes > 0 else None

    metrics.append({

        'ac_no': ac_no,

        'vote_gap': vote_gap,

        'margin_pct_true': margin_pct
    })

# =========================================================
# METRICS DF
# =========================================================

metrics_df = pd.DataFrame(metrics)

# =========================================================
# MERGE INTO WINNERS
# =========================================================

winners = winners.merge(

    metrics_df,

    on='ac_no',

    how='left'
)

# =========================================================
# OVERWRITE BAD IMPORTED VALUES
# =========================================================

winners['margin_pct'] = winners['margin_pct_true']

# =========================================================
# OVERVIEW KPI
# =========================================================

st.markdown("## Overview")

# ---------------------------------------------------------
# LEADING PARTY
# ---------------------------------------------------------

party_counts = winners["party_short"].value_counts()

leading_party = party_counts.idxmax()

leading_party_seats = party_counts.max()

# ---------------------------------------------------------
# STRONGHOLDS
# ---------------------------------------------------------

stronghold_seats = len(
    winners[winners["margin_pct"] >= 15]
)

# ---------------------------------------------------------
# CLOSE CONTESTS
# ---------------------------------------------------------

closest_contests = len(
    winners[winners["margin_pct"] <= 3]
)

# ---------------------------------------------------------
# SWING SEATS
# ---------------------------------------------------------

years_sorted = sorted(
    df[df["state"] == state]["year"].dropna().unique()
)

swing_seats = 0

if len(years_sorted) > 1:

    current_index = years_sorted.index(year)

    if current_index > 0:

        prev_year = years_sorted[current_index - 1]

        prev_winners = df[
            (df["state"] == state) &
            (df["year"] == prev_year) &
            (df["candidate_rank"] == 1)
        ][["ac_name", "party_short"]]

        prev_winners.columns = [
            "ac_name",
            "prev_party"
        ]

        swing_df = winners.merge(
            prev_winners,
            on="ac_name",
            how="left"
        )

        swing_seats = len(
            swing_df[
                swing_df["party_short"] !=
                swing_df["prev_party"]
            ]
        )

# ---------------------------------------------------------
# KPI DISPLAY
# ---------------------------------------------------------

c1,c2,c3,c4,c5,c6 = st.columns(6)

c1.metric(
    "Seats",
    len(winners)
)

c2.metric(
    "Voter Turnout",
    f"{round(winners['poll_pct'].mean(),1)}%"
)

c3.metric(
    "Leading Party",
    f"{leading_party} ({leading_party_seats})"
)

c4.metric(
    "Stronghold Seats",
    stronghold_seats
)

c5.metric(
    "Closest Contests",
    closest_contests
)

c6.metric(
    "Swing Seats",
    swing_seats
)

# =========================================================
# MAP SECTION
# =========================================================
st.markdown("## 🗺️ Constituency Map")

state_map_names = {
    "tamil-nadu": "TAMIL NADU",
    "assam": "ASSAM",
    "kerala": "KERALA",
    "west-bengal": "WEST BENGAL",
    "puducherry": "PUDUCHERRY"
}

shapefile_state = state_map_names[state.lower()]

india_gdf = gpd.read_file(
    "India_AC.shp"
)

state_gdf = india_gdf[
    india_gdf["ST_NAME"].str.upper() == shapefile_state
].copy()

state_gdf["AC_NO"] = pd.to_numeric(
    state_gdf["AC_NO"],
    errors="coerce"
)

state_gdf = state_gdf.merge(
    winners[["ac_no", "party_short"]],
    left_on="AC_NO",
    right_on="ac_no",
    how="left"
)

state_gdf["party_short"] = (
    state_gdf["party_short"]
    .fillna("OTHERS")
)

# =========================================================
# PARTY NUMBERS
# =========================================================
unique_parties = sorted(
    state_gdf["party_short"].unique()
)

party_to_num = {
    p:i for i,p in enumerate(unique_parties)
}

state_gdf["party_num"] = (
    state_gdf["party_short"]
    .map(party_to_num)
)

# =========================================================
# COLOR SCALE
# =========================================================
colorscale = []

for p,i in party_to_num.items():

    val = (
        i/(len(party_to_num)-1)
        if len(party_to_num)>1
        else 0
    )

    colorscale.append([
        val,
        party_colors.get(p, "#888888")
    ])

    colorscale.append([
        val,
        party_colors.get(p, "#888888")
    ])

# =========================================================
# GEOJSON
# =========================================================
state_geojson = json.loads(
    state_gdf.to_json()
)

# =========================================================
# LAYOUT
# =========================================================
col_map, col_legend = st.columns(
    [9,2],
    gap="small"
)

# =========================================================
# PUDUCHERRY SPECIAL
# =========================================================
if state.lower() == "puducherry":

    # -----------------------------------------------------
    # REGION SPLITS USING AC NAMES
    # -----------------------------------------------------

    puducherry_names = [
        "Mannadipet",
        "Thirubuvanai",
        "Oussudu",
        "Mangalam",
        "Villianur",
        "Ozhukarai",
        "Kadirgamam",
        "Indira Nagar",
        "Thattanchavady",
        "Kamaraj Nagar",
        "Lawspet",
        "Kalapet",
        "Muthialpet",
        "Raj Bhavan",
        "Mudaliarpet",
        "Ariyankuppam",
        "Embalam",
        "Nettapakkam",
        "Bahour",
        "Nellithope",
        "Orleampeth",
        "Dubrayapet",
        "Tirunallar"
    ]

    karaikal_names = [
        "Karaikal North",
        "Karaikal South",
        "Nedungadu",
        "Neravy T.R. Pattinam",
        "Kottucherry"
    ]

    mahe_names = [
        "Mahe"
    ]

    yanam_names = [
        "Yanam"
    ]

    # -----------------------------------------------------
    # FILTER REGIONS
    # -----------------------------------------------------

    puducherry_region = state_gdf[
        state_gdf["AC_NAME"].isin(puducherry_names)
    ]

    karaikal_region = state_gdf[
        state_gdf["AC_NAME"].isin(karaikal_names)
    ]

    mahe_region = state_gdf[
        state_gdf["AC_NAME"].isin(mahe_names)
    ]

    yanam_region = state_gdf[
        state_gdf["AC_NAME"].isin(yanam_names)
    ]

    regions = {
        "Puducherry": puducherry_region,
        "Karaikal": karaikal_region,
        "Mahe": mahe_region,
        "Yanam": yanam_region
    }

    with col_map:

        row1col1, row1col2 = st.columns(2)
        row2col1, row2col2 = st.columns(2)

        cols = [
            row1col1,
            row1col2,
            row2col1,
            row2col2
        ]

        for (region_name, region_gdf), col in zip(regions.items(), cols):

            if len(region_gdf) == 0:
                continue

            region_geojson = json.loads(
                region_gdf.to_json()
            )

            fig_region = go.Figure(

                go.Choropleth(

                    geojson=region_geojson,

                    locations=region_gdf["AC_NO"],

                    z=region_gdf["party_num"],

                    featureidkey="properties.AC_NO",

                    text=region_gdf["party_short"],

                    customdata=region_gdf["AC_NAME"],

                    colorscale=colorscale,

                    showscale=False,

                    marker=dict(
                        line=dict(
                            color="white",
                            width=0.4
                        )
                    ),

                    hovertemplate=
                        "<b>%{customdata}</b><br>" +
                        "%{text}<extra></extra>"
                )
            )

            # -------------------------------------------------
            # STRONGER ZOOM FOR MAIN PUDUCHERRY
            # -------------------------------------------------

            if region_name == "Puducherry":

                fig_region.update_geos(
                    fitbounds="locations",
                    visible=False,
                    projection_scale=9,
                    center={
                        "lat": 11.93,
                        "lon": 79.80
                    },
                    bgcolor="rgba(0,0,0,0)"
                )

            else:

                fig_region.update_geos(
                    fitbounds="locations",
                    visible=False,
                    bgcolor="rgba(0,0,0,0)"
                )

            fig_region.update_layout(
                title=region_name,
                height=340,
                autosize=True,
                margin=dict(l=0,r=0,t=30,b=0),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)"
            )

            with col:
                st.plotly_chart(
                fig_region,
                use_container_width=True,
                config=PLOT_CONFIG
            )

# =========================================================
# NORMAL STATES
# =========================================================
else:

    fig = go.Figure(

        go.Choropleth(

            geojson=state_geojson,

            locations=state_gdf["AC_NO"],

            z=state_gdf["party_num"],

            featureidkey="properties.AC_NO",

            text=state_gdf["party_short"],

            customdata=state_gdf["AC_NAME"],

            colorscale=colorscale,

            showscale=False,

            marker=dict(
                line=dict(
                    color="white",
                    width=0.15
                )
            ),

            hovertemplate=
                "<b>%{customdata}</b><br>" +
                "%{text}<extra></extra>"
        )
    )

    fig.update_geos(
        fitbounds="locations",
        visible=False,
        bgcolor="rgba(0,0,0,0)"
    )

    fig.update_layout(
        height=580,
        autosize=True,
        margin=dict(l=0,r=0,t=0,b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )

    with col_map:
        st.plotly_chart(
            fig,
            use_container_width=True,
            config=PLOT_CONFIG
        )

# =========================================================
# PARTY SUMMARY
# =========================================================
with col_legend:

    st.markdown("### 🏛️ Party Summary")

    pc = winners["party_short"].value_counts()

    for p,s in pc.items():

        c1,c2 = st.columns([4,1])

        with c1:

            st.markdown(
                f"""
                <div style='display:flex;gap:6px;align-items:center;'>
                    <div style='width:10px;height:10px;
                    background:{party_colors.get(p, "#888")};
                    border-radius:2px;'></div>
                    {p}
                </div>
                """,
                unsafe_allow_html=True
            )

        with c2:

            st.markdown(
                f"<div style='text-align:right;font-weight:600'>{int(s)}</div>",
                unsafe_allow_html=True
            )

# =========================================================
# PARTY PERFORMANCE
# =========================================================
st.markdown("## Party Performance")

pie1, pie2 = st.columns(2)

# =========================================================
# SEAT SHARE
# =========================================================
seat_share = (
    winners["party_short"]
    .value_counts()
    .reset_index()
)

seat_share.columns = ["party", "seats"]

fig_seats = px.pie(
    seat_share,
    names="party",
    values="seats",
    color="party",
    color_discrete_map=party_colors,
    hole=0.45
)

fig_seats.update_traces(

    textinfo='value',

    textposition='inside',

    textfont_size=14,

    insidetextorientation='horizontal',

    hovertemplate=
    "<b>%{label}</b><br>" +
    "Seats: %{value}<br>" +
    "Share: %{percent}<extra></extra>"
)

fig_seats.update_layout(

    title="Seat Share",

    height=420,

    margin=dict(l=20,r=20,t=50,b=20),

    uniformtext_minsize=12,

    uniformtext_mode='hide',

    showlegend=True
)

with pie1:
    st.plotly_chart(
        fig_seats,
        use_container_width=True
    )

# =========================================================
# VOTE SHARE
# =========================================================
vote_share = (
    df_filtered
    .groupby("party_short")["votes"]
    .sum()
    .reset_index()
)

vote_share.columns = ["party", "votes"]

fig_votes = px.pie(
    vote_share,
    names="party",
    values="votes",
    color="party",
    color_discrete_map=party_colors,
    hole=0.45
)

fig_votes.update_traces(

    texttemplate=
        "%{percent:.0%}",

    textposition='inside',

    textfont_size=14,

    insidetextorientation='horizontal',

    hovertemplate=
    "<b>%{label}</b><br>" +
    "Votes: %{value:,}<br>" +
    "Vote Share: %{percent}<extra></extra>"
)

fig_votes.update_layout(

    title="Vote Share",

    height=420,

    margin=dict(l=20,r=20,t=50,b=20),

    uniformtext_minsize=12,

    uniformtext_mode='hide',

    showlegend=True
)

with pie2:
    st.plotly_chart(
        fig_votes,
        use_container_width=True
    )

# =========================================================
# SANKEY: SEAT TRANSITIONS
# =========================================================

st.markdown("## 🔄 Seat Transition Flow")

years_sorted = sorted(
    df[df["state"] == state]["year"].dropna().unique()
)

current_index = years_sorted.index(year)

if current_index > 0:

    prev_year = years_sorted[current_index - 1]

    # -----------------------------------------------------
    # PREVIOUS WINNERS
    # -----------------------------------------------------

    prev_winners = df[
        (df["state"] == state) &
        (df["year"] == prev_year) &
        (df["candidate_rank"] == 1)
    ][["ac_name", "party_short"]].copy()

    prev_winners.columns = [
        "ac_name",
        "prev_party"
    ]

    # -----------------------------------------------------
    # CURRENT WINNERS
    # -----------------------------------------------------

    curr_winners = winners[
        ["ac_name", "party_short"]
    ].copy()

    curr_winners.columns = [
        "ac_name",
        "curr_party"
    ]

    # -----------------------------------------------------
    # MERGE
    # -----------------------------------------------------

    sankey_df = prev_winners.merge(
        curr_winners,
        on="ac_name",
        how="inner"
    )

    # -----------------------------------------------------
    # TRANSITION COUNTS
    # -----------------------------------------------------

    transition_counts = (
        sankey_df
        .groupby(
            ["prev_party", "curr_party"]
        )
        .size()
        .reset_index(name="seats")
        .sort_values("seats", ascending=False)
    )

    # OPTIONAL:
    # Remove tiny 1-seat flows for cleaner chart

    transition_counts = transition_counts[
        transition_counts["seats"] >= 2
    ]
    # -----------------------------------------------------
    # PARTY TOTALS
    # -----------------------------------------------------

    prev_totals = (
        prev_winners["prev_party"]
        .value_counts()
        .to_dict()
    )

    curr_totals = (
        curr_winners["curr_party"]
        .value_counts()
        .to_dict()
    )

    # -----------------------------------------------------
    # CREATE SEPARATE LEFT / RIGHT NODES
    # -----------------------------------------------------

    left_nodes = [

        f"{prev_totals.get(p,0)}   {p} ({prev_year})"

        for p in transition_counts["prev_party"].unique()
    ]

    right_nodes = [

        f"{p} ({year})   {curr_totals.get(p,0)}"

        for p in transition_counts["curr_party"].unique()
    ]

    all_nodes = left_nodes + right_nodes

    node_map = {
        node:i for i,node in enumerate(all_nodes)
    }
    # -----------------------------------------------------
    # LINKS
    # -----------------------------------------------------

    sources = transition_counts["prev_party"].apply(
        lambda x: node_map[
            f"{prev_totals.get(x,0)}   {x} ({prev_year})"
        ]
    )

    targets = transition_counts["curr_party"].apply(
        lambda x: node_map[
            f"{x} ({year})   {curr_totals.get(x,0)}"
        ]
    )

    values = transition_counts["seats"]

    # -----------------------------------------------------
    # NODE COLORS
    # -----------------------------------------------------

    node_colors = []

    for node in all_nodes:

        party = node.split(" (")[0]

        node_colors.append(
            party_colors.get(party, "#7f8c8d")
        )

    # -----------------------------------------------------
    # LINK COLORS
    # Use source party color with transparency
    # -----------------------------------------------------

    link_colors = []

    for p in transition_counts["prev_party"]:

        hex_color = party_colors.get(
            p,
            "#7f8c8d"
        )

        hex_color = hex_color.lstrip("#")

        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)

        rgba = f"rgba({r},{g},{b},0.35)"

        link_colors.append(rgba)

        #-----------------------------------------------------
        # CUSTOM HOVER TEXT
        # -----------------------------------------------------

        hover_text = []

        for _, row in transition_counts.iterrows():

            prev_party = row["prev_party"]
            curr_party = row["curr_party"]
            seats = row["seats"]

            # SAME PARTY RETAINED
            if prev_party == curr_party:

                txt = (
                    f"{curr_party} retained "
                    f"{seats} seats"
                )

            # PARTY SWITCH
            else:

                txt = (
                    f"{curr_party} gained "
                    f"{seats} seats from "
                    f"{prev_party}"
                )

            hover_text.append(txt)
            

    # -----------------------------------------------------
    # FIGURE
    # -----------------------------------------------------

    fig_sankey = go.Figure(

        go.Sankey(

            arrangement="fixed",

            node=dict(

                pad=22,
                thickness=20,

                line=dict(
                    color="rgba(255,255,255,0.15)",
                    width=0.5
                ),

                label=all_nodes,

                color=node_colors
            ),

            link=dict(

                source=sources,

                target=targets,

                value=values,

                color=link_colors,
                customdata=hover_text,
                hovertemplate="%{customdata}<extra></extra>"
            )
        )
    )

    fig_sankey.update_layout(

        title=f"Seat Flow: {prev_year} → {year}",

        font_size=13,

        height=650,

        margin=dict(
            l=20,
            r=20,
            t=60,
            b=20
        )
    )

    st.plotly_chart(
        fig_sankey,
        use_container_width=True
    )

else:

    st.info(
        "No previous election year available."
    )

# =========================================================
# STRONGHOLD SEATS
# =========================================================
st.markdown("## 🛡️ Top Stronghold Seats")

top_strongholds = (
    winners
    .sort_values('margin_pct', ascending=False)
    .head(15)
)

fig_stronghold = px.bar(
    top_strongholds,
    x='margin_pct',
    y='ac_name',
    orientation='h',
    color='party_short',
    color_discrete_map=party_colors
)

fig_stronghold.update_layout(
    height=500,
    xaxis_title="Victory Margin (%)",
    yaxis_title="",
    legend_title_text='Party',
    yaxis={'categoryorder':'total ascending'}
)

st.plotly_chart(
    fig_stronghold,
    use_container_width=True
)

# =========================================================
# CLOSEST SEATS
# =========================================================
st.markdown("## 🔥 Closest Seats")

top_close = winners.sort_values(
    'vote_gap'
).head(15)

fig_close = px.bar(
    top_close,
    x='vote_gap',
    y='ac_name',
    orientation='h',
    color='party_short',
    color_discrete_map=party_colors
)

fig_close.update_layout(
    height=500,
    xaxis_title="Vote Gap",
    yaxis_title="",
    legend_title_text='Party',
    yaxis={'categoryorder':'total ascending'}
)

st.plotly_chart(
    fig_close,
    use_container_width=True
)

# =========================================================
# SWING SEATS
# =========================================================
st.markdown("## 🔄 Top Swing Seats")

if current_index > 0:

    swing_chart_df = swing_df[
        swing_df["party_short"] != swing_df["prev_party"]
    ].copy()

    swing_chart_df = swing_chart_df.sort_values(
        "margin_pct"
    ).head(15)

    fig_swing = px.bar(
        swing_chart_df,
        x='margin_pct',
        y='ac_name',
        orientation='h',
        color='party_short',
        color_discrete_map=party_colors,
        hover_data=['prev_party']
    )

    fig_swing.update_layout(
        height=500,
        xaxis_title="Victory Margin (%)",
        yaxis_title="",
        legend_title_text='Party',
        yaxis={'categoryorder':'total ascending'}
    )

    st.plotly_chart(
        fig_swing,
        use_container_width=True
    )

else:

    st.info("No previous election year available for swing seat analysis.")



# =========================================================
# SCATTER
# =========================================================
st.markdown("## 📈 Fragmentation vs Margin")

fig5 = px.scatter(
    winners,
    x='ENP',
    y='margin',
    color='party_short',
    hover_data=['ac_name'],
    color_discrete_map=party_colors
)

fig5.update_layout(
    height=500,
    xaxis_title="Effective No. of Parties Contested",
    yaxis_title="Margin (Number of Votes)",
    legend_title_text='Party'
)

st.plotly_chart(
    fig5,
    use_container_width=True
)