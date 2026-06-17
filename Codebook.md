# 📘 DATA DICTIONARY / CODE BOOK

**Tên dự án:** Xây dựng Benchmark Dataset Khí tượng Thủy văn Việt Nam từ Dữ liệu Đa nguồn (GSOD & Open-Meteo).  
**File dữ liệu thành phẩm:** `data/processed/vietnam_weather_benchmark.csv` (hoặc `.parquet`)  
**Phạm vi thời gian:** `2015-01-01` → `2024-12-31`  
**Tổng số cột:** 105 biến (bao gồm biến thô, biến tích hợp, biến phái sinh và biến nhãn mục tiêu).

---

## 1. Thông tin chung (Metadata)

- **Định dạng file:** Comma-Separated Values (`.csv`) / Apache Parquet (`.parquet`)
- **Mã hóa:** `UTF-8`
- **Nguồn dữ liệu chính:**
  - **GSOD (Global Surface Summary of the Day):** Dữ liệu quan trắc từ các trạm khí tượng mặt đất của NOAA/USAF.
  - **Open-Meteo:** Dữ liệu tái phân tích khí hậu (reanalysis) độ phân giải cao từ mô hình ERA5.
  - **NOAA MEI:** Chỉ số ENSO đa biến (Multivariate ENSO Index) từ NOAA.
- **Xử lý dữ liệu khuyết:**
  - Sentinel values (ví dụ: `9999.9`, `999.9`, `99.99`) đã được thay bằng `NaN` trước mọi thao tác tính toán.
  - Áp dụng chiến lược **nội suy chéo nguồn (Cross-Source Imputation):** ưu tiên điền từ Open-Meteo khi dữ liệu GSOD khuyết và `target_reliable == True`.
  - Phần còn lại áp dụng **MICE (Multiple Imputation by Chained Equations)** với estimator `BayesianRidge`, fit riêng trên tập train để tránh Data Leakage.
  - Các giá trị ngoài miền vật lý bị ép về ngưỡng cho phép sau khi nội suy.
- **Phân chia tập dữ liệu:** Chia theo năm (Year-based Split) để tránh Data Leakage theo chuỗi thời gian.
- **Xử lý trùng lặp:** Các bản ghi trùng cặp `(STATION, DATE)` đã bị loại bỏ; chỉ giữ dòng ưu tiên cao nhất theo `TEMP_ATTRIBUTES`.

---

## 2. Chi tiết các biến và Nhãn dữ liệu

### Nhóm 1: Biến Định danh & Địa lý (Identifiers & Geospatial)

*Nguồn: GSOD. Các biến này xác định danh tính và vị trí địa lý của từng trạm quan trắc.*

| Tên Cột (Variable) | Kiểu Dữ Liệu | Null Count | Min | Max | Mean | Description | Source/Note |
| :--- | :--- | :---: | :--- | :--- | :--- | :--- | :--- |
| `DATE` | `datetime64[us]` | 0 | 2015-01-01 | 2024-12-31 | N/A | Ngày quan sát khí tượng. | Chuẩn hóa `datetime64[ns]` timezone-naive, bỏ giờ/phút/giây (00:00:00). |
| `STATION` | `int64` | 0 | 48,820,099,999 | 48,914,099,999 | 48,860,033,332.33 | Mã trạm khí tượng gốc (USAF). | Loại bản ghi lặp (STATION, DATE), giữ dòng cao nhất theo TEMP_ATTRIBUTES. |
| `LATITUDE` | `float64` | 728 | 9.1833 | 21.6000 | 15.9882 | Vĩ độ trạm khí tượng. | |
| `LONGITUDE` | `float64` | 728 | 105.0833 | 109.2167 | 106.6550 | Kinh độ trạm khí tượng. | |
| `ELEVATION` | `float64` | 728 | 2.0000 | 741.8800 | 64.6872 | Độ cao của trạm so với mực nước biển (mét). | |
| `NAME` | `str` | 728 | N/A | N/A | N/A | Tên quốc tế của trạm khí tượng (tiếng Anh). | |

---

### Nhóm 2: Biến Khí tượng Gốc từ GSOD (Raw GSOD Variables — Đã Chuẩn hóa Đơn vị)

*Nguồn: GSOD. Tất cả sentinel values đã được thay bằng `NaN`. Đã quy đổi đơn vị về hệ SI/metric. Đã áp ngưỡng miền vật lý (physical domain clipping) sau nội suy.*

| Tên Cột (Variable) | Kiểu Dữ Liệu | Null Count | Min | Max | Mean | Description | Source/Note |
| :--- | :--- | :---: | :--- | :--- | :--- | :--- | :--- |
| `FRSHTT` | `float64` | 728 | 0.0000 | 111,010.0000 | 6,245.6081 | Mã nhị phân tổng hợp các hiện tượng thời tiết trong ngày (Sương mù, Mưa, Tuyết, Mưa đá, Sấm sét, Lốc xoáy). | |
| `TEMP_c` | `float64` | 728 | 5.6111 | 36.3333 | 26.1391 | Nhiệt độ trung bình ngày quy đổi sang Celsius (°C). | Quy đổi từ Fahrenheit sang Celsius theo công thức $C = (F - 32) \times \frac{5}{9}$. Sentinel value → NaN. |
| `DEWP_c` | `float64` | 728 | -3.3889 | 29.5556 | 22.1492 | Nhiệt độ điểm sương trung bình ngày quy đổi sang Celsius (°C). | Sentinel value 9999.9 → NaN. Cross-source Fill từ `dew_point_2m_mean` (Open-Meteo); áp ngưỡng miền vật lý $[-30.0, 40.0]$. |
| `MAX_c` | `float64` | 728 | 6.0000 | 44.2222 | 29.7074 | Nhiệt độ không khí cao nhất trong ngày quy đổi sang Celsius (°C). | Sentinel value 9999.9 → NaN. Cross-source Fill từ `temperature_2m_max` (Open-Meteo); áp ngưỡng miền vật lý $[-20.0, 50.0]$. |
| `MIN_c` | `float64` | 728 | 4.5000 | 33.1111 | 23.0949 | Nhiệt độ không khí thấp nhất trong ngày quy đổi sang Celsius (°C). | Sentinel value 9999.9 → NaN. Cross-source Fill từ `temperature_2m_min` (Open-Meteo); áp ngưỡng miền vật lý $[-20.0, 45.0]$. |
| `prcp_gsod_mm` | `float64` | 728 | 0.0000 | 425.9580 | 5.8454 | Lượng mưa tổng ngày từ GSOD quy đổi sang mm (mm). | Sentinel value 99.99 inches → NaN. Cross-source Fill từ `precipitation_sum` (Open-Meteo) khi `target_reliable == True`; các ô còn lại xử lý bằng MICE (BayesianRidge, fit trên tập train), áp ngưỡng miền vật lý ($\geq 0.0$). |
| `WDSP_kmh` | `float64` | 728 | 0.0000 | 37.2252 | 7.3800 | Tốc độ gió trung bình ngày quy đổi sang km/h (km/h). | Sentinel value 999.9 knots → NaN. Cross-source Fill từ `wind_speed_10m_mean` (Open-Meteo); áp ngưỡng miền vật lý ($\geq 0.0$). |
| `MXSPD_kmh` | `float64` | 728 | 3.5188 | 90.0072 | 13.4384 | Tốc độ gió tối đa trong ngày quy đổi sang km/h (km/h). | Sentinel value 999.9 knots → NaN. Cross-source Fill từ `wind_speed_10m_max` (Open-Meteo); áp ngưỡng miền vật lý ($\geq 0.0$). |
| `VISIB_km` | `float64` | 728 | 0.9656 | 50.0505 | 15.2354 | Tầm nhìn xa trung bình ngày quy đổi sang km (km). | Sentinel value 999.9 miles → NaN. Giá trị khuyết xử lý bằng MICE (BayesianRidge, fit trên tập train); các ô còn sót lại điền bằng median fallback từ tập train, áp ngưỡng miền vật lý ($\geq 0.0$). |

---

### Nhóm 3: Cờ Chất lượng & Metadata Trạm (QC Flags)

*Các cờ nhị phân được tạo ra trong quá trình kiểm tra chất lượng và tích hợp đa nguồn.*

| Tên Cột (Variable) | Kiểu Dữ Liệu | Null Count | Min | Max | Mean | Description | Source/Note |
| :--- | :--- | :---: | :--- | :--- | :--- | :--- | :--- |
| `gust_observed` | `float64` | 728 | 0.0000 | 1.0000 | 0.0257 | Cờ nhị phân xác nhận trạm có ghi nhận gió giật thực đo trong ngày (1 = có, 0 = không). | Cột mới tạo trong bước kiểm tra chất lượng dữ liệu GSOD. |
| `slp_is_gsod` | `float64` | 728 | 0.0000 | 1.0000 | 0.7976 | Cờ nhị phân đánh dấu giá trị áp suất mực biển (SLP) lấy từ nguồn GSOD thay vì Open-Meteo (1 = GSOD, 0 = Open-Meteo). | Cột mới tạo trong bước tích hợp hai nguồn dữ liệu. |
| `prcp_mnar_station` | `float64` | 728 | 0.0000 | 1.0000 | 0.1345 | Cờ nhị phân xác định dữ liệu lượng mưa bị khuyết không ngẫu nhiên do trạm không có thiết bị đo mưa (MNAR). 1 = trạm không có thiết bị đo, 0 = trạm có thiết bị đo. | Cột mới tạo trong bước phân tích cơ chế khuyết dữ liệu. |
| `imputed_from_om` | `object` | 728 | N/A | N/A | N/A | Cờ logic đánh dấu Cross-source Fill từ Open-Meteo (True = đã điền từ Open-Meteo, False = dữ liệu gốc / không điền). | |

---

### Nhóm 4: Biến Tái phân tích từ Open-Meteo (Reanalysis Variables)

*Nguồn: Open-Meteo (ERA5 reanalysis). Phủ toàn bộ khung thời gian và không gian của dataset.*

| Tên Cột (Variable) | Kiểu Dữ Liệu | Null Count | Min | Max | Mean | Description | Source/Note |
| :--- | :--- | :---: | :--- | :--- | :--- | :--- | :--- |
| `precipitation_sum` | `float64` | 728 | 0.0000 | 551.2000 | 5.8811 | Tổng lượng mưa tích lũy trong ngày (mm). | Giúp điền khuyết `prcp_gsod_mm` khi `target_reliable == True`. |
| `precipitation_hours` | `float64` | 728 | 0.0000 | 24.0000 | 6.9815 | Tổng số giờ có lượng mưa > 0.1 mm trong ngày. | |
| `temperature_2m_mean` | `float64` | 728 | 5.6710 | 35.6938 | 25.4956 | Nhiệt độ không khí trung bình ngày đo ở độ cao 2m (°C). | Hỗ trợ MICE và tính các biến phái sinh nhiệt động lực học. |
| `apparent_temperature_mean` | `float64` | 728 | 0.5387 | 40.3593 | 29.1710 | Cảm giác nhiệt độ trung bình ngày (°C). | |
| `dew_point_2m_mean` | `float64` | 728 | -4.9104 | 27.9833 | 21.5694 | Nhiệt độ điểm sương trung bình ngày ở độ cao 2m (°C). | Giúp điền khuyết `DEWP_c` theo Cross-source Fill. |
| `wet_bulb_temperature_2m_mean` | `float64` | 728 | 2.2344 | 28.9088 | 22.7432 | Nhiệt độ bầu ướt trung bình ngày ở độ cao 2m, giới hạn làm mát bằng bay hơi (°C). | |
| `relative_humidity_2m_max` | `float64` | 728 | 45.1570 | 100.0000 | 92.9126 | Độ ẩm tương đối không khí cực đại trong ngày ở độ cao 2m (%). | |
| `relative_humidity_2m_mean` | `float64` | 728 | 31.1957 | 99.2361 | 80.3665 | Độ ẩm tương đối không khí trung bình ngày ở độ cao 2m (%). | |
| `vapour_pressure_deficit_max` | `float64` | 728 | 0.0462 | 5.6280 | 1.5517 | Thâm hụt áp suất hơi nước lớn nhất trong ngày (chênh lệch giữa áp suất hơi bão hòa và thực tế) (kPa). | |
| `leaf_wetness_probability_mean` | `float64` | 728 | 0.0000 | 99.8214 | 46.9667 | Xác suất trung bình ngày có nước đọng trên bề mặt lá cây (%). | |
| `pressure_msl_mean` | `float64` | 728 | 989.9291 | 1037.6167 | 1010.5946 | Áp suất khí quyển trung bình ngày quy về mực nước biển (hPa). | |
| `surface_pressure_mean` | `float64` | 728 | 919.8801 | 1036.4668 | 1004.2512 | Áp suất khí quyển thực tế trung bình ngày tại cao độ của trạm (hPa). | |
| `wind_speed_10m_max` | `float64` | 728 | 3.6713 | 83.0259 | 15.7515 | Tốc độ gió cao nhất trong ngày đo ở độ cao 10 mét (km/h). | Giúp điền khuyết `MXSPD_kmh` theo Cross-source Fill. |
| `wind_gusts_10m_max` | `float64` | 728 | 8.2800 | 162.0000 | 33.5124 | Tốc độ gió giật mạnh nhất trong ngày ở độ cao 10 mét (km/h). | |
| `wind_direction_10m_dominant` | `float64` | 728 | 0.0000 | 360.0000 | 158.6144 | Hướng gió chủ đạo trong ngày ở độ cao 10m (0–360°, 360° là hướng Bắc). | |
| `wind_speed_10m_mean` | `float64` | 728 | 2.2893 | 43.2593 | 9.6347 | Tốc độ gió trung bình ngày ở độ cao 10m (km/h). | Được dùng để điền khuyết `WDSP_kmh` theo quy tắc Cross-source Fill. |
| `shortwave_radiation_sum` | `float64` | 728 | 0.8600 | 28.5200 | 16.4608 | Tổng năng lượng bức xạ mặt trời sóng ngắn nhận được trong ngày trên một mét vuông (MJ/m²). | |
| `cloud_cover_mean` | `float64` | 728 | 0.0000 | 100.0000 | 72.9429 | Tỷ lệ mây che phủ bầu trời trung bình ngày (%). | |
| `cloud_cover_max` | `float64` | 728 | 0.0000 | 100.0000 | 95.9022 | Tỷ lệ mây che phủ bầu trời lớn nhất trong ngày (%). | |
| `cloud_cover_min` | `float64` | 728 | 0.0000 | 100.0000 | 37.1157 | Tỷ lệ mây che phủ bầu trời nhỏ nhất trong ngày (%). | |
| `sunshine_duration` | `float64` | 728 | 0.0000 | 46,657.2300 | 30,566.5800 | Tổng số giây có ánh nắng mặt trời trực tiếp trong ngày. | |
| `daylight_duration` | `float64` | 728 | 38,927.3700 | 48,424.9260 | 43,702.9407 | Thời gian ban ngày tính từ lúc mặt trời mọc đến khi lặn (giây). | |
| `et0_fao_evapotranspiration` | `float64` | 728 | 0.2989 | 9.3381 | 3.6406 | Lượng thoát hơi nước tiềm năng chuẩn theo công thức FAO-56 Penman-Monteith (mm). | |
| `soil_moisture_0_to_7cm_mean` | `float64` | 728 | 0.0295 | 0.5171 | 0.3743 | Độ ẩm đất trung bình ngày ở tầng nông 0–7 cm (tỷ lệ thể tích nước/đất) (m³/m³). | |
| `soil_moisture_28_to_100cm_mean` | `float64` | 728 | 0.0702 | 0.5193 | 0.3764 | Độ ẩm đất trung bình ngày ở tầng rễ sâu 28–100 cm (m³/m³). | |
| `soil_moisture_0_to_100cm_mean` | `float64` | 728 | 0.1111 | 0.5171 | 0.3767 | Độ ẩm đất trung bình ngày toàn bộ tầng rễ sâu 1 mét (0–100 cm) (m³/m³). | |
| `soil_temperature_0_to_7cm_mean` | `float64` | 728 | 9.6210 | 39.7188 | 26.9406 | Nhiệt độ đất trung bình ngày ở tầng bề mặt 0–7 cm (°C). | |
| `weather_code` | `float64` | 728 | 0.0000 | 65.0000 | 43.0918 | Mã hiện tượng thời tiết theo chuẩn WMO (World Meteorological Organization). | |

---

### Nhóm 5: Biến Nhãn Mục tiêu (Target Variables)

*Biến phụ thuộc phục vụ các tác vụ Machine Learning. Chỉ gán nhãn khi `target_reliable == True`.*

| Tên Cột (Variable) | Kiểu Dữ Liệu | Null Count | Min | Max | Mean | Description | Source/Note |
| :--- | :--- | :---: | :--- | :--- | :--- | :--- | :--- |
| `target_reliable` | `object` | 728 | N/A | N/A | N/A | Biến logic xác thực độ tin cậy của dòng dữ liệu mưa. `True` khi trạm có thiết bị đo mưa và không dính lỗi hệ thống. | **Target Variable:** Dùng làm điều kiện lọc khi gán nhãn `rain_class` và `rain_binary`; cũng là điều kiện để điền khuyết `prcp_gsod_mm` từ Open-Meteo. |
| `rain_class` | `Int64` | 8,000 | 0.0000 | 2.0000 | 0.4151 | Nhãn phân lớp mưa đa lớp (Int64): Lớp 0 – không mưa (< 0.1 mm), Lớp 1 – mưa thường (0.1–50 mm), Lớp 2 – mưa cực đoan (≥ 50 mm). NA khi `target_reliable == False`. | **Target Variable:** Ngưỡng phân lớp theo chuẩn WMO. 8000 giá trị NA tương ứng với các dòng `target_reliable == False`. |
| `rain_binary` | `Int64` | 8,000 | 0.0000 | 1.0000 | 0.0698 | Biến nhị phân phụ trợ phân tách mưa lớn: 1 nếu `prcp_gsod_mm ≥ 25 mm`. Trả về NA khi `target_reliable == False`. | **Target Variable:** Phụ trợ trong mô hình hóa. 8000 giá trị NA tương ứng với các dòng `target_reliable == False`. |

---

### Nhóm 6: Biến Thời gian & Tuần hoàn (Temporal & Cyclical Features)

*Tất cả tạo tại Phase 8 từ cột `DATE`.*

| Tên Cột (Variable) | Kiểu Dữ Liệu | Null Count | Min | Max | Mean | Description | Source/Note |
| :--- | :--- | :---: | :--- | :--- | :--- | :--- | :--- |
| `year` | `int32` | 0 | 2015.0000 | 2024.0000 | 2019.5004 | Năm của ngày quan sát, trích xuất từ cột DATE. | Feature Engineer: bằng `dt.year`. Cột trung gian YEAR dùng để chia tập đã bị xóa sau khi hoàn tất phân chia. |
| `month` | `int32` | 0 | 1.0000 | 12.0000 | 6.5223 | Tháng của ngày quan sát (1–12), trích xuất từ cột DATE. | Feature Engineer: bằng `dt.month`. |
| `day_of_year` | `int32` | 0 | 1.0000 | 366.0000 | 183.1503 | Thứ tự ngày trong năm (1–366), trích xuất từ cột DATE. | Feature Engineer: bằng `dt.dayofyear`. |
| `month_sin` | `float64` | 0 | -1.0000 | 1.0000 | -0.0047 | Mã hóa vòng tuần hoàn tháng theo chiều sin: $\sin(2\pi \times \text{month} / 12)$, tránh ngắt quãng tại ranh giới tháng 12–1. | Feature Engineer |
| `month_cos` | `float64` | 0 | -1.0000 | 1.0000 | -0.0020 | Mã hóa vòng tuần hoàn tháng theo chiều cos: $\cos(2\pi \times \text{month} / 12)$, tránh ngắt quãng tại ranh giới tháng 12–1. | Feature Engineer |
| `doy_sin` | `float64` | 0 | -1.0000 | 1.0000 | 0.0000 | Mã hóa vòng tuần hoàn ngày trong năm theo chiều sin: $\sin(2\pi \times \text{day\_of\_year} / 365.25)$. | Feature Engineer |
| `doy_cos` | `float64` | 0 | -1.0000 | 1.0000 | 0.0001 | Mã hóa vòng tuần hoàn ngày trong năm theo chiều cos: $\cos(2\pi \times \text{day\_of\_year} / 365.25)$. | Feature Engineer |
| `is_monsoon` | `int64` | 0 | 0.0000 | 1.0000 | 0.4687 | Biến nhị phân xác định mùa mưa (1 = mùa mưa, 0 = mùa khô) dựa theo vùng khí hậu của trạm: Bắc (tháng 5–10), Trung (tháng 9–12), Nam (tháng 5–11). | Feature Engineer |
| `season_label` | `str` | 0 | N/A | N/A | N/A | | |

---

### Nhóm 7: Biến ENSO Ngoại sinh (Exogenous ENSO Variables)

*Nguồn: NOAA MEI (Multivariate ENSO Index). Tạo tại Phase 8.*

| Tên Cột (Variable) | Kiểu Dữ Liệu | Null Count | Min | Max | Mean | Description | Source/Note |
| :--- | :--- | :---: | :--- | :--- | :--- | :--- | :--- |
| `enso_mei_current` | `float64` | 0 | -2.1700 | 2.2400 | -0.1956 | Giá trị chỉ số MEI (Multivariate ENSO Index) của tháng/năm hiện tại, lấy từ NOAA. | Feature Engineer: Nguồn dữ liệu ngoại sinh: NOAA MEI. |
| `enso_mei_3m_lag` | `float64` | 0 | -2.1700 | 2.2400 | -0.1707 | Giá trị chỉ số MEI của 3 tháng trước đó, phản ánh trạng thái ENSO có độ trễ. | Feature Engineer: Nguồn dữ liệu ngoại sinh: NOAA MEI. |
| `enso_phase` | `str` | 0 | N/A | N/A | N/A | Chuỗi phân loại pha ENSO dựa trên `enso_mei_current`: `'el_nino'` (> 0.5), `'la_nina'` (< −0.5), `'neutral'` (còn lại). | |

---

### Nhóm 8: Biến Trễ Thời gian (Lag Features)

*Tất cả tạo tại Phase 8 bằng `.shift(k)` theo nhóm `STATION` sau khi sắp xếp tăng dần theo `DATE`. **7 hàng đầu tiên của mỗi trạm bị loại bỏ** (`MAX_LAG_K = 7`).*

| Tên Cột (Variable) | Kiểu Dữ Liệu | Null Count | Min | Max | Mean | Description | Source/Note |
| :--- | :--- | :---: | :--- | :--- | :--- | :--- | :--- |
| `prcp_gsod_mm_lag1` | `float64` | 773 | 0.0000 | 425.9580 | 5.8492 | Lượng mưa GSOD (mm) của ngày T−1 theo từng trạm. | Feature Engineer: bằng `.shift(1)` theo nhóm STATION sau khi sắp xếp tăng dần theo DATE. 7 hàng đầu tiên của mỗi trạm bị loại bỏ (MAX_LAG_K = 7). |
| `prcp_gsod_mm_lag2` | `float64` | 806 | 0.0000 | 425.9580 | 5.8521 | Lượng mưa GSOD (mm) của ngày T−2 theo từng trạm. | Feature Engineer: bằng `.shift(2)` theo nhóm STATION. 7 hàng đầu tiên của mỗi trạm bị loại bỏ. |
| `prcp_gsod_mm_lag3` | `float64` | 851 | 0.0000 | 425.9580 | 5.8539 | Lượng mưa GSOD (mm) của ngày T−3 theo từng trạm. | Feature Engineer: bằng `.shift(3)` theo nhóm STATION. 7 hàng đầu tiên của mỗi trạm bị loại bỏ. |
| `prcp_gsod_mm_lag7` | `float64` | 1,031 | 0.0000 | 425.9580 | 5.8623 | Lượng mưa GSOD (mm) của ngày T−7 theo từng trạm. | Feature Engineer: bằng `.shift(7)` theo nhóm STATION. 7 hàng đầu tiên của mỗi trạm bị loại bỏ. |
| `precipitation_sum_lag1` | `float64` | 773 | 0.0000 | 551.2000 | 5.8843 | Tổng lượng mưa Open-Meteo (mm) của ngày T−1 theo từng trạm. | Feature Engineer: bằng `.shift(1)` theo nhóm STATION. 7 hàng đầu tiên của mỗi trạm bị loại bỏ. |
| `precipitation_sum_lag3` | `float64` | 851 | 0.0000 | 551.2000 | 5.8889 | Tổng lượng mưa Open-Meteo (mm) của ngày T−3 theo từng trạm. | Feature Engineer: bằng `.shift(3)` theo nhóm STATION. 7 hàng đầu tiên của mỗi trạm bị loại bỏ. |
| `precipitation_sum_lag7` | `float64` | 1,031 | 0.0000 | 551.2000 | 5.8957 | Tổng lượng mưa Open-Meteo (mm) của ngày T−7 theo từng trạm. | Feature Engineer: bằng `.shift(7)` theo nhóm STATION. 7 hàng đầu tiên của mỗi trạm bị loại bỏ. |
| `relative_humidity_2m_mean_lag1` | `float64` | 773 | 31.1957 | 99.2361 | 80.3688 | Độ ẩm tương đối không khí trung bình ngày (%) của ngày T−1 theo từng trạm. | Feature Engineer: bằng `.shift(1)` theo nhóm STATION. 7 hàng đầu tiên của mỗi trạm bị loại bỏ. |
| `relative_humidity_2m_mean_lag3` | `float64` | 851 | 31.1957 | 99.2361 | 80.3717 | Độ ẩm tương đối không khí trung bình ngày (%) của ngày T−3 theo từng trạm. | Feature Engineer: bằng `.shift(3)` theo nhóm STATION. 7 hàng đầu tiên của mỗi trạm bị loại bỏ. |
| `dew_point_2m_mean_lag1` | `float64` | 773 | -4.9104 | 27.9833 | 21.5734 | Nhiệt độ điểm sương trung bình ngày (°C) của ngày T−1 theo từng trạm. | Feature Engineer: bằng `.shift(1)` theo nhóm STATION. 7 hàng đầu tiên của mỗi trạm bị loại bỏ. |
| `pressure_msl_mean_lag1` | `float64` | 773 | 989.9291 | 1037.6167 | 1010.5889 | Áp suất mực biển trung bình ngày (hPa) của ngày T−1 theo từng trạm. | Feature Engineer: bằng `.shift(1)` theo nhóm STATION. 7 hàng đầu tiên của mỗi trạm bị loại bỏ. |
| `cloud_cover_mean_lag1` | `float64` | 773 | 0.0000 | 100.0000 | 72.9422 | Tỷ lệ mây che phủ bầu trời trung bình ngày (%) của ngày T−1 theo từng trạm. | Feature Engineer: bằng `.shift(1)` theo nhóm STATION. 7 hàng đầu tiên của mỗi trạm bị loại bỏ. |
| `temperature_2m_mean_lag1` | `float64` | 773 | 5.6710 | 35.6938 | 25.4992 | Nhiệt độ không khí trung bình ngày (°C) của ngày T−1 theo từng trạm. | Feature Engineer: bằng `.shift(1)` theo nhóm STATION. 7 hàng đầu tiên của mỗi trạm bị loại bỏ. |
| `temperature_2m_min_lag1` | `float64` | 773 | 4.3085 | 31.6650 | 22.6435 | Nhiệt độ thấp nhất ngày (°C) của ngày T−1 theo từng trạm. | Feature Engineer: bằng `.shift(1)` theo nhóm STATION. 7 hàng đầu tiên của mỗi trạm bị loại bỏ. |

---

### Nhóm 9: Biến Cửa sổ Trượt (Rolling Window Features)

*Tất cả tạo tại Phase 8 bằng `.rolling(W).agg().shift(1)` theo nhóm `STATION`. Tham số `shift(1)` đảm bảo không rò rỉ thông tin ngày T vào cửa sổ tính toán.*

| Tên Cột (Variable) | Kiểu Dữ Liệu | Null Count | Min | Max | Mean | Description | Source/Note |
| :--- | :--- | :---: | :--- | :--- | :--- | :--- | :--- |
| `prcp_gsod_mm_roll3_sum` | `float64` | 1,634 | 0.0000 | 754.3800 | 17.5604 | Tổng lượng mưa GSOD (mm) tích lũy trong cửa sổ trượt 3 ngày trước ngày T (T−3 đến T−1). | Feature Engineer: bằng `.rolling(3).sum().shift(1)` theo nhóm STATION. `min_periods = ceil(3 × 0.7) = 3`. |
| `prcp_gsod_mm_roll7_sum` | `float64` | 730 | 0.0000 | 1,308.1000 | 40.6384 | Tổng lượng mưa GSOD (mm) tích lũy trong cửa sổ trượt 7 ngày trước ngày T. | Feature Engineer: bằng `.rolling(7).sum().shift(1)` theo nhóm STATION. `min_periods = ceil(7 × 0.7) = 5`. |
| `prcp_gsod_mm_roll14_sum` | `float64` | 791 | 0.0000 | 1,787.9060 | 81.2375 | Tổng lượng mưa GSOD (mm) tích lũy trong cửa sổ trượt 14 ngày trước ngày T. | Feature Engineer: bằng `.rolling(14).sum().shift(1)` theo nhóm STATION. `min_periods = 10`. Có 45 giá trị NA do thiếu lịch sử đầu chuỗi. |
| `prcp_gsod_mm_roll30_sum` | `float64` | 969 | 0.0000 | 2,090.9280 | 174.3487 | Tổng lượng mưa GSOD (mm) tích lũy trong cửa sổ trượt 30 ngày trước ngày T. | Feature Engineer: bằng `.rolling(30).sum().shift(1)` theo nhóm STATION. `min_periods = 21`. Có 210 giá trị NA do thiếu lịch sử đầu chuỗi. |
| `precipitation_sum_roll3_sum` | `float64` | 1,634 | 0.0000 | 625.5000 | 17.6816 | Tổng lượng mưa Open-Meteo (mm) tích lũy trong cửa sổ trượt 3 ngày trước ngày T. | Feature Engineer: bằng `.rolling(3).sum().shift(1)` theo nhóm STATION. `min_periods = 3`. |
| `precipitation_sum_roll7_sum` | `float64` | 730 | 0.0000 | 824.3000 | 40.8837 | Tổng lượng mưa Open-Meteo (mm) tích lũy trong cửa sổ trượt 7 ngày trước ngày T. | Feature Engineer: bằng `.rolling(7).sum().shift(1)` theo nhóm STATION. `min_periods = 5`. |
| `precipitation_sum_roll14_sum` | `float64` | 791 | 0.0000 | 1,307.3000 | 81.7368 | Tổng lượng mưa Open-Meteo (mm) tích lũy trong cửa sổ trượt 14 ngày trước ngày T. | Feature Engineer: bằng `.rolling(14).sum().shift(1)` theo nhóm STATION. `min_periods = 10`. Có 45 giá trị NA do thiếu lịch sử đầu chuỗi. |
| `relative_humidity_2m_mean_roll3_mean` | `float64` | 1,634 | 36.2074 | 98.3932 | 80.3800 | Độ ẩm tương đối không khí trung bình ngày (%) trung bình cửa sổ trượt 3 ngày trước ngày T. | Feature Engineer: bằng `.rolling(3).mean().shift(1)` theo nhóm STATION. `min_periods = 3`. |
| `relative_humidity_2m_mean_roll7_mean` | `float64` | 730 | 44.5491 | 96.8281 | 80.3704 | Độ ẩm tương đối không khí trung bình ngày (%) trung bình cửa sổ trượt 7 ngày trước ngày T. | Feature Engineer: bằng `.rolling(7).mean().shift(1)` theo nhóm STATION. `min_periods = 5`. |
| `cloud_cover_mean_roll3_mean` | `float64` | 1,634 | 0.0000 | 100.0000 | 73.0077 | Tỷ lệ mây che phủ bầu trời trung bình ngày (%) trung bình cửa sổ trượt 3 ngày trước ngày T. | Feature Engineer: bằng `.rolling(3).mean().shift(1)` theo nhóm STATION. `min_periods = 3`. |
| `cloud_cover_mean_roll7_mean` | `float64` | 730 | 4.8929 | 100.0000 | 72.9448 | Tỷ lệ mây che phủ bầu trời trung bình ngày (%) trung bình cửa sổ trượt 7 ngày trước ngày T. | Feature Engineer: bằng `.rolling(7).mean().shift(1)` theo nhóm STATION. `min_periods = 5`. |
| `soil_moisture_0_to_7cm_mean_roll7_mean` | `float64` | 730 | 0.0360 | 0.5139 | 0.3745 | Độ ẩm đất trung bình ngày ở tầng nông 0–7 cm (tỷ lệ thể tích nước/đất) (m³/m³) trung bình cửa sổ trượt 7 ngày trước ngày T. | Feature Engineer: bằng `.rolling(7).mean().shift(1)` theo nhóm STATION. `min_periods = 5`. |
| `wind_gusts_10m_max_roll3_max` | `float64` | 1,634 | 12.6000 | 162.0000 | 38.1774 | Tốc độ gió giật mạnh nhất trong ngày (km/h) trong cửa sổ trượt 3 ngày trước ngày T. | Feature Engineer: bằng `.rolling(3).max().shift(1)` theo nhóm STATION. `min_periods = 3`. |
| `temperature_2m_mean_roll7_std` | `float64` | 730 | 0.0446 | 6.1984 | 1.0455 | Độ lệch chuẩn nhiệt độ không khí trung bình ngày (°C) trong cửa sổ trượt 7 ngày trước ngày T, phản ánh mức độ biến động nhiệt. | Feature Engineer: bằng `.rolling(7).std().shift(1)` theo nhóm STATION. `min_periods = 5`. |
| `pressure_msl_mean_roll7_std` | `float64` | 730 | 0.1366 | 9.1656 | 1.7071 | Độ lệch chuẩn áp suất khí quyển trung bình ngày quy về mực nước biển (hPa) trong cửa sổ trượt 7 ngày trước ngày T, phản ánh biến động hình thế thời tiết. | Feature Engineer: bằng `.rolling(7).std().shift(1)` theo nhóm STATION. `min_periods = 5`. |

---

### Nhóm 10: Biến Phái sinh Vật lý & Khí tượng (Physics-Derived Features)

*Các biến được tính toán từ các công thức vật lý và nghiệp vụ khí tượng, tạo tại Phase 8.*

| Tên Cột (Variable) | Kiểu Dữ Liệu | Null Count | Min | Max | Mean | Description | Source/Note |
| :--- | :--- | :---: | :--- | :--- | :--- | :--- | :--- |
| `wet_bulb_depression` | `float64` | 728 | 0.0785 | 10.5004 | 2.7524 | Độ hụt nhiệt độ bầu ướt: `temperature_2m_mean` − `wet_bulb_temperature_2m_mean` (°C), phản ánh mức độ khô của không khí. | Feature Engineer |
| `saturation_deficit_proxy` | `float64` | 728 | -10.6500 | 12.2000 | 0.2830 | Đại diện cho độ hụt bão hòa: `dew_point_2m_max` − `temperature_2m_min` (°C). | Feature Engineer |
| `wind_dir_sin` | `float64` | 728 | -1.0000 | 1.0000 | 0.2033 | Mã hóa vòng tuần hoàn hướng gió chủ đạo theo chiều sin: $\sin(2\pi \times \text{wind\_direction\_10m\_dominant} / 360)$. | Feature Engineer |
| `wind_dir_cos` | `float64` | 728 | -1.0000 | 1.0000 | -0.0732 | Mã hóa vòng tuần hoàn hướng gió chủ đạo theo chiều cos: $\cos(2\pi \times \text{wind\_direction\_10m\_dominant} / 360)$. | Feature Engineer |
| `is_sw_wind` | `int64` | 0 | 0.0000 | 1.0000 | 0.2127 | Cờ nhị phân nhận diện gió mùa Tây Nam: 1 − hướng gió trong góc phần tư 180°–270° (`wind_dir_sin < 0` và `wind_dir_cos < 0`). | Feature Engineer |
| `sw_wind_strength` | `float64` | 728 | 0.0000 | 43.2593 | 2.1979 | Cường độ gió mùa Tây Nam: `is_sw_wind` × `wind_speed_10m_mean` (km/h). Bằng 0 khi không phải gió Tây Nam. | Feature Engineer |
| `wind_shear_proxy` | `float64` | 728 | 2.0158 | 74.2004 | 11.2627 | Đại diện cho độ đứt gió trong ngày: `wind_speed_10m_max` − `wind_speed_10m_min` (km/h). | Feature Engineer |
| `gust_factor` | `float64` | 728 | 1.8849 | 12.0495 | 3.7243 | Hệ số gió giật: $\frac{\text{wind\_gusts\_10m\_max}}{\text{wind\_speed\_10m\_mean} + 0.1}$, thể hiện mức độ đột biến tốc độ gió so với trung bình ngày. | Feature Engineer: Mẫu số cộng 0.1 để tránh chia cho 0. |
| `pressure_anomaly` | `float64` | 773 | -20.3024 | 18.6928 | -0.0089 | Độ lệch khí áp so với trung bình khí hậu 15 ngày xung quanh cùng ngày trong năm: `pressure_msl_mean_lag1` − `pressure_clim` (hPa). | Feature Engineer: Sử dụng `pressure_msl_mean_lag1` làm P_target để tránh rò rỉ dữ liệu; trung bình khí hậu được fit riêng trên tập train. |
| `et0_anomaly` | `float64` | 728 | -4.7875 | 4.8527 | 0.0348 | Độ lệch lượng bốc hơi tiềm năng so với trung bình khí hậu theo từng tháng và từng trạm: `et0_fao_evapotranspiration` − `et0_clim` (mm). | Feature Engineer: Trung bình khí hậu được fit riêng trên tập train theo nhóm `(STATION, month)`. |

---

### Nhóm 11: Biến Địa lý & Phân loại Vùng Khí hậu (Climate Zone Features)

*One-Hot Encoding các đặc trưng theo vùng khí hậu Köppen. Tất cả tạo tại Phase 8.*

| Tên Cột (Variable) | Kiểu Dữ Liệu | Null Count | Min | Max | Mean | Description | Source/Note |
| :--- | :--- | :---: | :--- | :--- | :--- | :--- | :--- |
| `coast_distance_km` | `int64` | 0 | 2.0000 | 120.0000 | 27.2667 | Khoảng cách ước tính từ trạm đến bờ biển gần nhất (km), tra bảng theo mã STATION. Gán mặc định 50 km nếu không tìm thấy. | Feature Engineer: Giá trị tra bảng tĩnh (lookup) từ COAST_DISTANCE_KM. |
| `koppen_Cwa` | `int64` | 0 | 0.0000 | 1.0000 | 0.2667 | Cờ nhị phân: 1 − thuộc khí hậu Köppen Cwa (cận nhiệt đới ẩm, mùa đông khô). | Feature Engineer: One-Hot Encoding theo vùng khí hậu Köppen của từng trạm. |
| `koppen_Am` | `int64` | 0 | 0.0000 | 1.0000 | 0.2667 | Cờ nhị phân: 1 − thuộc khí hậu Köppen Am (nhiệt đới gió mùa, tiêu biểu ở Đà Nẵng, Huế). | Feature Engineer: One-Hot Encoding theo vùng khí hậu Köppen của từng trạm. |
| `koppen_Aw` | `int64` | 0 | 0.0000 | 1.0000 | 0.4667 | Cờ nhị phân: 1 − thuộc khí hậu Köppen Aw (nhiệt đới xavan, tiêu biểu ở TP.HCM, Cần Thơ). | Feature Engineer: One-Hot Encoding theo vùng khí hậu Köppen của từng trạm. |

---

## 3. Sơ đồ Nguồn gốc Dữ liệu (Data Provenance Summary)

```
GSOD (NOAA/USAF)          Open-Meteo (ERA5)          NOAA MEI
       │                         │                        │
       ▼                         ▼                        ▼
  Sentinel → NaN           Không có NaN            Join theo (year, month)
  Unit conversion          (full coverage)                 │
       │                         │                        │
       └──────────┬──────────────┘                        │
                  ▼                                        │
         Cross-Source Imputation                          │
         (GSOD ← Open-Meteo khi                          │
          target_reliable == True)                        │
                  │                                        │
                  ▼                                        │
            MICE (BayesianRidge)                          │
            fit trên tập TRAIN                            │
            (ZERO DATA LEAKAGE)                           │
                  │                                        │
                  └──────────────┬────────────────────────┘
                                 ▼
                    Feature Engineering (Phase 8)
                    Lag / Rolling / Physics / Köppen
                                 │
                                 ▼
                      vietnam_weather_benchmark.csv
                      (105 cột, ~43,000+ bản ghi)
```

---

## 4. Lưu ý Quan trọng về Data Leakage

> ⚠️ **CẢNH BÁO:** Các biến `pressure_anomaly` và `et0_anomaly` sử dụng trung bình khí hậu được **fit riêng trên tập train** theo từng nhóm. Khi sử dụng dataset này để huấn luyện mô hình, người dùng cần tái tạo các trung bình khí hậu từ tập train của mình và áp dụng lên tập test, **không được dùng trung bình từ toàn bộ dataset.**

> ⚠️ Các cột `prcp_gsod_mm_roll14_sum` và `prcp_gsod_mm_roll30_sum` có Null Count lần lượt là **791** và **969** (bao gồm cả 728 dòng thiếu trạm + NA do thiếu lịch sử đầu chuỗi). Cần xử lý trước khi đưa vào mô hình.