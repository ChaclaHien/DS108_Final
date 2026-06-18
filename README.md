# Tiền xử lí dữ liệu cho bài toán dự đoán khả năng mưa và mưa lũ cực đoan

---

## A. Thông tin dự án

| Trường | Nội dung |
|---|---|
| **Tên dự án** | Thu thập và tiền xử lí dữ liệu cho bài toán dự đoán khả năng mưa và mưa lũ cực đoan |
| **Môn học** | DS108 - Tiền xử lý và xây dựng bộ dữ liệu |
| **Trường** | Trường Đại học Công nghệ Thông tin – Đại học Quốc gia TP.HCM (UIT – VNU-HCM) |
| **Giảng viên hướng dẫn** | TS. Nguyễn Gia Tuấn Anh · CN. Trần Quốc Khánh |

### Mô tả 

Dữ liệu khí tượng thực tế thường tồn tại giá trị thiếu, nhiễu, sai khác giữa các nguồn và mất cân bằng ở những trường hợp mưa lớn. Nghiên cứu này xây dựng một pipeline tiền xử lí dữ liệu phục vụ bài toán dự đoán mưa và mưa cực đoan tại Việt Nam. Dữ liệu được thu thập và xử lí từ NOAA GSOD và Open-Meteo tại 15 trạm khí tượng trong giai đoạn 2015–2024.

### Thành viên nhóm

| Họ tên | MSSV |
|---|---|
| Phạm Nguyễn Minh Hiền | 24520478 |
| Trần Hải Hoàng | 24520567 |

---

## B. Mục tiêu dự án

1. Xây dựng pipeline thu thập và tích hợp dữ liệu đa nguồn (NOAA GSOD + Open-Meteo ERA5) cho 15 trạm khí tượng tại Việt Nam giai đoạn 2015–2024.
2. Chuẩn hóa, làm sạch và xử lí dữ liệu thiếu có cơ sở — chẩn đoán cơ chế MCAR/MAR/MNAR theo từng biến và từng trạm, áp dụng cơ chế phù hợp (cross-source fill, MICE, median fallback).
3. Xây dựng biến mục tiêu `rain_class` (3 lớp: không mưa / mưa thường / mưa cực đoan ≥50mm) và tập đặc trưng phong phú phản ánh mùa vụ, ENSO, gió, áp suất, địa lý và thủy văn.
4. Thiết kế chiến lược chia tập (Year-Based Expanding Window CV, held-out test 2024) đảm bảo không rò rỉ thông tin tương lai vào quá trình huấn luyện.

### Kết quả đầu ra 

- Dataset cuối (`test_final.parquet`, `train_representative.parquet`, `val_representative.parquet`) sẵn sàng cho modeling
- 5 cặp fold CV (`data/processed/feature_engineered/folds/`)
- Codebook mô tả toàn bộ biến (`df_codebook_final.parquet`, `Codebook.md`)
- Dashboard phân tích EDA bằng Streamlit (`dashboard/app.py`)
- Báo cáo khoa học định dạng IEEE (`DS108__real__.pdf`)

---

## C. Nguồn dữ liệu

### Dataset 1 — NOAA Global Summary of the Day (GSOD)

| Trường | Nội dung |
|---|---|
| **Tên nguồn** | NOAA Global Summary of the Day (GSOD) |
| **Đơn vị cung cấp** | NOAA National Centers for Environmental Information (NCEI) |
| **Khoảng thời gian** | 2015-01-01 đến 2024-12-31 |
| **Mô tả dữ liệu** | Dữ liệu quan trắc bề mặt theo ngày tại 15 trạm khí tượng trên lãnh thổ Việt Nam. Là nguồn chính để xây dựng biến mục tiêu (lượng mưa thực đo). |

**Biến quan trọng:**
- `PRCP` — Lượng mưa (inches → mm sau chuẩn hóa), cơ sở xây dựng `rain_class`
- `TEMP`, `MAX`, `MIN`, `DEWP` — Nhiệt độ và điểm sương (°F → °C)
- `WDSP`, `MXSPD` — Tốc độ gió trung bình và cực đại (knots → km/h)
- `SLP` — Áp suất mực biển (millibars)
- `VISIB` — Tầm nhìn (miles → km)
- `FRSHTT` — Mã hiện tượng thời tiết

---

### Dataset 2 — Open-Meteo Historical Weather API (ERA5)

| Trường | Nội dung |
|---|---|
| **Tên nguồn** | Open-Meteo Historical Weather API |
| **Đơn vị cung cấp** | Open-Meteo (dữ liệu tái phân tích ERA5 từ ECMWF) |
| **Khoảng thời gian** | 2015-01-01 đến 2024-12-31 |
| **Mô tả dữ liệu** | Dữ liệu tái phân tích truy vấn theo tọa độ từng trạm GSOD (snap-to-grid ERA5, độ phân giải ~25–31 km). Dùng làm nguồn bổ sung đặc trưng và điền khuyết cho GSOD. |

**Biến quan trọng:**
- `precipitation_sum` — Tổng mưa tái phân tích (dùng thay thế cho 2 trạm MNAR)
- `temperature_2m_mean/max/min` — Nhiệt độ không khí 2m
- `relative_humidity_2m_mean` — Độ ẩm tương đối
- `wind_speed_10m_mean/max`, `wind_direction_10m_dominant` — Gió tại 10m
- `pressure_msl_mean` — Áp suất mực biển (thay thế `SLP_hpa`)
- `shortwave_radiation_sum` — Bức xạ sóng ngắn
- `soil_moisture_0_to_7cm_mean`, `soil_moisture_28_to_100cm_mean` — Độ ẩm đất

---

## D. Cấu trúc thư mục

```
project_root/
│
├── data/
│   ├── raw/
│   │   ├── noaa_gsod_daily.parquet        # Dữ liệu GSOD thô sau thu thập
│   │   └── openmeteo_15stations.parquet   # Dữ liệu Open-Meteo thô sau thu thập
│   │
│   └── processed/
│       ├── preprocessed/                  # Dữ liệu sau tiền xử lý 
│       │   ├── cv_folds/                  # 5 cặp fold expanding window
│       │   ├── df_full_processed.parquet  # Toàn bộ dữ liệu sau clean + impute
│       │   ├── train_repr.parquet         # Tập train đại diện (2015–2022)
│       │   ├── val_repr.parquet           # Tập val đại diện (2023)
│       │   └── test.parquet              # Tập test (2024)
│       │
│       └── feature_engineered/            # Dữ liệu sau feature engineering 
│           ├── folds/                     # 5 cặp fold sau feature engineering
│           ├── df_codebook_final.parquet  # Toàn bộ dữ liệu cuối cùng
│           ├── test_final.parquet         # Tập test cuối (105 cột)
│           ├── train_representative.parquet
│           └── val_representative.parquet
│
├── notebook/
│   ├── collection.ipynb                   # Thu thập dữ liệu GSOD + Open-Meteo
│   ├── preprocessing.ipynb                # Tiền xử lý, điền khuyết, chia tập
│   └── feature_engineering.ipynb         # Feature engineering, kiểm định dư thừa
│
├── dashboard/
│   └── app.py                             # Dashboard Streamlit EDA
│
├── Codebook.md                            # Từ điển dữ liệu 
├── README.md
└── requirement.txt
```

### Giải thích các thư mục

| Thư mục | Mục đích |
|---|---|
| `data/raw/` | Dữ liệu gốc sau khi thu thập từ NOAA và Open-Meteo, không chỉnh sửa |
| `data/processed/preprocessed/` | Dữ liệu sau xử lý sentinel values, chuẩn hóa đơn vị, imputation, chia tập |
| `data/processed/feature_engineered/` | Dataset cuối sau feature engineering và loại bỏ dư thừa (105 cột) |
| `notebook/` | Jupyter Notebooks thực thi toàn bộ pipeline theo thứ tự |
| `dashboard/` | Dashboard Streamlit phân tích EDA |
| `Codebook.md` | Từ điển mô tả ý nghĩa, kiểu dữ liệu, đơn vị của từng biến |

---

## E. Kiến trúc dữ liệu

```

| Tầng | Mô tả |
|---|---|
| **Raw** | Dữ liệu thô từ NOAA GSOD (54.067 dòng) và Open-Meteo, chưa xử lý, còn chứa sentinel values và đơn vị gốc (°F, inches, knots, miles) |
| **Preprocessed** | Dữ liệu đã làm sạch: sentinel → NaN, chuẩn hóa sang SI, Skeleton DataFrame, điền khuyết (cross-source fill + MICE), chia tập time-series. 54.795 dòng × 61 cột sau loại bỏ cột null/hằng/trùng |
| **Feature Engineered** | Dataset cuối sau feature engineering: 105 cột gồm đặc trưng thời gian tuần hoàn, ENSO, lag/rolling precipitation, gió, áp suất, địa lý, độ ẩm đất. Sẵn sàng đưa vào mô hình ML |
```
---

## F. Pipeline xử lý dữ liệu

```
NOAA GSOD API          Open-Meteo Historical API
(15 trạm × 10 năm)    (ERA5, tọa độ trạm GSOD)
        ↓                        ↓
   Thu thập dữ liệu tự động (không can thiệp thủ công)
        ↓
   Kiểm tra toàn vẹn (DataFrame không rỗng, biên ngày,
   số ngày/năm, phát hiện Pattern A/B/C missing)
        ↓
   Skeleton DataFrame (tái cấu trúc ngày thiếu → NaN rows)
        ↓
   Kiểm tra chất lượng nguồn
   (Haversine ≤ 50km, MAE nhiệt độ tại lát cắt chuyển mùa,
    kiểm tra khóa trùng, ma trận bao phủ 15×10)
        ↓
   Left join GSOD ← Open-Meteo theo (STATION, DATE)
   → 54.067 dòng, không row explosion
        ↓
   Xử lý Sentinel Values → NaN
   Chuẩn hóa đơn vị (°F→°C, inch→mm, knots→km/h, miles→km)
   Loại cột: 100% null, hằng số, trùng lặp (102→61 cột)
        ↓
   Chẩn đoán missing: Little's MCAR test + MAR logistic regression
   Phân loại từng biến: MNAR event-driven / MNAR cấu trúc / MAR
        ↓
   Chia tập Year-Based Expanding Window CV
   (Train: 2015–2022 | Val fold: 2019/20/21/22/23 | Test: 2024)
        ↓
   Điền khuyết hai tầng (per-fold, fit only on train):
   Tầng 1: Cross-source fill (ERA5 tương đương)
   Tầng 2: MICE BayesianRidge (prcp_gsod_mm, VISIB_km)
   Tầng 3: Median fallback (dự phòng)
   + Domain clipping (giá trị âm → 0, ngưỡng vật lý)
        ↓
   Phát hiện outlier (IQR / Z-score / Isolation Forest)
   — chẩn đoán, KHÔNG loại bỏ (outlier = tín hiệu cực đoan)
        ↓
   Xây dựng biến mục tiêu rain_class (3 lớp):
   0: < 0.1mm | 1: 0.1–50mm | 2: ≥ 50mm
   + target_reliable flag (loại nhãn không tin cậy khỏi loss)
        ↓
   Feature Engineering (61→130 cột):
   Thời gian tuần hoàn, ENSO lag, lag/rolling precipitation,
   gió (sin/cos), áp suất anomaly, địa lý, độ ẩm đất
        ↓
   Kiểm định dư thừa (Pearson, MI, PCA, VIF)
   Loại 25 cột (130→105 cột)
        ↓
   Dataset cuối: train/val/test + 5 fold CV
   (54.795 dòng × 105 cột)
```

## G. Chi tiết Notebooks

| File | Chức năng |
|---|---|
| `notebook/collection.ipynb` | Thu thập dữ liệu |
| `notebook/preprocessing.ipynb` | Xử lý sentinel values; chuẩn hóa đơn vị SI; loại cột dư thừa; Year-Based Expanding Window CV split; điền khuyết hai tầng |
| `notebook/feature_engineering.ipynb` | Tạo các đặc trưng; kiểm định và loại cột dư thừa; xuất dataset cuối và codebook |

---

### Dataset cuối

| Thuộc tính | Giá trị |
|---|---|
| **Tên file train** | `train_representative.parquet` |
| **Tên file val** | `val_representative.parquet` |
| **Tên file test** | `test_final.parquet` |
| **Tổng số dòng** | 54.795 dòng |
| **Số cột** | 105 cột |
| **Khoảng thời gian** | 2015-01-01 đến 2024-12-31 |
| **Tập train** | 2015–2022 — 43.830 dòng |
| **Tập val** | 2023 — 5.475 dòng |
| **Tập test** | 2024 — 5.490 dòng |
| **Biến mục tiêu** | `rain_class` (3 lớp), `rain_binary`, `target_reliable` |
| **Imbalance Ratio** | IR ≈ 21.9 (3-class scheme được chọn) |

---

## H. Phân tích dữ liệu (EDA)

### Các nội dung phân tích

- Thống kê mô tả toàn bộ biến
- Phân phối lượng mưa và các lớp `rain_class`
- Missing values — ma trận theo Trạm × Biến, theo Trạm × Tháng, theo Trạm × Năm
- Pattern thiếu dữ liệu (Pattern A/B/C) và chẩn đoán cơ chế MNAR
- Outlier — IQR, Z-score, Isolation Forest (chẩn đoán, không loại)
- Tương quan giữa các đặc trưng (Pearson heatmap)
- Time series analysis — xu hướng lượng mưa theo năm, theo mùa
- Spatial analysis — phân bố 15 trạm, mật độ theo vùng
- Mutual Information Score — xếp hạng đóng góp đặc trưng với `rain_binary`
- PCA — tỷ lệ phương sai giải thích theo số thành phần chính

---

## K. Dashboard

| Trường | Nội dung |
|---|---|
| **Công nghệ** | Streamlit + Plotly |
| **File chính** | `dashboard/app.py` |
| **Data source** | `data/processed/feature_engineered/df_codebook_final.parquet` |

**Chạy dashboard:**
```bash
streamlit run dashboard/app.py
```

**KPI header (luôn hiển thị):**

| Chỉ số | Mô tả |
|---|---|
| 📋 Tổng quan sát | Số dòng sau khi áp bộ lọc |
| 🌧️ Ngày có mưa | Số ngày `prcp_gsod_mm > 0.1mm` + % tổng |
| ⛈️ Mưa cực đoan | Số ngày `prcp_gsod_mm ≥ 50mm` + % tổng |
| 💧 Lượng mưa TB | Mean `prcp_gsod_mm` (mm) |
| 🌡️ Nhiệt độ TB | Mean `temperature_2m_mean` (°C) |
| 💦 Độ ẩm TB | Mean `relative_humidity_2m_mean` (%) |

**Các tab chính:**

**Tab 1. 📊 Phân phối Mưa**
- Donut chart phân bố 3 lớp `rain_class` (Không mưa / Mưa thường / Mưa cực đoan) kèm insight imbalance ratio
- Histogram lượng mưa log-scale theo vùng, có đường ngưỡng 25mm và 50mm
- Bar chart lượng mưa TB theo tháng × vùng (Bắc / Trung / Nam) — phân tích mùa vụ
- Violin plot phân phối lượng mưa theo từng trạm (chỉ ngày mưa)

**Tab 2. 📈 Chuỗi Thời Gian**
- Line chart time-series cho 8 biến tùy chọn (mưa, nhiệt độ, độ ẩm, áp suất, mây, gió, điểm sương, ET0) theo Tuần / Tháng / Quý với hàm Mean / Sum / Max
- Heatmap lượng mưa TB theo Tháng × Năm (toàn bộ 15 trạm)
- Bar chart số ngày mưa cực đoan (≥50mm) theo năm × trạm

**Tab 3. 🗺️ So sánh Trạm**
- Bản đồ scatter mapbox 15 trạm (kích thước = lượng mưa TB, màu = vùng khí hậu)
- Bar chart so sánh lượng mưa TB/ngày và số ngày cực đoan theo trạm
- Box plot phân phối 4 biến tùy chọn (nhiệt độ, độ ẩm, điểm sương, áp suất) theo trạm

**Tab 4. 🌡️ Tương quan Biến**
- Heatmap ma trận tương quan Pearson (15 biến khí tượng chính)
- Scatter plot tùy chọn trục X/Y/màu với trendline OLS (có thể sample đến 10.000 điểm)
- Bar chart top 12 biến tương quan cao nhất với `prcp_gsod_mm`

**Tab 5. 🌊 ENSO & Khí hậu**
- Box plot lượng mưa theo pha ENSO (El Niño / La Niña / Neutral)
- Bar chart lượng mưa TB Mùa mưa vs Mùa khô theo vùng
- Line chart chỉ số MEI theo tháng (2015–2024) với ngưỡng El Niño / La Niña
- Bar chart lượng mưa TB theo vùng khí hậu Köppen (Cwa / Am / Aw)
- Histogram phân phối `pressure_anomaly` theo pha ENSO

**Tab 6. 🔬 Feature Engineering**
- Bar chart tương quan top 15 lag/rolling features với `prcp_gsod_mm`
- Bar chart tương quan rolling sum (3/7/14/30 ngày) với target
- Scatter plot mã hóa tuần hoàn `month_sin` × `month_cos` tô màu theo lượng mưa
- Box plot `gust_factor` và `wet_bulb_depression` theo `rain_class`
- Bar chart % `target_reliable` theo trạm
- Bar chart tỷ lệ MNAR (`prcp_mnar_station`) theo trạm

**Tab 7. 🔍 Truy vấn dữ liệu**
- Lọc kết hợp theo khoảng lượng mưa, nhiệt độ và `rain_class_label`
- Chọn cột hiển thị tùy ý, xem bảng dữ liệu trực tiếp
- Thống kê mô tả kết quả truy vấn
- Nút tải xuống CSV kết quả truy vấn
- Bảng Top 15 ngày mưa cực đoan (highlight gradient)

**Bộ lọc sidebar (áp dụng toàn bộ dashboard):**

| Bộ lọc | Loại | Mô tả |
|---|---|---|
| 📅 Khoảng thời gian | Date range | Lọc theo ngày bắt đầu – kết thúc (2015–2024) |
| 🏢 Trạm khí tượng | Multiselect | Chọn 1 hoặc nhiều trong 15 trạm |
| 🗺️ Vùng khí hậu | Selectbox | Tất cả / Bắc / Trung / Nam |
| 📆 Năm | Multiselect | Chọn một hoặc nhiều năm (2015–2024) |
| 🌊 Pha ENSO | Selectbox | Tất cả / El Niño / La Niña / Neutral |
| ✅ Chỉ target_reliable | Checkbox | Lọc chỉ dòng có `target_reliable=True` (mặc định bật) |

---

## N. Yêu cầu môi trường

| Thành phần | 
|---|
| **Python** | 

**Cài đặt thư viện:**
```bash
pip install -r requirement.txt
```
---

## O. Hướng dẫn sử dụng

### 1. Clone repository
```bash
git clone <https://github.com/ChaclaHien/DS108_Final>
cd <project_name>
```

### 2. Cài đặt môi trường
```bash
pip install -r requirement.txt
```

### 3. Chạy pipeline theo thứ tự

**Bước 1 — Thu thập dữ liệu:**
```bash
jupyter notebook notebook/collection.ipynb
```

**Bước 2 — Tiền xử lý:**
```bash
jupyter notebook notebook/preprocessing.ipynb
```

**Bước 3 — Feature Engineering:**
```bash
jupyter notebook notebook/feature_engineering.ipynb
```

### 4. Chạy Dashboard
```bash
streamlit run dashboard/app.py
```

---

## P. Các file cấu hình quan trọng

| File | Chức năng |
|---|---|
| `requirement.txt` | Thư viện Python cần thiết |
| `Codebook.md` | Từ điển dữ liệu — mô tả ý nghĩa, đơn vị, kiểu dữ liệu của 105 biến |

---

## Q. Công nghệ sử dụng

| Hạng mục | Công nghệ |
|---|---|
| **Data Collection** | `requests`, `requests_cache`, `pandas` |
| **Data Processing** | `pandas`, `numpy`, `scikit-learn` (MICE/BayesianRidge) |
| **Missing Data** | `pyampute` (Little's MCAR), `statsmodels` (MAR logistic regression), `sklearn.impute.IterativeImputer` |
| **Outlier Detection** | `sklearn.ensemble.IsolationForest`, IQR, Z-score |
| **Feature Selection** | `sklearn.feature_selection.mutual_info_classif`, `statsmodels` VIF, PCA |
| **Visualization / EDA** | `matplotlib`, `seaborn`, `plotly`, `plotly.express`, `plotly.graph_objects` |
| **Dashboard** | `streamlit`, `plotly` (scatter_mapbox, imshow, violin, box, histogram, scatter, bar) |
| **Notebook** | Jupyter Notebook |

---

## R. Kết quả chính

**Đóng góp nổi bật:**
- Skeleton DataFrame — phát hiện ngày thiếu hoàn toàn không bị phát hiện bởi kiểm tra NaN thông thường
- Chẩn đoán MNAR cấu trúc theo trạm (trạm 48831, 48820, 48900) — tránh điền khuyết sai lệch các sự kiện cực đoan
- Year-Based Expanding Window CV — khắc phục lỗi `TimeSeriesSplit` cắt giữa năm với dữ liệu bảng 15 trạm
- Kiểm soát leakage toàn diện: MICE fit-on-train, lag/rolling shift 1 ngày, loại `prcp_gsod_mm` khỏi feature matrix

**Hạn chế:**
- 15 trạm chủ yếu ở đồng bằng, ven biển, đô thị — chưa đại diện cho vùng núi, hải đảo và địa hình phức tạp.
- Open-Meteo là dữ liệu tái phân tích, không hoàn toàn thay thế được quan trắc tại trạm, đặc biệt với mưa cực đoan có tính cục bộ cao.
- Chẩn đoán MNAR dựa trên cấu trúc hợp lý nhưng chưa xác nhận được nguyên nhân vật lý cụ thể (hỏng thiết bị do thời tiết cực đoan).
- Thời gian quan sát 10 năm còn tương đối ngắn để mô tả ổn định các sự kiện mưa chu kỳ dài; lớp cực đoan vẫn chiếm tỷ lệ thấp (1.9%).

**Hướng phát triển**

- Mở rộng số trạm, thời gian quan sát và tích hợp dữ liệu radar, vệ tinh (GPM IMERG), lưu lượng dòng chảy.
- Đánh giá phương pháp điền khuyết bằng thí nghiệm che dữ liệu có kiểm soát (masked imputation experiment).
- Hiệu chỉnh ngưỡng mưa cực đoan theo vùng khí hậu hoặc kết hợp Extreme Value Theory.
- Huấn luyện và so sánh mô hình (LightGBM, XGBoost, Random Forest) — đánh giá tập trung vào Recall, F1, PR-AUC của lớp cực đoan.
- Đóng gói pipeline thành quy trình tự động có quản lý phiên bản dữ liệu và kiểm tra chất lượng định kỳ.

---

## T. Tài liệu tham khảo

### Dữ liệu
- NOAA GSOD: https://www.ncei.noaa.gov/access/metadata/landing-page/bin/iso?id=gov.noaa.ncdc:C00516
- Open-Meteo Historical API: https://open-meteo.com/en/docs/historical-weather-api

### Bài báo / Tài liệu học thuật
- R. Lam et al., "Learning skillful medium-range global weather forecasting," *Science*, vol. 382, no. 6677, pp. 1416–1421, 2023. https://doi.org/10.1126/science.adi2336
- A. U. G. Senocak et al., "An explainable two-stage machine learning approach for precipitation forecast," *Journal of Hydrology*, vol. 627, p. 130375, 2023. https://doi.org/10.1016/j.jhydrol.2023.130375
- T. Gebru et al., "Datasheets for datasets," *Communications of the ACM*, vol. 64, no. 12, pp. 86–92, 2021. https://doi.org/10.1145/3458723

### Thư viện
- scikit-learn: https://scikit-learn.org/
- Streamlit: https://streamlit.io/
- pandas: https://pandas.pydata.org/

---

## U. Giấy phép

Chỉ phục vụ học tập — môn DS108, UIT – VNU-HCM.

---

## V. Liên hệ

| Trường | Nội dung |
|---|---|
| **Repository** | https://github.com/ChaclaHien/DS108_Final |
| **Email** | 24520478@gm.uit.edu.vn / 24520567@gm.uit.edu.vn |
| **Ngày cập nhật cuối** | 18/06/2026 |
| **Trạng thái dự án** | Hoàn thành (pipeline tiền xử lý) — Đang phát triển (modeling) |
