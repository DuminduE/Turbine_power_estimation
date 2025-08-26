# Wind Turbine_power_estimation
Estimation of Wind Turbine Power Output from SCADA Data (Vensys 82 machine) using Weibull Distribution and Spline-Interpolated Power Curve

## Overview
This project estimates wind turbine power output using SCADA data by reconstructing wind speed distributions with Weibull statistics and applying cubic spline-interpolated turbine power curves. The model provides a performance benchmark by comparing predicted and actual turbine output.

---

## 1. Introduction
Wind turbine SCADA systems record operational data every 10 minutes, including:

- Average, minimum, and maximum wind speeds  
- Wind speed standard deviation  
- Turbine power output  

SCADA averages do not reflect the true wind distribution within each 10-minute interval. Since turbine power output is highly nonlinear with respect to wind speed, simply using average wind speed can misrepresent expected generation.

This project develops a Python model that:

- Reconstructs wind speed distributions using Weibull statistics  
- Uses cubic spline interpolation of the manufacturer’s power curve to estimate expected power  
- Compares predicted output with actual SCADA-measured power to calculate efficiency ratios  

---

## 2. Data Input
The script processes a CSV file exported from the turbine SCADA system.  
**Required variables (column indexes based on SCADA export format):**

| Variable | Column Index | Renamed As |
|----------|--------------|------------|
| Average power | 1 | avg_power |
| Average wind speed | 4 | windspeed_avg |
| Maximum wind speed | 5 | wind_speed_max |
| Minimum wind speed | 6 | wind_speed_min |
| 10-minute power production | 66 | power_production_10m |
| Wind speed standard deviation | 88 | wind_speed_std_dev |

⚠️ Column positions are specific to the SCADA file format. In the GitHub repo, the CSV is **anonymized**.

Interactive environment for single input ( one data interval) : 
[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/<username>/turbine-power-estimation/blob/main/demo.ipynb)

---

## 3. Methodology

### 3.1 Data Cleaning
- Converted key columns to numeric values.  
- Excluded intervals where `power_production_10m < 600` (turbine not producing energy).

### 3.2 Weibull Distribution Estimation
- Derived Weibull shape parameter (k) from standard deviation to mean wind speed ratio.  
- Calculated scale parameter (λ).  
- Generated 600 synthetic wind speed samples per interval, constrained by SCADA min/max speeds.

### 3.3 Power Curve Interpolation
- Manufacturer’s power curve provided at discrete points.  
- Cubic Spline interpolation created a smooth curve over the full operating range.

### 3.4 Power & Energy Estimation
For each sampled wind speed:

- Interpolated expected power output  
- Calculated for each interval:
  - Predicted average power (kW)  
  - Predicted energy (kWh)  
  - Efficiency ratio (%) = (actual ÷ predicted average power) × 100

### 3.5 Output
- Enriched CSV with predicted values and efficiency ratios
- Summary row at bottom with overall average efficiency  

---

## 4. Example Console Output:

Successfully loaded 'DLRDL-08_m250729_anonymized.csv' with 144 rows.
Filtered out 12 rows where 'power_production_10m' < 600.

--- Summary ---
Average Assumed Power Production Percentage (for filtered data): 94.28%

## 5. Visualizations
- Weibull distribution reconstruction for a 10-minute interval
  <img width="1389" height="590" alt="image" src="https://github.com/user-attachments/assets/0b7d343e-7aa2-421b-8861-df33f08cbb67" />
  
- Power curve interpolation – discrete points vs cubic spline
  <img width="705" height="590" alt="image" src="https://github.com/user-attachments/assets/8671bfd6-5047-469d-9bbb-8a01f31f1dbb" />
 
- Actual vs predicted average power (scatter plot or time series)  


---

## 6. Applications
- **Performance Benchmarking:** Compare actual production to theoretical turbine output
  <img width="713" height="267" alt="image" src="https://github.com/user-attachments/assets/4ddcc938-1391-48b0-ae94-c1814628e625" />
 
- **Underperformance Detection:** Highlight low-efficiency intervals
  <img width="712" height="267" alt="image" src="https://github.com/user-attachments/assets/f6efe9df-7c71-4473-9f63-011d710d4325" />

  

---

## 7. Technologies Used
- Python: `pandas`, `NumPy`, `SciPy`, `CubicSpline`  
- Statistical Modeling: Weibull distribution fitting  
- Data Engineering: SCADA preprocessing, filtering, validation  

---

## 8. Usage
Install dependencies:
```bash
pip install pandas numpy scipy matplotlib
```
### Interactive Notebook

You can run the interactive demo in the browser without installing anything:
- **[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/<username>/turbine-power-estimation/blob/main/demo.ipynb)** Click the badge above to open `demo.ipynb` with interactive sliders and plots.  
- **Binder:** Click the badge to launch a temporary Jupyter environment with all dependencies installed.

**Features:**

- Input mean, std deviation, min/max wind speeds
- Generate Weibull-distributed wind speed samples
- Estimate expected turbine power and energy
- Visualize distribution and expected power output
