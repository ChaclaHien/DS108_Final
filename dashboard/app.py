import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import warnings
from pathlib import Path
import plotly.io as pio
warnings.filterwarnings("ignore")

# Transparent background → Plotly inherits Streamlit theme font color (works in light & dark)
pio.templates["adaptive"] = go.layout.Template(
    layout=go.Layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(gridcolor="rgba(128,128,128,0.3)", linecolor="rgba(128,128,128,0.5)"),
        yaxis=dict(gridcolor="rgba(128,128,128,0.3)", linecolor="rgba(128,128,128,0.5)"),
    )
)
pio.templates.default = "plotly+adaptive"

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Vietnam Weather EDA Dashboard",
    page_icon="🌧️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1a6eb5;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1rem;
        color: #666;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #f0f6ff, #e8f0fe);
        border-radius: 12px;
        padding: 1rem 1.2rem;
        border-left: 4px solid #1a6eb5;
        margin-bottom: 0.5rem;
    }
    .insight-box {
    background: #fff8e1;
    border-left: 4px solid #f9a825;
    border-radius: 8px;
    padding: 0.8rem 1rem;
    margin: 0.5rem 0;
    font-size: 0.9rem;
    color: #222222;
    }
    .section-header {
        font-size: 1.3rem;
        font-weight: 600;
        color: #1a6eb5;
        border-bottom: 2px solid #e0e7ef;
        padding-bottom: 0.3rem;
        margin-bottom: 1rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 8px 18px;
        border-radius: 8px 8px 0 0;
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# DATA LOADING
# ─────────────────────────────────────────────
@st.cache_data
def load_data():
    BASE_DIR = Path(__file__).resolve().parent

    DATA_PATH = (
        BASE_DIR.parent
        / "data"
        / "processed"
        / "feature engineered"
        / "df_codebook_final.parquet"
    )

    df = pd.read_parquet(DATA_PATH)
    df["DATE"] = pd.to_datetime(df["DATE"])

    # year, month, day_of_year already exist in dataset — only add if missing
    if "year" not in df.columns:
        df["year"] = df["DATE"].dt.year
    if "month" not in df.columns:
        df["month"] = df["DATE"].dt.month
    if "day_of_year" not in df.columns:
        df["day_of_year"] = df["DATE"].dt.dayofyear

    # Short station name — handle NaN in NAME
    df["station_short"] = df["NAME"].apply(
        lambda x: x.replace(", VM", "").strip() if pd.notna(x) else "Unknown"
    )

    # Region — handle NaN in NAME
    north = ["NOIBAI INTERNATIONAL", "NAM DINH", "PHU LIEN", "THAI NGUYEN"]
    central = ["THANH HOA", "VINH", "DONG HOI", "PHUBAI", "QUANG NGAI"]
    def region(name):
        if pd.isna(name):
            return "Nam"  # fallback to Nam for unknown stations
        n = name.replace(", VM", "").strip()
        if any(x in n for x in north): return "Bắc"
        if any(x in n for x in central): return "Trung"
        return "Nam"
    df["region"] = df["NAME"].apply(region)

    # rain_class_label — rain_class is nullable Int64, .map handles NA → NaN
    df["rain_class_label"] = df["rain_class"].map({0: "Không mưa", 1: "Mưa thường", 2: "Mưa cực đoan"})

    df["month_name"] = df["DATE"].dt.strftime("%m/%Y")

    # Ensure target_reliable is boolean-compatible (stored as object)
    df["target_reliable"] = df["target_reliable"].astype(bool)

    return df

df = load_data()

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🎛️ Bộ lọc dữ liệu")

    # Date range
    min_date = df["DATE"].min().date()
    max_date = df["DATE"].max().date()
    date_range = st.date_input("📅 Khoảng thời gian", [min_date, max_date],
                               min_value=min_date, max_value=max_date)

    # Stations
    all_stations = sorted(df["station_short"].unique())
    selected_stations = st.multiselect("🏢 Trạm khí tượng", all_stations, default=all_stations,
                                        help="Chọn một hoặc nhiều trạm")

    # Region
    regions = ["Tất cả"] + sorted(df["region"].unique())
    selected_region = st.selectbox("🗺️ Vùng khí hậu", regions)

    # Year
    years = sorted(df["year"].unique())
    selected_years = st.multiselect("📆 Năm", years, default=years)

    # ENSO
    enso_opts = ["Tất cả"] + sorted(df["enso_phase"].unique())
    selected_enso = st.selectbox("🌊 Pha ENSO", enso_opts)

    # target_reliable only
    reliable_only = st.checkbox("✅ Chỉ target_reliable", value=True,
                                 help="Lọc chỉ các dòng có target_reliable=True")

    st.markdown("---")
    st.markdown("**📊 Dataset Info**")
    st.caption(f"• {len(df):,} observations\n• {df['station_short'].nunique()} stations\n• 2015–2024")

# ─────────────────────────────────────────────
# APPLY FILTERS
# ─────────────────────────────────────────────
dff = df.copy()
if len(date_range) == 2:
    dff = dff[(dff["DATE"].dt.date >= date_range[0]) & (dff["DATE"].dt.date <= date_range[1])]
if selected_stations:
    dff = dff[dff["station_short"].isin(selected_stations)]
if selected_region != "Tất cả":
    dff = dff[dff["region"] == selected_region]
if selected_years:
    dff = dff[dff["year"].isin(selected_years)]
if selected_enso != "Tất cả":
    dff = dff[dff["enso_phase"] == selected_enso]
if reliable_only:
    dff = dff[dff["target_reliable"] == True]

dff_labeled = dff.dropna(subset=["rain_class"])

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
st.markdown('<p class="main-title">🌧️ Vietnam Weather ML – EDA Dashboard</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Phân tích dữ liệu khí tượng Việt Nam 2015–2024 | 15 Trạm | Pipeline ML Dự báo Mưa</p>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
# KPIs
# ─────────────────────────────────────────────
col1, col2, col3, col4, col5, col6 = st.columns(6)
total = len(dff)
rain_days = (dff["prcp_gsod_mm"] > 0.1).sum() if total > 0 else 0
extreme_days = (dff["prcp_gsod_mm"] >= 50).sum() if total > 0 else 0
avg_rain = dff["prcp_gsod_mm"].mean() if total > 0 else 0
avg_temp = dff["temperature_2m_mean"].mean() if total > 0 else 0
avg_humid = dff["relative_humidity_2m_mean"].mean() if total > 0 else 0

col1.metric("📋 Tổng quan sát", f"{total:,}")
col2.metric("🌧️ Ngày có mưa", f"{rain_days:,}", f"{rain_days/total*100:.1f}%" if total else "")
col3.metric("⛈️ Mưa cực đoan", f"{extreme_days:,}", f"{extreme_days/total*100:.1f}%" if total else "")
col4.metric("💧 Lượng mưa TB", f"{avg_rain:.1f} mm")
col5.metric("🌡️ Nhiệt độ TB", f"{avg_temp:.1f} °C")
col6.metric("💦 Độ ẩm TB", f"{avg_humid:.1f} %")

st.markdown("---")

# ─────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────
tabs = st.tabs([
    "📊 Phân phối Mưa",
    "📈 Chuỗi Thời Gian",
    "🗺️ So sánh Trạm",
    "🌡️ Tương quan Biến",
    "🌊 ENSO & Khí hậu",
    "🔬 Feature Engineering",
    "🔍 Truy vấn dữ liệu"
])

# ══════════════════════════════════════════════
# TAB 1: Phân phối Mưa
# ══════════════════════════════════════════════
with tabs[0]:
    st.markdown('<p class="section-header">📊 Phân phối Lượng mưa & Phân lớp</p>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)

    with c1:
        # Rain class donut
        if not dff_labeled.empty:
            rc_counts = dff_labeled["rain_class_label"].value_counts().reset_index()
            rc_counts.columns = ["Lớp", "Số ngày"]
            fig = px.pie(rc_counts, values="Số ngày", names="Lớp",
                         title="Phân bố nhãn Rain Class",
                         color="Lớp",
                         color_discrete_map={"Không mưa": "#90caf9", "Mưa thường": "#42a5f5", "Mưa cực đoan": "#d32f2f"},
                         hole=0.45)
            fig.update_traces(textposition="outside", textinfo="percent+label")
            fig.update_layout(height=380, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

            total_labeled = len(dff_labeled)
            n_extreme = (dff_labeled["rain_class"] == 2).sum()
            st.markdown(f'<div class="insight-box">💡 <b>Insight:</b> Mưa cực đoan (≥50mm) chiếm <b>{n_extreme/total_labeled*100:.2f}%</b> tổng số ngày có nhãn — class imbalance nghiêm trọng, cần SMOTE/class_weight.</div>', unsafe_allow_html=True)

    with c2:
        # Histogram log scale
        fig = px.histogram(dff[dff["prcp_gsod_mm"] > 0], x="prcp_gsod_mm",
                           nbins=80, color="region",
                           title="Phân phối lượng mưa (ngày mưa, log scale)",
                           labels={"prcp_gsod_mm": "Lượng mưa (mm)", "region": "Vùng"},
                           log_y=True, marginal="box")
        fig.add_vline(x=25, line_dash="dash", line_color="orange", annotation_text="25mm (rain_binary)")
        fig.add_vline(x=50, line_dash="dash", line_color="red", annotation_text="50mm (cực đoan)")
        fig.update_layout(height=380)
        st.plotly_chart(fig, use_container_width=True)

    # Monthly rain by region
    st.markdown("#### 📅 Lượng mưa trung bình theo tháng & vùng")
    monthly = dff.groupby(["month", "region"])["prcp_gsod_mm"].mean().reset_index()
    monthly.columns = ["Tháng", "Vùng", "Lượng mưa TB (mm)"]
    fig = px.bar(monthly, x="Tháng", y="Lượng mưa TB (mm)", color="Vùng",
                 barmode="group",
                 color_discrete_map={"Bắc": "#1565c0", "Trung": "#00897b", "Nam": "#f57f17"},
                 title="Phân bố mưa theo tháng và vùng khí hậu")
    fig.update_xaxes(tickvals=list(range(1,13)), ticktext=["T1","T2","T3","T4","T5","T6","T7","T8","T9","T10","T11","T12"])
    fig.update_layout(height=380)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("""
    <div class="insight-box">💡 <b>Insight mùa vụ:</b> Vùng <b>Bắc</b>: mưa tập trung T5–T9 (gió mùa Đông Nam). 
    Vùng <b>Trung</b>: mưa cực đoan T9–T12 (bão + dải hội tụ nhiệt đới). Vùng <b>Nam</b>: mưa T5–T11 (mùa Tây Nam).</div>
    """, unsafe_allow_html=True)

    # Violin plot by station
    st.markdown("#### 🎻 Phân phối lượng mưa theo trạm (violin)")
    fig = px.violin(dff[dff["prcp_gsod_mm"] > 0], x="station_short", y="prcp_gsod_mm",
                    color="region", box=True,
                    title="Violin plot lượng mưa theo trạm (chỉ ngày mưa)",
                    labels={"station_short": "Trạm", "prcp_gsod_mm": "Lượng mưa (mm)"})
    fig.update_layout(height=420, xaxis_tickangle=-30)
    st.plotly_chart(fig, use_container_width=True)

# ══════════════════════════════════════════════
# TAB 2: Chuỗi Thời Gian
# ══════════════════════════════════════════════
with tabs[1]:
    st.markdown('<p class="section-header">📈 Phân tích Chuỗi Thời Gian</p>', unsafe_allow_html=True)

    c1, c2 = st.columns([2, 1])
    with c1:
        ts_var = st.selectbox("Chọn biến:", [
            "prcp_gsod_mm", "temperature_2m_mean", "relative_humidity_2m_mean",
            "pressure_msl_mean", "cloud_cover_mean", "wind_speed_10m_mean",
            "dew_point_2m_mean", "et0_fao_evapotranspiration"
        ], format_func=lambda x: {
            "prcp_gsod_mm": "Lượng mưa GSOD (mm)",
            "temperature_2m_mean": "Nhiệt độ TB (°C)",
            "relative_humidity_2m_mean": "Độ ẩm TB (%)",
            "pressure_msl_mean": "Áp suất mực biển (hPa)",
            "cloud_cover_mean": "Mây che phủ TB (%)",
            "wind_speed_10m_mean": "Tốc độ gió TB (km/h)",
            "dew_point_2m_mean": "Điểm sương TB (°C)",
            "et0_fao_evapotranspiration": "Bốc hơi FAO (mm)"
        }.get(x, x))
    with c2:
        agg_freq = st.selectbox("Tần suất tổng hợp:", ["Tuần", "Tháng", "Quý"])
        agg_func = st.selectbox("Hàm tổng hợp:", ["Mean", "Sum", "Max"])

    # Time series
    freq_map = {"Tuần": "W", "Tháng": "ME", "Quý": "QE"}
    func_map = {"Mean": "mean", "Sum": "sum", "Max": "max"}
    
    ts_df = dff.groupby(["DATE", "station_short"])[ts_var].mean().reset_index()
    ts_pivot = ts_df.pivot(index="DATE", columns="station_short", values=ts_var)
    ts_resampled = getattr(ts_pivot.resample(freq_map[agg_freq]), func_map[agg_func])()

    fig = go.Figure()
    colors = px.colors.qualitative.Set2
    for i, col in enumerate(ts_resampled.columns):
        fig.add_trace(go.Scatter(
            x=ts_resampled.index, y=ts_resampled[col],
            name=col, mode="lines", opacity=0.8,
            line=dict(color=colors[i % len(colors)], width=1.5)
        ))
    fig.update_layout(
        title=f"{ts_var} theo {agg_freq} ({agg_func})",
        height=420, hovermode="x unified",
        xaxis_title="Thời gian", yaxis_title=ts_var,
        legend=dict(orientation="h", y=-0.2)
    )
    st.plotly_chart(fig, use_container_width=True)

    # Heatmap theo tháng-năm
    st.markdown("#### 🗓️ Heatmap Lượng mưa TB theo Tháng–Năm (tất cả trạm)")
    heat_df = dff.groupby(["year", "month"])["prcp_gsod_mm"].mean().reset_index()
    heat_pivot = heat_df.pivot(index="year", columns="month", values="prcp_gsod_mm")
    heat_pivot.columns = ["T1","T2","T3","T4","T5","T6","T7","T8","T9","T10","T11","T12"]

    fig = px.imshow(heat_pivot, color_continuous_scale="Blues",
                    title="Lượng mưa trung bình theo Tháng–Năm (mm)",
                    labels=dict(color="mm"), text_auto=".1f", aspect="auto")
    fig.update_layout(height=360)
    st.plotly_chart(fig, use_container_width=True)

    # Year over year extreme rain
    st.markdown("#### ⛈️ Số ngày mưa cực đoan theo năm & trạm")
    ext_df = dff[dff["prcp_gsod_mm"] >= 50].groupby(["year", "station_short"]).size().reset_index()
    ext_df.columns = ["Năm", "Trạm", "Số ngày cực đoan"]
    fig = px.bar(ext_df, x="Năm", y="Số ngày cực đoan", color="Trạm",
                 title="Số ngày mưa cực đoan (≥50mm) theo năm")
    fig.update_layout(height=360)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("""
    <div class="insight-box">💡 <b>Insight temporal:</b> Có thể quan sát <b>xu hướng gia tăng</b> mưa cực đoan qua các năm — cần kiểm định thống kê (Mann-Kendall test). 
    Năm La Niña thường đi kèm lượng mưa cao hơn ở miền Nam.</div>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════
# TAB 3: So sánh Trạm
# ══════════════════════════════════════════════
with tabs[2]:
    st.markdown('<p class="section-header">🗺️ So sánh Trạm & Phân tích Không gian</p>', unsafe_allow_html=True)

    # Map of stations — exclude rows with no valid NAME (station_short == "Unknown")
    dff_named = dff[dff["station_short"] != "Unknown"]
    station_stats = dff_named.groupby(["station_short", "LATITUDE", "LONGITUDE", "region"]).agg(
        avg_rain=("prcp_gsod_mm", "mean"),
        total_rain=("prcp_gsod_mm", "sum"),
        extreme_days=("prcp_gsod_mm", lambda x: (x >= 50).sum()),
        avg_temp=("temperature_2m_mean", "mean"),
        n_obs=("prcp_gsod_mm", "count")
    ).reset_index()

    fig = px.scatter_mapbox(station_stats,
                            lat="LATITUDE", lon="LONGITUDE",
                            size="avg_rain", color="region",
                            hover_name="station_short",
                            hover_data={"avg_rain": ":.1f", "extreme_days": True, "avg_temp": ":.1f", "n_obs": True},
                            color_discrete_map={"Bắc": "#1565c0", "Trung": "#00897b", "Nam": "#f57f17"},
                            zoom=4.5, mapbox_style="open-street-map",
                            title="Bản đồ 15 trạm khí tượng — kích thước = lượng mưa TB",
                            size_max=30, height=450)
    st.plotly_chart(fig, use_container_width=True)

    # Radar chart multi-var per station
    st.markdown("#### 📡 So sánh đa biến giữa các trạm (Radar Chart)")
    radar_vars = ["avg_rain", "extreme_days", "avg_temp"]
    
    # Bar comparison
    compare_df = station_stats.sort_values("avg_rain", ascending=False)
    c1, c2 = st.columns(2)
    with c1:
        fig = px.bar(compare_df, x="station_short", y="avg_rain", color="region",
                     title="Lượng mưa TB/ngày theo trạm (mm)",
                     color_discrete_map={"Bắc": "#1565c0", "Trung": "#00897b", "Nam": "#f57f17"})
        fig.update_layout(height=360, xaxis_tickangle=-30)
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        fig = px.bar(compare_df.sort_values("extreme_days", ascending=False),
                     x="station_short", y="extreme_days", color="region",
                     title="Số ngày mưa cực đoan (≥50mm) theo trạm",
                     color_discrete_map={"Bắc": "#1565c0", "Trung": "#00897b", "Nam": "#f57f17"})
        fig.update_layout(height=360, xaxis_tickangle=-30)
        st.plotly_chart(fig, use_container_width=True)

    # Box plot cross-station for temp
    st.markdown("#### 🌡️ Phân phối nhiệt độ & độ ẩm theo trạm")
    box_var = st.selectbox("Biến:", ["temperature_2m_mean", "relative_humidity_2m_mean",
                                     "dew_point_2m_mean", "pressure_msl_mean"])
    fig = px.box(dff_named, x="station_short", y=box_var, color="region",
                 title=f"Phân phối {box_var} theo trạm",
                 color_discrete_map={"Bắc": "#1565c0", "Trung": "#00897b", "Nam": "#f57f17"})
    fig.update_layout(height=400, xaxis_tickangle=-30)
    st.plotly_chart(fig, use_container_width=True)

# ══════════════════════════════════════════════
# TAB 4: Tương quan Biến
# ══════════════════════════════════════════════
with tabs[3]:
    st.markdown('<p class="section-header">🌡️ Phân tích Tương quan & Scatter</p>', unsafe_allow_html=True)

    # Correlation heatmap
    corr_vars = [
        "prcp_gsod_mm", "temperature_2m_mean", "relative_humidity_2m_mean",
        "dew_point_2m_mean", "pressure_msl_mean", "cloud_cover_mean",
        "wind_speed_10m_mean", "wind_gusts_10m_max", "shortwave_radiation_sum",
        "et0_fao_evapotranspiration", "soil_moisture_0_to_7cm_mean",
        "precipitation_hours", "wet_bulb_temperature_2m_mean",
        "vapour_pressure_deficit_max", "gust_factor"
    ]
    existing_corr = [v for v in corr_vars if v in dff.columns]
    corr_matrix = dff[existing_corr].corr()

    fig = px.imshow(corr_matrix, color_continuous_scale="RdBu_r",
                    zmin=-1, zmax=1,
                    title="Ma trận tương quan Pearson giữa các biến khí tượng",
                    text_auto=".2f", aspect="auto")
    fig.update_layout(height=600)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("""
    <div class="insight-box">💡 <b>Insight tương quan:</b> <b>Độ ẩm</b> và <b>điểm sương</b> có tương quan dương mạnh với lượng mưa. 
    <b>Áp suất</b> tương quan âm — áp thấp → mưa nhiều hơn. <b>Bức xạ mặt trời</b> tương quan âm với mây che phủ.</div>
    """, unsafe_allow_html=True)

    # Scatter plot tùy chọn
    st.markdown("#### 🔵 Scatter Plot tùy chọn")
    num_cols = [c for c in dff.select_dtypes(include=np.number).columns
                if c not in ["STATION", "FRSHTT", "year", "month", "day_of_year"]]

    c1, c2, c3 = st.columns(3)
    with c1:
        x_var = st.selectbox("Trục X:", num_cols, index=num_cols.index("relative_humidity_2m_mean") if "relative_humidity_2m_mean" in num_cols else 0)
    with c2:
        y_var = st.selectbox("Trục Y:", num_cols, index=num_cols.index("prcp_gsod_mm") if "prcp_gsod_mm" in num_cols else 1)
    with c3:
        color_by = st.selectbox("Màu theo:", ["region", "rain_class_label", "enso_phase", "station_short"])

    sample_size = st.slider("Số điểm mẫu:", 500, min(10000, len(dff)), 3000, 500)
    dff_sample = dff.dropna(subset=[x_var, y_var]).sample(min(sample_size, len(dff)), random_state=42)

    fig = px.scatter(dff_sample, x=x_var, y=y_var, color=color_by,
                     opacity=0.6, trendline="ols",
                     title=f"Scatter: {x_var} vs {y_var}",
                     hover_data=["station_short", "DATE"])
    fig.update_layout(height=450)
    st.plotly_chart(fig, use_container_width=True)

    # Pair plot summary statistics
    st.markdown("#### 📊 Top biến tương quan với prcp_gsod_mm")
    if "prcp_gsod_mm" in dff.columns:
        corr_target = dff[existing_corr].corr()["prcp_gsod_mm"].drop("prcp_gsod_mm").sort_values(key=abs, ascending=False).head(12)
        fig = px.bar(x=corr_target.values, y=corr_target.index,
                     orientation="h",
                     color=corr_target.values,
                     color_continuous_scale="RdBu_r",
                     color_continuous_midpoint=0,
                     title="Tương quan Pearson với prcp_gsod_mm (Top 12)",
                     labels={"x": "Pearson r", "y": "Biến"})
        fig.update_layout(height=400, coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

# ══════════════════════════════════════════════
# TAB 5: ENSO & Khí hậu
# ══════════════════════════════════════════════
with tabs[4]:
    st.markdown('<p class="section-header">🌊 ENSO, Mùa vụ & Yếu tố Khí hậu</p>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        # ENSO phase vs rain
        enso_rain = dff.groupby("enso_phase")["prcp_gsod_mm"].describe().round(2)
        fig = px.box(dff, x="enso_phase", y="prcp_gsod_mm", color="enso_phase",
                     title="Lượng mưa theo pha ENSO",
                     color_discrete_map={"el_nino": "#ef5350", "la_nina": "#42a5f5", "neutral": "#66bb6a"},
                     labels={"enso_phase": "Pha ENSO", "prcp_gsod_mm": "Lượng mưa (mm)"})
        fig.update_layout(height=380, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        # Monsoon vs non-monsoon
        dff = dff.copy()
        dff["Mùa"] = dff["is_monsoon"].map({1: "Mùa mưa", 0: "Mùa khô"})
        monsoon_rain = dff.groupby(["Mùa", "region"])["prcp_gsod_mm"].mean().reset_index()
        fig = px.bar(monsoon_rain, x="region", y="prcp_gsod_mm", color="Mùa",
                     barmode="group",
                     title="Lượng mưa TB: Mùa mưa vs Mùa khô theo vùng",
                     color_discrete_map={"Mùa mưa": "#1565c0", "Mùa khô": "#ff8f00"},
                     labels={"prcp_gsod_mm": "Lượng mưa TB (mm)", "region": "Vùng"})
        fig.update_layout(height=380)
        st.plotly_chart(fig, use_container_width=True)

    # MEI index over time
    st.markdown("#### 📉 Chỉ số MEI (ENSO) theo thời gian")
    mei_ts = dff.groupby("DATE")["enso_mei_current"].mean().reset_index()
    mei_ts = mei_ts.resample("ME", on="DATE").mean().reset_index()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=mei_ts["DATE"], y=mei_ts["enso_mei_current"],
                             fill="tozeroy", mode="lines",
                             line=dict(color="#1565c0"),
                             fillcolor="rgba(21,101,192,0.3)",
                             name="MEI"))
    fig.add_hline(y=0.5, line_dash="dash", line_color="red", annotation_text="El Niño (>0.5)")
    fig.add_hline(y=-0.5, line_dash="dash", line_color="blue", annotation_text="La Niña (<-0.5)")
    fig.update_layout(title="Chỉ số MEI theo tháng (2015–2024)", height=340,
                      xaxis_title="Thời gian", yaxis_title="MEI")
    st.plotly_chart(fig, use_container_width=True)

    # Köppen climate distribution
    st.markdown("#### 🌍 Phân tích theo vùng khí hậu Köppen")
    c1, c2 = st.columns(2)
    with c1:
        koppen_rain = dff.groupby(["koppen_Cwa", "koppen_Am", "koppen_Aw"]).agg(
            avg_rain=("prcp_gsod_mm", "mean"), n=("prcp_gsod_mm", "count")
        ).reset_index()
        koppen_labels = []
        koppen_vals = []
        for _, row in koppen_rain.iterrows():
            if row["koppen_Cwa"] == 1:
                koppen_labels.append("Cwa (Cận nhiệt đới ẩm)")
            elif row["koppen_Am"] == 1:
                koppen_labels.append("Am (Nhiệt đới gió mùa)")
            elif row["koppen_Aw"] == 1:
                koppen_labels.append("Aw (Nhiệt đới xavan)")
            else:
                koppen_labels.append("Khác")
            koppen_vals.append(row["avg_rain"])
        fig = px.bar(x=koppen_labels, y=koppen_vals,
                     title="Lượng mưa TB theo vùng khí hậu Köppen",
                     labels={"x": "Khí hậu Köppen", "y": "Lượng mưa TB (mm)"},
                     color=koppen_vals, color_continuous_scale="Blues")
        fig.update_layout(height=340, coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        # pressure anomaly distribution
        fig = px.histogram(dff, x="pressure_anomaly", color="enso_phase", nbins=60,
                           title="Phân phối Pressure Anomaly theo pha ENSO",
                           color_discrete_map={"el_nino": "#ef5350", "la_nina": "#42a5f5", "neutral": "#66bb6a"},
                           barmode="overlay", opacity=0.7)
        fig.update_layout(height=340)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("""
    <div class="insight-box">💡 <b>Insight ENSO:</b> La Niña có trung vị lượng mưa cao hơn El Niño ở miền Nam VN. 
    Tuy nhiên El Niño gây hạn hán ở vùng Trung. Độ trễ 3 tháng (enso_mei_3m_lag) quan trọng để dự báo sớm.</div>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════
# TAB 6: Feature Engineering
# ══════════════════════════════════════════════
with tabs[5]:
    st.markdown('<p class="section-header">🔬 Kiểm tra Feature Engineering & Lag Variables</p>', unsafe_allow_html=True)

    # Lag features effectiveness
    st.markdown("#### ⏱️ Hiệu quả của Lag Features (tương quan với prcp_gsod_mm)")
    lag_vars = [c for c in dff.columns if "lag" in c or "roll" in c]
    lag_corr = dff[lag_vars + ["prcp_gsod_mm"]].corr()["prcp_gsod_mm"].drop("prcp_gsod_mm")
    lag_corr = lag_corr.sort_values(key=abs, ascending=False).head(15)

    fig = px.bar(x=lag_corr.values, y=lag_corr.index, orientation="h",
                 color=lag_corr.values, color_continuous_scale="RdBu_r",
                 color_continuous_midpoint=0,
                 title="Tương quan lag/rolling features với prcp_gsod_mm",
                 labels={"x": "Pearson r", "y": "Feature"})
    fig.update_layout(height=450, coloraxis_showscale=False)
    st.plotly_chart(fig, use_container_width=True)

    # Rolling window analysis
    st.markdown("#### 📊 Rolling Sum Lượng mưa")
    c1, c2 = st.columns(2)
    roll_cols = ["prcp_gsod_mm_roll3_sum", "prcp_gsod_mm_roll7_sum",
                 "prcp_gsod_mm_roll14_sum", "prcp_gsod_mm_roll30_sum"]
    roll_cols = [c for c in roll_cols if c in dff.columns]

    with c1:
        roll_corr = dff[roll_cols + ["prcp_gsod_mm"]].corr()["prcp_gsod_mm"].drop("prcp_gsod_mm")
        fig = px.bar(x=roll_corr.index, y=roll_corr.values,
                     title="Tương quan Rolling Sum (GSOD) với target",
                     color=roll_corr.values, color_continuous_scale="Blues",
                     labels={"x": "Feature", "y": "Pearson r"})
        fig.update_layout(height=340, coloraxis_showscale=False, xaxis_tickangle=-20)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        # Cyclical features — month_sin/month_cos already exist in dataset
        fig = px.scatter(dff.sample(min(3000, len(dff)), random_state=1),
                         x="month_sin", y="month_cos",
                         color="prcp_gsod_mm", size_max=8,
                         color_continuous_scale="Blues",
                         title="Mã hóa vòng tuần hoàn tháng (sin-cos)",
                         labels={"month_sin": "sin(2π×month/12)", "month_cos": "cos(2π×month/12)"},
                         opacity=0.7)
        fig.update_layout(height=340)
        st.plotly_chart(fig, use_container_width=True)

    # Engineered features comparison
    st.markdown("#### 🌀 Đặc trưng vật lý: Gust Factor & Wet Bulb Depression")
    c1, c2 = st.columns(2)
    with c1:
        if "gust_factor" in dff.columns:
            fig = px.box(dff.dropna(subset=["rain_class_label"]), x="rain_class_label", y="gust_factor",
                         color="rain_class_label",
                         color_discrete_map={"Không mưa": "#90caf9", "Mưa thường": "#1565c0", "Mưa cực đoan": "#d32f2f"},
                         title="Gust Factor theo Rain Class",
                         labels={"rain_class_label": "Lớp mưa", "gust_factor": "Gust Factor"})
            fig.update_layout(height=360, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
    with c2:
        if "wet_bulb_depression" in dff.columns:
            fig = px.box(dff.dropna(subset=["rain_class_label"]),
                         x="rain_class_label", y="wet_bulb_depression",
                         color="rain_class_label",
                         color_discrete_map={"Không mưa": "#90caf9", "Mưa thường": "#1565c0", "Mưa cực đoan": "#d32f2f"},
                         title="Wet Bulb Depression theo Rain Class",
                         labels={"rain_class_label": "Lớp mưa", "wet_bulb_depression": "WBD (°C)"})
            fig.update_layout(height=360, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("""
    <div class="insight-box">💡 <b>Insight Feature:</b> <b>prcp_gsod_mm_roll7_sum</b> có tương quan cao nhất với target — tích lũy mưa 7 ngày là dấu hiệu rõ 
    nhất cho mưa cực đoan. <b>Wet bulb depression thấp</b> (không khí ẩm bão hòa) là tiền triệu quan trọng cho mưa lớn.</div>
    """, unsafe_allow_html=True)

    # target_reliable analysis
    st.markdown("#### ✅ Phân tích target_reliable & MNAR")
    c1, c2 = st.columns(2)
    with c1:
        reliable_by_station = df.groupby("station_short").agg(
            total=("target_reliable", "count"),
            reliable=("target_reliable", "sum")
        ).reset_index()
        reliable_by_station["pct"] = reliable_by_station["reliable"] / reliable_by_station["total"] * 100
        fig = px.bar(reliable_by_station.sort_values("pct"), x="pct", y="station_short",
                     orientation="h", title="% target_reliable theo trạm",
                     labels={"pct": "% Reliable", "station_short": "Trạm"},
                     color="pct", color_continuous_scale="Greens")
        fig.update_layout(height=400, coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        mnar_by_station = df.groupby("station_short")["prcp_mnar_station"].mean().reset_index()
        mnar_by_station.columns = ["Trạm", "MNAR Rate"]
        mnar_by_station = mnar_by_station.sort_values("MNAR Rate", ascending=False)
        fig = px.bar(mnar_by_station, x="MNAR Rate", y="Trạm", orientation="h",
                     title="Tỷ lệ MNAR (thiếu thiết bị đo mưa) theo trạm",
                     color="MNAR Rate", color_continuous_scale="Reds")
        fig.update_layout(height=400, coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

# ══════════════════════════════════════════════
# TAB 7: Truy vấn dữ liệu
# ══════════════════════════════════════════════
with tabs[6]:
    st.markdown('<p class="section-header">🔍 Truy vấn & Khám phá dữ liệu</p>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Lọc theo lượng mưa (mm)**")
        rain_min, rain_max = st.slider("Khoảng lượng mưa (mm):",
                                        0.0, float(dff["prcp_gsod_mm"].max()),
                                        (0.0, float(dff["prcp_gsod_mm"].max())), 0.1)
    with c2:
        st.markdown("**Lọc theo nhiệt độ (°C)**")
        temp_range = st.slider("Khoảng nhiệt độ (°C):",
                                float(dff["temperature_2m_mean"].min()),
                                float(dff["temperature_2m_mean"].max()),
                                (float(dff["temperature_2m_mean"].min()),
                                 float(dff["temperature_2m_mean"].max())), 0.5)

    query_rain_class = st.multiselect("Lọc theo Rain Class:",
                                       ["Không mưa", "Mưa thường", "Mưa cực đoan"],
                                       default=["Không mưa", "Mưa thường", "Mưa cực đoan"])

    # Apply query filters
    qdf = dff[
        (dff["prcp_gsod_mm"] >= rain_min) &
        (dff["prcp_gsod_mm"] <= rain_max) &
        (dff["temperature_2m_mean"] >= temp_range[0]) &
        (dff["temperature_2m_mean"] <= temp_range[1])
    ]
    if query_rain_class and "rain_class_label" in qdf.columns:
        qdf = qdf[qdf["rain_class_label"].isin(query_rain_class)]

    st.markdown(f"**Kết quả: {len(qdf):,} dòng** ({len(qdf)/len(dff)*100:.1f}% của tập lọc)")

    # Display columns selector
    display_cols = st.multiselect("Chọn cột hiển thị:",
                                   ["DATE", "station_short", "region", "prcp_gsod_mm",
                                    "temperature_2m_mean", "relative_humidity_2m_mean",
                                    "rain_class_label", "enso_phase", "is_monsoon",
                                    "pressure_msl_mean", "cloud_cover_mean", "wind_speed_10m_mean"],
                                   default=["DATE", "station_short", "region", "prcp_gsod_mm",
                                            "temperature_2m_mean", "rain_class_label", "enso_phase"])

    if display_cols:
        st.dataframe(qdf[display_cols].reset_index(drop=True), height=350, use_container_width=True)

    # Summary statistics for query result
    st.markdown("#### 📋 Thống kê mô tả kết quả truy vấn")
    num_display = [c for c in display_cols if c in qdf.select_dtypes(include=np.number).columns]
    if num_display:
        st.dataframe(qdf[num_display].describe().round(3), use_container_width=True)

    # Download button
    @st.cache_data
    def convert_to_csv(data):
        return data.to_csv(index=False).encode("utf-8")

    if not qdf.empty:
        csv_data = convert_to_csv(qdf[display_cols] if display_cols else qdf)
        st.download_button(
            label="⬇️ Tải xuống kết quả CSV",
            data=csv_data,
            file_name="weather_query_result.csv",
            mime="text/csv"
        )

    # Quick anomaly detection
    st.markdown("#### 🚨 Top ngày mưa cực đoan trong tập lọc")
    top_extreme = dff.nlargest(15, "prcp_gsod_mm")[
        ["DATE", "station_short", "region", "prcp_gsod_mm",
         "temperature_2m_mean", "relative_humidity_2m_mean", "enso_phase"]
    ].reset_index(drop=True)
    top_extreme.columns = ["Ngày", "Trạm", "Vùng", "Lượng mưa (mm)",
                            "Nhiệt độ (°C)", "Độ ẩm (%)", "Pha ENSO"]
    st.dataframe(top_extreme.style.background_gradient(subset=["Lượng mưa (mm)"], cmap="Blues"),
                 use_container_width=True)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align:center; color:#999; font-size:0.85rem;">
🌧️ Vietnam Weather ML Pipeline EDA Dashboard | 15 Trạm Khí tượng | 2015–2024 | Built with Streamlit + Plotly
</div>
""", unsafe_allow_html=True)