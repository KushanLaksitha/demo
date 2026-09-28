# AgriSense — AI-Driven Vegetable Production & Price Optimization System

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/framework-Kivy%20%7C%20KivyMD-green.svg)](https://kivymd.readthedocs.io/)
[![Database](https://img.shields.io/badge/database-MySQL%20%7C%20SQLAlchemy-orange.svg)](https://www.mysql.com/)
[![Deep Learning & ML](https://img.shields.io/badge/ML%20%26%20DL-TensorFlow%20%7C%20Keras%20%7C%20Scikit--Learn%20%7C%20Statsmodels-brightgreen.svg)](https://www.tensorflow.org/)
[![License](https://img.shields.io/badge/license-MIT-lightgrey.svg)](LICENSE)

**AgriSense** is an advanced, AI-driven mobile and desktop application tailored for Sri Lanka's agricultural ecosystem. The system leverages state-of-the-art **Deep Learning LSTM (Long Short-Term Memory)** neural networks for crop price forecasting, **Random Forest Regressors** for seasonal harvest yields, **SARIMA** seasonal time-series decomposition, and **Rolling Z-Score** anomaly detection to deliver real-time market intelligence and early warning alerts for **Farmers**, **Traders**, **Policymakers**, and **System Administrators**.

> ### 🚀 Model Architecture & Performance Upgrade (2021–2025 Dataset)
> The machine learning pipeline has been upgraded with the verified 2021–2025 Sri Lankan agricultural dataset in [`AgriSense_Model_Training_Export.ipynb`](AgriSense_Model_Training_Export.ipynb) using [`AgriSense_Dataset_2021_2025_Cleaned.xlsx`](AgriSense_Dataset_2021_2025_Cleaned.xlsx). 
> 
> By deploying specialized **LSTM Deep Learning models** (13-week lookback windows with sequential feature extraction), **Random Forest ensemble regressors** for seasonal production volume ($R^2 \approx 0.87$), **52-week SARIMA seasonal decomposition**, and dynamic **Z-score volatility monitoring**, AgriSense provides high-accuracy predictive intelligence packaged directly into [`agrisense_export/`](agrisense_export/) for production deployment.

---

## 📋 Table of Contents

- [Screenshots](#-screenshots)
- [Exploratory Data Analysis (EDA)](#-exploratory-data-analysis-eda--market-insights)
- [Machine Learning Architecture & Evaluation](#-machine-learning-architecture--model-evaluation)
- [Overview & Key Features](#-overview--key-features)
- [System Architecture](#-system-architecture)
- [Technology Stack](#-technology-stack)
- [Project Directory Structure](#-project-directory-structure)
- [Prerequisites](#-prerequisites)
- [Installation & Setup](#-installation--setup)
- [Database Setup & Seeding](#-database-setup--seeding)
- [Email Confirmation Endpoint](#-email-confirmation-endpoint)
- [Running the Application](#-running-the-application)
- [Demo User Credentials](#-demo-user-credentials)
- [Android APK Build Guide](#-android-apk-build-guide-buildozer)
- [Database Schema & Migrations](#-database-schema--migrations)
- [Codebase Functions & Scripts Index](#-codebase-functions--scripts-index)
- [Author & License](#-author--license)

---

## 📸 Screenshots

### 🔐 Authentication & Onboarding

| Login Screen | Crop Selection |
|:---:|:---:|
| ![Login Screen](screenshot/Homepage.png) | ![Crop Selection](screenshot/editCrops.png) |

### 📊 Role-Based Dashboards

| Admin Dashboard | Farmer Dashboard |
|:---:|:---:|
| ![Admin Dashboard](screenshot/dashboard-admin.png) | ![Farmer Dashboard](screenshot/dashboard-farmer.png) |

| Policymaker Dashboard | Trader Dashboard |
|:---:|:---:|
| ![Policymaker Dashboard](screenshot/dashboard-policymaker.png) | ![Trader Dashboard](screenshot/dashboard-trader.png) |

### 🔔 Insights & Alerts

| For You — Recommendations | Alerts |
|:---:|:---:|
| ![For You](screenshot/forYou.png) | ![Alerts](screenshot/alerts.png) |

### 📈 History & Analytics

| Beans — Price Trend (16 Weeks) | Beans — Production Volume (16 Weeks) |
|:---:|:---:|
| ![Price History](screenshot/history-beans-price.png) | ![Production History](screenshot/history=beans-production.png) |

### 👤 Profile & Settings

| Profile | Edit Profile | Feedback |
|:---:|:---:|:---:|
| ![Profile](screenshot/profile.png) | ![Edit Profile](screenshot/editprofile.png) | ![Feedback](screenshot/feedback.png) |

---

## 📈 Exploratory Data Analysis (EDA) & Market Dynamics

Exploratory Data Analysis was performed on the cleaned multi-year Sri Lankan agricultural dataset (2021–2025) spanning wholesale prices, seasonal harvest yields, and climate indicators across key production districts (Kandy & Matale). Visualizations are exported directly to [`agrisense_export/graphs/`](agrisense_export/graphs/):

### 1. 📉 Historical Weekly Wholesale Price Trends (2021–2025)

Multi-year wholesale price trajectories (LKR/kg) for the five core vegetable commodities across Kandy and Matale districts, illustrating seasonal pricing dynamics and multi-year inflation trends:

| Crop | Historical Price Trend (2021–2025) |
| :--- | :--- |
| **Beans** | ![Beans Price Trend](agrisense_export/graphs/price_trend_beans.png) |
| **Cabbage** | ![Cabbage Price Trend](agrisense_export/graphs/price_trend_cabbage.png) |
| **Carrots** | ![Carrots Price Trend](agrisense_export/graphs/price_trend_carrots.png) |
| **Leeks** | ![Leeks Price Trend](agrisense_export/graphs/price_trend_leeks.png) |
| **Okra** | ![Okra Price Trend](agrisense_export/graphs/price_trend_okra.png) |

---

### 2. 🌾 Seasonal Production Volume by Crop & Season (2021–2025)

Seasonal production volume (Metric Tons) across consecutive *Maha* and *Yala* cultivation seasons, showing seasonal supply cycles and output distribution:

| Crop | Seasonal Production Volume (Mt) |
| :--- | :--- |
| **Beans** | ![Beans Production Volume](agrisense_export/graphs/production_volume_beans.png) |
| **Cabbage** | ![Cabbage Production Volume](agrisense_export/graphs/production_volume_cabbage.png) |
| **Carrots** | ![Carrots Production Volume](agrisense_export/graphs/production_volume_carrots.png) |
| **Leeks** | ![Leeks Production Volume](agrisense_export/graphs/production_volume_leeks.png) |
| **Okra** | ![Okra Production Volume](agrisense_export/graphs/production_volume_okra.png) |

---

### 3. 🌡️ Market Volatility & Production Drivers

| Price Volatility Heatmap (Month vs. Crop) | Random Forest Production Feature Importance |
| :---: | :---: |
| ![Price Volatility Heatmap](agrisense_export/graphs/price_volatility_heatmap.png) | ![Production Feature Importance](agrisense_export/graphs/production_feature_importance.png) |
| **Monthly Price Volatility**: Highlights standard deviation of prices by month, revealing peak volatility during festive and inter-monsoon seasons. | **Production Feature Importance**: Confirms `Cultivated Area (ha)` and previous season's production (`prod_lag_1`) as primary yield determinants. |

---

## 🤖 Machine Learning Architecture & Model Evaluation

AgriSense uses a production-ready, multi-paradigm Machine Learning and Deep Learning pipeline designed in [`AgriSense_Model_Training_Export.ipynb`](AgriSense_Model_Training_Export.ipynb):
1. **Price Forecasting Engine**: Deep Learning **LSTM (Long Short-Term Memory)** neural networks trained per crop.
2. **Production Forecasting Engine**: Non-linear **Random Forest Regressor** predicting seasonal crop yields.
3. **Seasonal Decomposition & Forecasting**: **SARIMA** modeling capturing 52-week annual cycles and generating confidence-bounded projections.
4. **Market Anomaly & Alert Engine**: Dynamic **Rolling Z-Score** monitoring for price surge and collapse alerts.

---

### 🧠 1. Price Forecasting: Deep Learning LSTM Neural Networks

To capture complex temporal dependencies, non-linear market shocks, and seasonal momentum, vegetable wholesale prices are modeled using multi-layer **LSTM** architectures trained individually on 2021–2025 price sequences.

#### 🏗 Model Architecture & Feature Engineering
- **Input Lookback Horizon**: 13 weeks ($\approx 90$ days) of sequential history.
- **Input Feature Dimension**: 11 features per time step:
  - `Price (Rs/kg)` (target lag 0)
  - `ma_4`: 4-week short-term moving average
  - `ma_12`: 12-week medium-term moving average
  - `lag_1`, `lag_4`: 1-week and 4-week autoregressive lags
  - `yoy_change`: Year-over-year price growth rate (52-week shift)
  - `District_enc`: District label encoding (Kandy / Matale)
  - `Season_enc`: Seasonal cycle encoding (Maha / Yala)
  - `month`: Calendar month (1–12)
  - `week_sin`, `week_cos`: Cyclical sinusoidal calendar features ($\sin(2\pi \cdot \text{week}/52)$, $\cos(2\pi \cdot \text{week}/52)$)
- **Neural Network Topology**:
  - `LSTM Layer 1`: 64 memory units with `return_sequences=True`
  - `Dropout Layer 1`: 20% dropout rate for regularization
  - `LSTM Layer 2`: 32 memory units with `return_sequences=False`
  - `Dropout Layer 2`: 20% dropout rate
  - `Dense Layer 1`: 16 units with ReLU activation
  - `Output Layer`: 1 unit with Linear activation (scaled price)
  - `Optimizer & Loss`: Adam optimizer ($\eta = 0.001$), Mean Squared Error (`MSE`) loss, early stopping with best weight restoration.

#### 📊 LSTM Price Model Performance Evaluation

Evaluated on held-out test split (20% sequence holdout):

| Crop | RMSE (Rs/kg) | MAE (Rs/kg) | MAPE (%) | Directional Accuracy (%) | Model Artifact | Scaler Artifact |
| :--- | :---: | :---: | :---: | :---: | :--- | :--- |
| **Beans** | 129.43 | 105.14 | 37.73% | 44.94% | [`price_lstm_beans.keras`](agrisense_export/models/price_lstm_beans.keras) | [`price_scaler_beans.pkl`](agrisense_export/scalers/price_scaler_beans.pkl) |
| **Cabbage** | 58.85 | 47.99 | 31.35% | 44.94% | [`price_lstm_cabbage.keras`](agrisense_export/models/price_lstm_cabbage.keras) | [`price_scaler_cabbage.pkl`](agrisense_export/scalers/price_scaler_cabbage.pkl) |
| **Carrots** | 123.64 | 104.98 | 51.44% | 53.93% | [`price_lstm_carrots.keras`](agrisense_export/models/price_lstm_carrots.keras) | [`price_scaler_carrots.pkl`](agrisense_export/scalers/price_scaler_carrots.pkl) |
| **Leeks** | 84.27 | 55.65 | 25.78% | 50.56% | [`price_lstm_leeks.keras`](agrisense_export/models/price_lstm_leeks.keras) | [`price_scaler_leeks.pkl`](agrisense_export/scalers/price_scaler_leeks.pkl) |
| **Okra** | 35.70 | 29.54 | 32.31% | 43.82% | [`price_lstm_okra.keras`](agrisense_export/models/price_lstm_okra.keras) | [`price_scaler_okra.pkl`](agrisense_export/scalers/price_scaler_okra.pkl) |

#### 📈 LSTM Training Loss Curves & Forecast vs Actual

| Crop | Training Loss Curve (MSE) | Forecast vs Actual (Test Set) |
| :--- | :---: | :---: |
| **Beans** | ![Beans Loss](agrisense_export/graphs/price_loss_curve_beans.png) | ![Beans Forecast vs Actual](agrisense_export/graphs/price_forecast_vs_actual_beans.png) |
| **Cabbage** | ![Cabbage Loss](agrisense_export/graphs/price_loss_curve_cabbage.png) | ![Cabbage Forecast vs Actual](agrisense_export/graphs/price_forecast_vs_actual_cabbage.png) |
| **Carrots** | ![Carrots Loss](agrisense_export/graphs/price_loss_curve_carrots.png) | ![Carrots Forecast vs Actual](agrisense_export/graphs/price_forecast_vs_actual_carrots.png) |
| **Leeks** | ![Leeks Loss](agrisense_export/graphs/price_loss_curve_leeks.png) | ![Leeks Forecast vs Actual](agrisense_export/graphs/price_forecast_vs_actual_leeks.png) |
| **Okra** | ![Okra Loss](agrisense_export/graphs/price_loss_curve_okra.png) | ![Okra Forecast vs Actual](agrisense_export/graphs/price_forecast_vs_actual_okra.png) |

---

### 🌲 2. Production Forecasting: Random Forest Regressor

Seasonal crop yield (Metric Tons) is predicted using an optimized **Random Forest Regressor** trained on historical agricultural production statistics.

#### ⚙️ Model Configuration & Metrics
- **Hyperparameters**: `n_estimators=150`, `max_depth=15`, `min_samples_split=5`, `min_samples_leaf=2`, `random_state=42`.
- **Input Features**: `Veg_enc`, `Dist_enc`, `Year`, `Season_enc` (*Maha=0, Yala=1*), `Cultivated Area (ha)`, `prod_lag_1` (*previous season production volume*).
- **Target**: `Production Volume (Mt)`.
- **Performance**:
  - **$R^2$ Score**: **0.8699** ($\approx 87\%$ of harvest variance explained)
  - **RMSE**: **411.65 Mt**
  - **MAE**: **284.06 Mt**
  - **MAPE**: **41.43%**
  - **Model Bias**: **+29.11%**

| Production Forecast vs Actual (Scatter) | Production Feature Importance |
| :---: | :---: |
| ![Production Forecast vs Actual](agrisense_export/graphs/production_forecast_vs_actual.png) | ![Production Feature Importance](agrisense_export/graphs/production_feature_importance.png) |

- **Model Artifacts**: [`agrisense_export/models/production_rf.pkl`](agrisense_export/models/production_rf.pkl) and [`agrisense_export/models/production_rf_features.pkl`](agrisense_export/models/production_rf_features.pkl).

---

### 📅 3. Seasonal Trend Decomposition & Forecasting: SARIMA

To validate long-term macroeconomic trends and cyclical oscillations, an additive **SARIMA(1, 1, 1)(1, 1, 1, 52)** model decomposes weekly vegetable prices into trend, 52-week seasonality, and residual stochastic variations, providing 8-week probabilistic forward forecasts:

| Crop | Seasonal Decomposition (Trend, Season, Residuals) | SARIMA 8-Week Forecast with Confidence Interval | Akaike Information Criterion (AIC) |
| :--- | :---: | :---: | :---: |
| **Beans** | ![Beans SARIMA Decomp](agrisense_export/graphs/sarima_decomposition_beans.png) | ![Beans SARIMA Forecast](agrisense_export/graphs/sarima_forecast_beans.png) | 817.98 |
| **Cabbage** | ![Cabbage SARIMA Decomp](agrisense_export/graphs/sarima_decomposition_cabbage.png) | ![Cabbage SARIMA Forecast](agrisense_export/graphs/sarima_forecast_cabbage.png) | 496.25 |
| **Carrots** | ![Carrots SARIMA Decomp](agrisense_export/graphs/sarima_decomposition_carrots.png) | ![Carrots SARIMA Forecast](agrisense_export/graphs/sarima_forecast_carrots.png) | -121.37 |
| **Leeks** | ![Leeks SARIMA Decomp](agrisense_export/graphs/sarima_decomposition_leeks.png) | ![Leeks SARIMA Forecast](agrisense_export/graphs/sarima_forecast_leeks.png) | -40.60 |
| **Okra** | ![Okra SARIMA Decomp](agrisense_export/graphs/sarima_decomposition_okra.png) | ![Okra SARIMA Forecast](agrisense_export/graphs/sarima_forecast_okra.png) | 636.43 |

---

### 🚨 4. Price Volatility & Anomaly Alert Engine (Rolling Z-Score)

AgriSense includes a real-time statistical anomaly detection engine running directly on device. It computes a 13-week ($\approx 90$ day) rolling mean ($\mu$) and rolling standard deviation ($\sigma$) to calculate the standardized Z-score:
$$Z = \frac{P_t - \mu_{13}}{\sigma_{13}}$$

#### Severity Thresholds:
- **Normal**: $|Z| < 2.0$ (Standard market fluctuation)
- **Medium Alert**: $2.0 \le |Z| < 2.5$ (Elevated price movement)
- **High Alert**: $2.5 \le |Z| < 3.0$ (Significant price surge / crash)
- **Critical Alert**: $|Z| \ge 3.0$ (Severe supply shock or market distortion)

| Crop | Alerts Triggered (2021–2025) | Z-Score Anomaly Monitor Graph |
| :--- | :---: | :--- |
| **Beans** | 17 | ![Beans Z-Score](agrisense_export/graphs/zscore_alerts_beans.png) |
| **Cabbage** | 20 | ![Cabbage Z-Score](agrisense_export/graphs/zscore_alerts_cabbage.png) |
| **Carrots** | 26 | ![Carrots Z-Score](agrisense_export/graphs/zscore_alerts_carrots.png) |
| **Leeks** | 18 | ![Leeks Z-Score](agrisense_export/graphs/zscore_alerts_leeks.png) |
| **Okra** | 25 | ![Okra Z-Score](agrisense_export/graphs/zscore_alerts_okra.png) |

---

### 📦 5. Exported ML Pipeline Assets (`agrisense_export/`)

The automated pipeline exports all assets directly for native KivyMD application integration:
```
agrisense_export/
├── data/
│   └── mobile_export.json              # Pre-calculated next-week price forecasts & metrics
├── graphs/                             # 38 high-resolution analytical PNG plots
├── models/
│   ├── price_lstm_beans.keras          # Trained LSTM price model for Beans
│   ├── price_lstm_cabbage.keras        # Trained LSTM price model for Cabbage
│   ├── price_lstm_carrots.keras        # Trained LSTM price model for Carrots
│   ├── price_lstm_leeks.keras          # Trained LSTM price model for Leeks
│   ├── price_lstm_okra.keras           # Trained LSTM price model for Okra
│   ├── production_rf.pkl               # Random Forest seasonal production model
│   └── production_rf_features.pkl      # Feature column names for production inference
└── scalers/
    ├── price_scaler_beans.pkl          # MinMaxScaler for Beans features
    ├── price_scaler_cabbage.pkl        # MinMaxScaler for Cabbage features
    ├── price_scaler_carrots.pkl        # MinMaxScaler for Carrots features
    ├── price_scaler_leeks.pkl          # MinMaxScaler for Leeks features
    └── price_scaler_okra.pkl           # MinMaxScaler for Okra features
```

#### Inference Code Example:
```python
import joblib
import numpy as np
import tensorflow as tf

# 1. Load trained LSTM price model and scaler for Carrots
model = tf.keras.models.load_model("agrisense_export/models/price_lstm_carrots.keras")
scaler = joblib.load("agrisense_export/scalers/price_scaler_carrots.pkl")

# 2. Prepare 13-week lookback feature sequence (13 timesteps x 11 features)
# [Price, ma_4, ma_12, lag_1, lag_4, yoy_change, District_enc, Season_enc, month, week_sin, week_cos]
sample_sequence = np.random.rand(13, 11)  # replace with actual historical weekly values
scaled_sequence = scaler.transform(sample_sequence)

# 3. Predict scaled price for next week and invert scaling
scaled_pred = model.predict(scaled_sequence.reshape(1, 13, 11), verbose=0)[0][0]
dummy = np.zeros((1, 11))
dummy[0, 0] = scaled_pred
predicted_price = float(scaler.inverse_transform(dummy)[0, 0])
print(f"Predicted Carrots Price: Rs. {predicted_price:.2f} / kg")

# 4. Load Random Forest Production model
rf_model = joblib.load("agrisense_export/models/production_rf.pkl")
# Features: [Veg_enc, Dist_enc, Year, Season_enc, Cultivated Area (ha), prod_lag_1]
pred_prod = rf_model.predict([[0, 0, 2026, 0, 150.0, 2200.0]])[0]
print(f"Predicted Harvest Output: {pred_prod:.2f} Mt")
```

---

## ✨ Overview & Key Features

AgriSense addresses agricultural market volatility and crop overproduction/shortage issues through data intelligence.

### 🌟 Key Highlights

- **Role-Based Dashboards**: Customized interface tailored to user persona:
  - **Farmer**: Harvest planning, yield forecasts, market price trends, crop recommendations, and alert notifications.
  - **Trader**: Wholesale price projections, regional crop availability, price spike alerts, and market supply analytics.
  - **Policymaker**: National production trends, regional supply balance, climate impact monitoring, and policy recommendations.
  - **Admin**: User management, database seeding overview, system analytics, and user feedback monitoring with average rating metrics.
- **AI/ML Forecasting Engine**: Production-ready **Deep Learning LSTM** models for vegetable market prices, **Random Forest** for seasonal crop yields, **SARIMA** seasonal decomposition, and **Rolling Z-Score** anomaly alerts.
- **Date Search & Market Records Inspector**: Interactive calendar picker enabling users to inspect actual wholesale prices (Rs/kg) and seasonal production outputs (Mt) for any market date between 2021 and 2025, alongside forward-looking AI model predictions.
- **Dedicated Price & Production History Screen**: Comprehensive full-screen historical analysis with dynamic date pickers, tabbed crop selection, and synchronized AI price/yield forecasting cards.
- **Interactive Visualizations**: Dynamic Matplotlib charts rendered seamlessly within KivyMD views for intuitive data analysis.
- **Smart Notification System**: Automated alert generation for price spikes, sharp market drops, regional oversupply, and crop shortages.
- **Email Verification Flow**: Secure user registration with bcrypt password hashing and tokenized email confirmation (via SMTP and Flask).
- **Password Strength & Crop Selection**: Built-in real-time password strength validation and seamless favourite crop onboarding.
- **5-Star Rating & Feedback Hub**: Direct feedback pipeline connecting users with platform administrators featuring star rating summaries.
- **Enhanced Visual UX**: Animated splash screen with growing sprout logo, smooth slide transitions, and staggered card animations.

---

## 🏗 System Architecture

```
                                +---------------------------+
                                |      AgriSense App        |
                                |  (KivyMD Mobile / Desktop)|
                                +-------------+-------------+
                                              |
                   +--------------------------+--------------------------+
                   |                                                     |
        +----------v----------+                               +----------v----------+
        |   Auth & Security   |                               |  Data Visualization |
        | (bcrypt, SMTP, Auth)|                               |  (Matplotlib Charts)|
        +----------+----------+                               +----------+----------+
                   |                                                     |
                   +--------------------------+--------------------------+
                                              |
                                +-------------v-------------+
                                |    SQLAlchemy ORM Layer   |
                                +-------------+-------------+
                                              |
                                +-------------v-------------+
                                |     MySQL Database        |
                                |      (vectamind_db)       |
                                +-------------+-------------+
                                              ^
                                              |
                   +--------------------------+--------------------------+
                   |                                                     |
        +----------+----------+                               +----------+----------+
        |  ML Model Pipelines |                               | Flask Confirm Server|
        | (LSTM / RF / SARIMA)|                               | (Email Token Auth)  |
        +---------------------+                               +---------------------+
```

---

## 🛠 Technology Stack

- **User Interface**: [Kivy 2.3.0](https://kivy.org/), [KivyMD 1.2.0](https://kivymd.readthedocs.io/)
- **Backend Architecture**: Python 3.10+, SQLAlchemy ORM, PyMySQL
- **Database**: MySQL Server 8.0+
- **Deep Learning & Machine Learning**: TensorFlow / Keras 2.16+, Scikit-Learn 1.6+, Statsmodels 0.14+, Joblib, Pandas, NumPy
- **Data Visualization**: Matplotlib, Seaborn, `kivy-garden.matplotlib`
- **Security & Authentication**: `bcrypt`, `python-dotenv`, SMTP protocol
- **Microservice / Utility**: Flask (Account verification server)
- **Mobile Packaging**: Buildozer, Cython (Android APK target)

---

## 📁 Project Directory Structure

```
AgriSense/
│
├── main.py                              # Main application entry point & screen manager
├── requirements.txt                     # Python dependencies specification
├── buildozer.spec                       # Android APK build configuration
├── .env.example                         # Template for environment variables
├── .gitignore                           # Git exclusion rules
├── README.md                            # Comprehensive project documentation
├── AgriSense_Dataset_2021_2025_Cleaned.xlsx # Multi-year cleaned agricultural dataset
├── AgriSense_Model_Training_Export.ipynb# Jupyter notebook for LSTM, RF & SARIMA training
│
├── agrisense_export/                    # Exported ML pipeline outputs & deployment assets
│   ├── models/                          # Trained models (.keras LSTM and .pkl RF models)
│   ├── scalers/                         # Feature MinMaxScalers (.pkl) per vegetable
│   ├── graphs/                          # 38 EDA, loss curves, forecast & alert PNG plots
│   └── data/                            # mobile_export.json (precomputed forecasts & metrics)
│
├── database/                            # Database & ORM module
│   ├── schema.sql              # Complete MySQL database schema
│   ├── migration_add_rating.sql# Database migration script for feedback ratings
│   ├── db_connection.py        # SQLAlchemy engine & session factory
│   ├── models.py               # ORM data models (User, Crop, Price, Alert, etc.)
│   ├── data_service.py         # Data access queries & UI data formatting
│   ├── auth_service.py         # Registration, authentication & token verification
│   ├── import_excel_dataset.py # Imports verified 2021-2025 Excel dataset into MySQL
│   ├── seed_demo_data.py       # Seeds verified 2021-2025 dataset and demo user accounts
│   └── confirm_server.py       # Flask server handling email link verification
│
├── screens/                    # KivyMD UI Screen Components
│   ├── loading_screen.py       # Animated splash / launch screen
│   ├── login_screen.py         # User login screen with validation
│   ├── register_screen.py      # Registration with email check & password strength meter
│   ├── crop_selection_screen.py# Onboarding crop selection UI
│   ├── dashboard_screen.py     # Role-based dashboard (Farmer, Trader, Policymaker)
│   ├── admin_dashboard_screen.py# Administrator management dashboard
│   ├── price_production_history_screen.py # Crop & date search view with actual market records & AI forecast
│   └── feedback_screen.py      # User feedback screen with 5-star rating system
│
└── utils/                      # Helper & Utility Modules
    ├── theme.py                # Color palette & visual styling tokens
    ├── auth_utils.py            # Bcrypt hashing & SMTP email delivery logic
    ├── chart_utils.py           # Matplotlib chart generator functions
    ├── validators.py           # Email & password validation utilities
    ├── animations.py           # KivyMD UI animation helpers
    └── layout_helpers.py       # Visual layout & screen transition utilities
```

---

## ⚙️ Prerequisites

Before installing and running AgriSense, ensure you have the following installed:

- **Python**: Version 3.10 or higher
- **MySQL Server**: Version 8.0 or higher (or MariaDB equivalent)
- **Git**: Latest version
- **Virtual Environment**: `venv` (recommended)

---

## 🚀 Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/KushanLaksitha/AgriSense2.1.git
cd AgriSense2.1
```

### 2. Create and Activate a Virtual Environment

- **On Windows (PowerShell / Command Prompt)**:
  ```cmd
  python -m venv venv
  venv\Scripts\activate
  ```

- **On Linux / macOS**:
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

> **Note for Windows Users**: If you encounter installation issues with Kivy/KivyMD, install base packages first before running requirements:
> ```cmd
> pip install kivy[base] kivy_examples --pre
> pip install -r requirements.txt
> ```

---

## 🗄 Database Setup & Seeding

### 1. Create the Database Schema

Import `database/schema.sql` into your MySQL server via MySQL Workbench, DBeaver, or command line:

```bash
mysql -u root -p < database/schema.sql
```

*(Optional)* If upgrading an existing installation that predates the feedback rating feature, run the migration script:
```bash
mysql -u root -p vectamind_db < database/migration_add_rating.sql
```

### 2. Configure Environment Variables (`.env`)

Copy `.env.example` to create your local `.env` configuration file:

- **Windows (PowerShell)**:
  ```powershell
  Copy-Item .env.example .env
  ```
- **Linux / macOS**:
  ```bash
  cp .env.example .env
  ```

Open `.env` and set your MySQL credentials and SMTP email configuration:

```env
# ---- MySQL Database Configuration ----
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_actual_mysql_password
DB_NAME=vectamind_db

# ---- Email / SMTP Configuration ----
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_google_app_password
SMTP_SENDER_NAME=AgriSense

# ---- Account Confirmation URL ----
CONFIRM_BASE_URL=http://127.0.0.1:5000/confirm
```

### 3. Import Dataset & Seed Demo Accounts

AgriSense is powered by the verified 2021–2025 multi-year Sri Lankan agricultural dataset in [`AgriSense_Dataset_2021_2025_Cleaned.xlsx`](AgriSense_Dataset_2021_2025_Cleaned.xlsx).

Select the setup option that fits your workflow:

#### 🌟 Option A: Full Setup — Dataset Import & Demo Accounts (Recommended)
This command automatically imports all 2,285 weekly wholesale prices, 2,285 seasonal production records (in Mt), and 570 climate entries directly from the Excel dataset, while simultaneously creating the 4 pre-configured persona accounts (`Farmer`, `Trader`, `Policymaker`, `Admin`), sample alerts, and crop preferences:

```bash
python database/seed_demo_data.py
```

#### 📊 Option B: Dataset Import Only
If you only need to populate or refresh the market prices, production records, and climate observations directly from the cleaned Excel dataset without resetting user accounts:

```bash
python database/import_excel_dataset.py
```

---

## ✉️ Email Confirmation Endpoint

AgriSense includes an automated email confirmation workflow upon registration.

To run the confirmation server locally:

```bash
python database/confirm_server.py
```

- When running locally, links sent to emails will point to `http://127.0.0.1:5000/confirm`.
- When testing on a physical mobile device, replace `127.0.0.1` in `.env` under `CONFIRM_BASE_URL` with your development computer's Local Area Network (LAN) IP address (e.g., `http://192.168.1.100:5000/confirm`).
- **Development Mode**: If SMTP parameters are omitted, registration links are printed to the console for testing.

---

## 🖥 Running the Application

Launch the main application on desktop (runs with a simulated 400x820 mobile aspect ratio for optimal layout testing):

```bash
python main.py
```

---

## 🔑 Demo User Credentials

Once `seed_demo_data.py` has executed, you can log in using any of the pre-configured accounts:

| User Persona | Email Address | Password | Features Accessible |
| :--- | :--- | :--- | :--- |
| **Farmer** | `farmer@agrisense.lk` | `Demo@1234` | Harvest advice, crop price charts, yield recommendations |
| **Trader** | `trader@agrisense.lk` | `Demo@1234` | Price trend predictions, regional crop availability alerts |
| **Policymaker** | `policy@agrisense.lk` | `Demo@1234` | National market analytics, climate impact reports |
| **Admin** | `admin@agrisense.lk` | `Demo@1234` | User management, rating metrics, feedback review board |

---

## 📱 Android APK Build Guide (Buildozer)

AgriSense is fully configured for compilation to Android target APKs using **Buildozer**.

### Building on Linux / WSL2:

1. Install system prerequisites & Buildozer:
   ```bash
   sudo apt update && sudo apt install -y git zip unzip openjdk-17-jdk python3-pip autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libffi-dev libssl-dev
   pip install buildozer cython
   ```

2. Compile the Android Debug APK:
   ```bash
   buildozer -v android debug
   ```

3. The generated `.apk` file will be saved in the `bin/` directory.

> ⚠️ **Important Device Networking Note**: When deploying the APK to a physical Android phone, `DB_HOST` inside `.env` cannot be `localhost`. Point `DB_HOST` to a publicly accessible IP address or your local host machine's network IP.

---

## 📊 Database Schema & Migrations

The database structure consists of key normalized tables:

- **`user`**: Accounts, roles (`farmer`, `trader`, `policymaker`, `admin`), password hashes, activation state.
- **`crop`**: Core crops tracked (*Okra, Cabbage, Beans, Carrots, Leeks*).
- **`region`**: Regional districts (*Matale Region, Kandy Region*).
- **`production`**: Historical and seasonal yield records.
- **`price`**: Historical wholesale/retail vegetable prices (LKR/kg).
- **`climate`**: Rainfall (mm), temperature (°C), and humidity (%).
- **`prediction`**: Machine learning forecast outputs for price & production.
- **`alert`**: Generated automated user alerts.
- **`recommendation`**: Actionable insights per crop and region.
- **`feedback`**: User feedback records with 1–5 star ratings.

## 📑 Codebase Functions & Scripts Index

This index provides a complete, organized inventory of all **203 functions and methods** across the **25 Python source scripts** powering the AgriSense application, detailing their location, class scope, starting line number, and technical purpose.

| Architectural Layer | Scripts | Total Functions |
| :--- | :---: | :---: |
| **🖥 Application Entry Point** | 1 | 3 |
| **🗄 Database Layer & Backend Services** | 6 | 53 |
| **📱 Presentation Layer & UI Screens** | 10 | 110 |
| **⚙️ Machine Learning Engines, Utilities & Helpers** | 8 | 37 |
| **Total** | **25** | **203** |

---

### 🖥 Application Entry Point

> Core initialization, screen management, theme configuration, and async model bootstrapping.

| Script / File | Scope / Class | Function / Method | Line | Description / Purpose |
| :--- | :--- | :--- | :---: | :--- |
| [`main.py`](main.py#L33) | `AgriSenseApp` | `build()` | [`L33`](main.py#L33) | Initializes application window, sets Kivy theme colors, builds ScreenManager, and registers all screens. |
| [`main.py`](main.py#L75) | `AgriSenseApp` | `_preload_ml_models_async()` | [`L75`](main.py#L75) | Launches a background daemon thread to load LSTM, Random Forest, and SARIMA models at startup. |
| [`main.py`](main.py#L86) | `AgriSenseApp` | `route_to_dashboard()` | [`L86`](main.py#L86) | Navigates authenticated user to the appropriate dashboard based on their assigned role. |

---

### 🗄 Database Layer & Backend Services

> SQLAlchemy ORM models, session pooling, authentication handlers, email verification server, and analytical data queries.

| Script / File | Scope / Class | Function / Method | Line | Description / Purpose |
| :--- | :--- | :--- | :---: | :--- |
| [`database/auth_service.py`](database/auth_service.py#L17) | *Module* | `register_user()` | [`L17`](database/auth_service.py#L17) | Validates input, checks duplicates, hashes password, saves new unconfirmed user, and sends verification email. |
| [`database/auth_service.py`](database/auth_service.py#L58) | *Module* | `admin_create_user()` | [`L58`](database/auth_service.py#L58) | Enables administrators to create pre-activated user accounts with roles, region, and crop assignments. |
| [`database/auth_service.py`](database/auth_service.py#L95) | *Module* | `resend_confirmation()` | [`L95`](database/auth_service.py#L95) | Regenerates a confirmation token and resends the verification link email to an unverified user. |
| [`database/auth_service.py`](database/auth_service.py#L116) | *Module* | `login_user()` | [`L116`](database/auth_service.py#L116) | Authenticates email and password, checks active/confirmed status, and returns session user dictionary. |
| [`database/auth_service.py`](database/auth_service.py#L143) | *Module* | `validate_admin_session()` | [`L143`](database/auth_service.py#L143) | Verifies whether a cached session ID belongs to an active user with admin privileges. |
| [`database/confirm_server.py`](database/confirm_server.py#L36) | *Module* | `confirm()` | [`L36`](database/confirm_server.py#L36) | Flask route handler verifying confirmation tokens from email links and activating user accounts. |
| [`database/data_service.py`](database/data_service.py#L23) | *Module* | `last_db_error_occurred()` | [`L23`](database/data_service.py#L23) | Returns boolean status and error message if the most recent database operation encountered an exception. |
| [`database/data_service.py`](database/data_service.py#L28) | *Module* | `clear_db_error()` | [`L28`](database/data_service.py#L28) | Resets thread-local database error tracker state. |
| [`database/data_service.py`](database/data_service.py#L33) | *Module* | `db_safe()` | [`L33`](database/data_service.py#L33) | Decorator wrapping database calls with exception logging, rollback, and default fallback return values. |
| [`database/data_service.py`](database/data_service.py#L57) | *Module* | `get_all_crops()` | [`L57`](database/data_service.py#L57) | Queries and returns all crop entities (ID, name, category, icon) from database. |
| [`database/data_service.py`](database/data_service.py#L66) | *Module* | `get_all_regions()` | [`L66`](database/data_service.py#L66) | Queries and returns all regional districts (ID, district name, province). |
| [`database/data_service.py`](database/data_service.py#L75) | *Module* | `get_user_preferred_crop_ids()` | [`L75`](database/data_service.py#L75) | Retrieves the list of crop IDs preferred/followed by a specific user. |
| [`database/data_service.py`](database/data_service.py#L87) | *Module* | `set_user_preferred_crop_ids()` | [`L87`](database/data_service.py#L87) | Updates the association table with a user's selected crop preferences. |
| [`database/data_service.py`](database/data_service.py#L104) | *Module* | `get_price_history()` | [`L104`](database/data_service.py#L104) | Fetches historical weekly wholesale prices for a crop and region over a specified number of weeks. |
| [`database/data_service.py`](database/data_service.py#L118) | *Module* | `get_production_history()` | [`L118`](database/data_service.py#L118) | Fetches historical seasonal harvest production volumes (Mt) for a crop and region. |
| [`database/data_service.py`](database/data_service.py#L132) | *Module* | `get_latest_predictions()` | [`L132`](database/data_service.py#L132) | Retrieves future ML forecast records (price or yield) grouped by crop for a region. |
| [`database/data_service.py`](database/data_service.py#L153) | *Module* | `get_alerts_for_user()` | [`L153`](database/data_service.py#L153) | Fetches active alert notifications for a user, optionally filtering for unread alerts. |
| [`database/data_service.py`](database/data_service.py#L167) | *Module* | `mark_alert_read()` | [`L167`](database/data_service.py#L167) | Updates an alert record status to mark it as read by the user. |
| [`database/data_service.py`](database/data_service.py#L180) | *Module* | `get_recommendations_for_user()` | [`L180`](database/data_service.py#L180) | Fetches actionable advisory recommendations for a user based on their crops and region. |
| [`database/data_service.py`](database/data_service.py#L191) | *Module* | `submit_feedback()` | [`L191`](database/data_service.py#L191) | Inserts user feedback review message, star rating (1-5), and timestamp into feedback table. |
| [`database/data_service.py`](database/data_service.py#L202) | *Module* | `get_average_rating()` | [`L202`](database/data_service.py#L202) | Calculates overall average user rating score across all submitted feedback. |
| [`database/data_service.py`](database/data_service.py#L215) | *Module* | `get_all_feedback_for_admin()` | [`L215`](database/data_service.py#L215) | Retrieves paginated feedback records with user details for admin moderation. |
| [`database/data_service.py`](database/data_service.py#L236) | *Module* | `mark_feedback_reviewed()` | [`L236`](database/data_service.py#L236) | Flags a user feedback entry as reviewed by an administrator. |
| [`database/data_service.py`](database/data_service.py#L249) | *Module* | `get_all_users_for_admin()` | [`L249`](database/data_service.py#L249) | Queries all registered accounts with role filtering and search query support for the admin console. |
| [`database/data_service.py`](database/data_service.py#L284) | *Module* | `_is_last_active_admin()` | [`L284`](database/data_service.py#L284) | Safety check ensuring the last remaining active admin cannot be deactivated or deleted. |
| [`database/data_service.py`](database/data_service.py#L291) | *Module* | `toggle_user_status_by_admin()` | [`L291`](database/data_service.py#L291) | Toggles user account status between active and suspended. |
| [`database/data_service.py`](database/data_service.py#L312) | *Module* | `update_user_role_by_admin()` | [`L312`](database/data_service.py#L312) | Updates the system role of a designated user account. |
| [`database/data_service.py`](database/data_service.py#L335) | *Module* | `delete_user_by_admin()` | [`L335`](database/data_service.py#L335) | Safely removes a user account and cascading dependencies from database. |
| [`database/data_service.py`](database/data_service.py#L362) | *Module* | `update_user_profile()` | [`L362`](database/data_service.py#L362) | Updates user profile details (first name, last name, region) and returns refreshed record. |
| [`database/data_service.py`](database/data_service.py#L397) | *Module* | `get_market_summary()` | [`L397`](database/data_service.py#L397) | Computes latest wholesale price and week-over-week change percentage per crop. |
| [`database/data_service.py`](database/data_service.py#L423) | *Module* | `get_market_demand_trends()` | [`L423`](database/data_service.py#L423) | Calculates crop demand indices, trading volumes, and supply equilibrium trends. |
| [`database/data_service.py`](database/data_service.py#L485) | *Module* | `get_weather_impact_analysis()` | [`L485`](database/data_service.py#L485) | Evaluates current rainfall, temperature, and humidity against agronomic thresholds for crop risk. |
| [`database/data_service.py`](database/data_service.py#L572) | *Module* | `get_latest_prices_for_crops()` | [`L572`](database/data_service.py#L572) | Returns dictionary mapping crop names to their most recent recorded price. |
| [`database/data_service.py`](database/data_service.py#L592) | *Module* | `get_lag_features_for_crops()` | [`L592`](database/data_service.py#L592) | Extracts price lag features (t-1, t-2, t-3) used as inputs for ML inference models. |
| [`database/data_service.py`](database/data_service.py#L630) | *Module* | `get_current_weather()` | [`L630`](database/data_service.py#L630) | Returns latest weather metrics formatted for ML feature vector inputs. |
| [`database/data_service.py`](database/data_service.py#L651) | *Module* | `save_ml_prediction()` | [`L651`](database/data_service.py#L651) | Persists an ML prediction record (price/yield, forecast date, confidence) to the database. |
| [`database/data_service.py`](database/data_service.py#L671) | *Module* | `save_ml_alert()` | [`L671`](database/data_service.py#L671) | Persists an ML-generated volatility/risk alert to the alert table. |
| [`database/data_service.py`](database/data_service.py#L689) | *Module* | `save_ml_recommendation()` | [`L689`](database/data_service.py#L689) | Persists an ML-generated agronomic or market recommendation to the database. |
| [`database/data_service.py`](database/data_service.py#L707) | *Module* | `get_last_ml_run_time()` | [`L707`](database/data_service.py#L707) | Returns timestamp of the most recent automated ML prediction pipeline execution. |
| [`database/data_service.py`](database/data_service.py#L720) | *Module* | `clear_old_ml_data()` | [`L720`](database/data_service.py#L720) | Purges expired or stale ML predictions, alerts, and recommendations to prevent clutter. |
| [`database/data_service.py`](database/data_service.py#L734) | *Module* | `get_crop_name_to_id_map()` | [`L734`](database/data_service.py#L734) | Returns lookup dictionary mapping crop name strings to database primary keys. |
| [`database/data_service.py`](database/data_service.py#L745) | *Module* | `get_region_district()` | [`L745`](database/data_service.py#L745) | Returns the district name string for a given region primary key. |
| [`database/data_service.py`](database/data_service.py#L759) | *Module* | `get_price_by_date()` | [`L759`](database/data_service.py#L759) | Queries wholesale price for a specific crop and calendar date. |
| [`database/data_service.py`](database/data_service.py#L785) | *Module* | `get_production_by_date()` | [`L785`](database/data_service.py#L785) | Queries production volume for a specific crop and calendar date. |
| [`database/data_service.py`](database/data_service.py#L811) | *Module* | `get_price_production_range()` | [`L811`](database/data_service.py#L811) | Fetches combined price and yield time-series for a date window. |
| [`database/data_service.py`](database/data_service.py#L831) | *Module* | `get_latest_record_date()` | [`L831`](database/data_service.py#L831) | Retrieves the most recent record date available in the historical price dataset. |
| [`database/db_connection.py`](database/db_connection.py#L20) | *Module* | `run_schema_migrations()` | [`L20`](database/db_connection.py#L20) | Executes database schema upgrades and MySQL column type adjustments. |
| [`database/db_connection.py`](database/db_connection.py#L39) | *Module* | `create_db_engine()` | [`L39`](database/db_connection.py#L39) | Initializes SQLAlchemy engine pool with connection parameters and fallback options. |
| [`database/db_connection.py`](database/db_connection.py#L81) | *Module* | `get_session()` | [`L81`](database/db_connection.py#L81) | Creates and returns a thread-safe scoped SQLAlchemy database session. |
| [`database/db_connection.py`](database/db_connection.py#L86) | *Module* | `safe_query()` | [`L86`](database/db_connection.py#L86) | Runs a database callable inside an isolated transaction with auto-rollback on error. |
| [`database/db_connection.py`](database/db_connection.py#L98) | *Module* | `test_connection()` | [`L98`](database/db_connection.py#L98) | Tests database connectivity and logs latency/status upon startup. |
| [`database/import_excel_dataset.py`](database/import_excel_dataset.py#L32) | *Module* | `run_import()` | [`L32`](database/import_excel_dataset.py#L32) | Parses Excel agricultural dataset and imports normalized records into MySQL. |
| [`database/seed_demo_data.py`](database/seed_demo_data.py#L42) | *Module* | `run()` | [`L42`](database/seed_demo_data.py#L42) | Populates database with initial crops, demo accounts, baseline climate, and seed data. |

---

### 📱 Presentation Layer & UI Screens

> KivyMD screens, dynamic role-based dashboards, reactive user interactions, form validation, and data visualization views.

| Script / File | Scope / Class | Function / Method | Line | Description / Purpose |
| :--- | :--- | :--- | :---: | :--- |
| [`screens/loading_screen.py`](screens/loading_screen.py#L108) | `LoadingScreen` | `on_enter()` | [`L108`](screens/loading_screen.py#L108) | Screen lifecycle hook: starts logo animation and triggers background tasks. |
| [`screens/loading_screen.py`](screens/loading_screen.py#L139) | `LoadingScreen` | `_start_dots()` | [`L139`](screens/loading_screen.py#L139) | Initiates clock timer to animate loading dots text sequence. |
| [`screens/loading_screen.py`](screens/loading_screen.py#L151) | `LoadingScreen` | `finish()` | [`L151`](screens/loading_screen.py#L151) | Transitions screen manager from splash loading screen to login screen. |
| [`screens/login_screen.py`](screens/login_screen.py#L166) | `LoginScreen` | `on_enter()` | [`L166`](screens/login_screen.py#L166) | Screen lifecycle hook: resets input fields, error messages, and sets field focus. |
| [`screens/login_screen.py`](screens/login_screen.py#L171) | `LoginScreen` | `do_login()` | [`L171`](screens/login_screen.py#L171) | Handles login form submission: validates credentials and routes to dashboard. |
| [`screens/login_screen.py`](screens/login_screen.py#L207) | `LoginScreen` | `do_resend()` | [`L207`](screens/login_screen.py#L207) | Triggers resending of email verification link for unconfirmed accounts. |
| [`screens/login_screen.py`](screens/login_screen.py#L216) | `LoginScreen` | `go_register()` | [`L216`](screens/login_screen.py#L216) | Navigates from login screen to account registration screen. |
| [`screens/register_screen.py`](screens/register_screen.py#L267) | `RegisterScreen` | `on_pre_enter()` | [`L267`](screens/register_screen.py#L267) | Loads available regional districts and crops from database to populate form chips. |
| [`screens/register_screen.py`](screens/register_screen.py#L304) | `RegisterScreen` | `_make_role_chip()` | [`L304`](screens/register_screen.py#L304) | Constructs selectable role toggle chip with appropriate icon and label. |
| [`screens/register_screen.py`](screens/register_screen.py#L332) | `RegisterScreen` | `_make_crop_chip()` | [`L332`](screens/register_screen.py#L332) | Constructs selectable crop preference chip with active/inactive visual styling. |
| [`screens/register_screen.py`](screens/register_screen.py#L359) | `RegisterScreen` | `pick_role_chip()` | [`L359`](screens/register_screen.py#L359) | Handles user selection of account persona role (Farmer, Trader, Policymaker). |
| [`screens/register_screen.py`](screens/register_screen.py#L370) | `RegisterScreen` | `toggle_crop_chip()` | [`L370`](screens/register_screen.py#L370) | Toggles selection state of crop preference chip in registration form. |
| [`screens/register_screen.py`](screens/register_screen.py#L381) | `RegisterScreen` | `on_enter()` | [`L381`](screens/register_screen.py#L381) | Screen lifecycle hook: focuses initial input field when screen is displayed. |
| [`screens/register_screen.py`](screens/register_screen.py#L385) | `RegisterScreen` | `clear_email_error()` | [`L385`](screens/register_screen.py#L385) | Clears inline validation error label for email text field. |
| [`screens/register_screen.py`](screens/register_screen.py#L389) | `RegisterScreen` | `validate_email()` | [`L389`](screens/register_screen.py#L389) | Validates email format and availability in real time on text change. |
| [`screens/register_screen.py`](screens/register_screen.py#L408) | `RegisterScreen` | `on_password_change()` | [`L408`](screens/register_screen.py#L408) | Updates visual password strength indicator bar and label as user types. |
| [`screens/register_screen.py`](screens/register_screen.py#L425) | `RegisterScreen` | `check_password_match()` | [`L425`](screens/register_screen.py#L425) | Verifies that confirmation password matches entered password. |
| [`screens/register_screen.py`](screens/register_screen.py#L439) | `RegisterScreen` | `open_region_menu()` | [`L439`](screens/register_screen.py#L439) | Opens dropdown menu displaying available agricultural districts. |
| [`screens/register_screen.py`](screens/register_screen.py#L442) | `RegisterScreen` | `pick_region()` | [`L442`](screens/register_screen.py#L442) | Sets selected agricultural region in registration form state. |
| [`screens/register_screen.py`](screens/register_screen.py#L448) | `RegisterScreen` | `do_register()` | [`L448`](screens/register_screen.py#L448) | Validates complete form data, creates account, and initiates email confirmation. |
| [`screens/register_screen.py`](screens/register_screen.py#L495) | `RegisterScreen` | `go_back()` | [`L495`](screens/register_screen.py#L495) | Navigates back to login screen. |
| [`screens/crop_selection_screen.py`](screens/crop_selection_screen.py#L55) | `CropSelectionScreen` | `on_pre_enter()` | [`L55`](screens/crop_selection_screen.py#L55) | Fetches crops and pre-selects user's existing preferences in selection grid. |
| [`screens/crop_selection_screen.py`](screens/crop_selection_screen.py#L82) | `CropSelectionScreen` | `save_and_continue()` | [`L82`](screens/crop_selection_screen.py#L82) | Saves updated crop preferences to database and navigates to main dashboard. |
| [`screens/dashboard_screen.py`](screens/dashboard_screen.py#L232) | `DashboardScreen` | `on_pre_enter()` | [`L232`](screens/dashboard_screen.py#L232) | Screen lifecycle hook: initializes role UI, loads preferences, and triggers ML pipeline. |
| [`screens/dashboard_screen.py`](screens/dashboard_screen.py#L255) | `DashboardScreen` | `_run_ml_predictions_async()` | [`L255`](screens/dashboard_screen.py#L255) | Spawns background worker thread to execute ML predictions without blocking UI. |
| [`screens/dashboard_screen.py`](screens/dashboard_screen.py#L270) | `DashboardScreen` | `_ml_worker()` | [`L270`](screens/dashboard_screen.py#L270) | Background thread execution: runs LSTM/RF inference and caches results in database. |
| [`screens/dashboard_screen.py`](screens/dashboard_screen.py#L331) | `DashboardScreen` | `load_home()` | [`L331`](screens/dashboard_screen.py#L331) | Builds role-customized dashboard overview tab with KPI cards and charts. |
| [`screens/dashboard_screen.py`](screens/dashboard_screen.py#L781) | `DashboardScreen` | `_load_policymaker_home()` | [`L781`](screens/dashboard_screen.py#L781) | Renders policymaker-specific view: national demand, weather risk, and macro indicators. |
| [`screens/dashboard_screen.py`](screens/dashboard_screen.py#L1220) | `DashboardScreen` | `_load_trader_home()` | [`L1220`](screens/dashboard_screen.py#L1220) | Renders trader-specific view: wholesale price movements and market arbitrage signals. |
| [`screens/dashboard_screen.py`](screens/dashboard_screen.py#L1522) | `DashboardScreen` | `_refresh_home()` | [`L1522`](screens/dashboard_screen.py#L1522) | Refreshes home tab KPI widgets and charts on user pull-to-refresh or navigation. |
| [`screens/dashboard_screen.py`](screens/dashboard_screen.py#L1526) | `DashboardScreen` | `_make_price_card()` | [`L1526`](screens/dashboard_screen.py#L1526) | Constructs styled summary card displaying crop price, trend arrow, and volatility. |
| [`screens/dashboard_screen.py`](screens/dashboard_screen.py#L1585) | `DashboardScreen` | `_build_weather_cards()` | [`L1585`](screens/dashboard_screen.py#L1585) | Constructs regional climate cards displaying temperature, rainfall, and risk level. |
| [`screens/dashboard_screen.py`](screens/dashboard_screen.py#L1667) | `DashboardScreen` | `_make_divider()` | [`L1667`](screens/dashboard_screen.py#L1667) | Helper creating stylized visual divider line between dashboard sections. |
| [`screens/dashboard_screen.py`](screens/dashboard_screen.py#L1677) | `DashboardScreen` | `load_recommendations()` | [`L1677`](screens/dashboard_screen.py#L1677) | Populates recommendations tab with AI agronomic advice cards. |
| [`screens/dashboard_screen.py`](screens/dashboard_screen.py#L1729) | `DashboardScreen` | `_get_ml_recommendations()` | [`L1729`](screens/dashboard_screen.py#L1729) | Retrieves cached ML recommendations for user's crops and region. |
| [`screens/dashboard_screen.py`](screens/dashboard_screen.py#L1742) | `DashboardScreen` | `_render_ml_recommendations()` | [`L1742`](screens/dashboard_screen.py#L1742) | Renders ML recommendation cards with urgency styling and action badges. |
| [`screens/dashboard_screen.py`](screens/dashboard_screen.py#L1890) | `DashboardScreen` | `_render_db_recommendations()` | [`L1890`](screens/dashboard_screen.py#L1890) | Fallback renderer for database-stored recommendation records. |
| [`screens/dashboard_screen.py`](screens/dashboard_screen.py#L1963) | `DashboardScreen` | `_toggle_rec_card()` | [`L1963`](screens/dashboard_screen.py#L1963) | Toggles expanded/collapsed detail view of a recommendation card. |
| [`screens/dashboard_screen.py`](screens/dashboard_screen.py#L1975) | `DashboardScreen` | `load_alerts()` | [`L1975`](screens/dashboard_screen.py#L1975) | Loads and renders user notification alerts in alerts tab with unread filters. |
| [`screens/dashboard_screen.py`](screens/dashboard_screen.py#L2142) | `DashboardScreen` | `dismiss_alert()` | [`L2142`](screens/dashboard_screen.py#L2142) | Marks an alert as dismissed/read and animates its removal from list. |
| [`screens/dashboard_screen.py`](screens/dashboard_screen.py#L2150) | `DashboardScreen` | `mark_all_alerts_read()` | [`L2150`](screens/dashboard_screen.py#L2150) | Marks all active notifications as read and updates badge counters. |
| [`screens/dashboard_screen.py`](screens/dashboard_screen.py#L2161) | `DashboardScreen` | `_build_history_crop_chips()` | [`L2161`](screens/dashboard_screen.py#L2161) | Builds horizontal scrollable row of crop filter chips for history tab. |
| [`screens/dashboard_screen.py`](screens/dashboard_screen.py#L2180) | `DashboardScreen` | `_make_hist_chip()` | [`L2180`](screens/dashboard_screen.py#L2180) | Constructs an individual crop selector chip for history chart navigation. |
| [`screens/dashboard_screen.py`](screens/dashboard_screen.py#L2204) | `DashboardScreen` | `_select_history_chip()` | [`L2204`](screens/dashboard_screen.py#L2204) | Updates active crop selection state and triggers history chart redraw. |
| [`screens/dashboard_screen.py`](screens/dashboard_screen.py#L2212) | `DashboardScreen` | `_pick_history_chip()` | [`L2212`](screens/dashboard_screen.py#L2212) | Event handler when user taps a crop history chip. |
| [`screens/dashboard_screen.py`](screens/dashboard_screen.py#L2219) | `DashboardScreen` | `set_metric()` | [`L2219`](screens/dashboard_screen.py#L2219) | Toggles history view metric between wholesale price (Rs/kg) and production (Mt). |
| [`screens/dashboard_screen.py`](screens/dashboard_screen.py#L2231) | `DashboardScreen` | `open_history_date_picker()` | [`L2231`](screens/dashboard_screen.py#L2231) | Opens date picker modal to query historical records for a specific date. |
| [`screens/dashboard_screen.py`](screens/dashboard_screen.py#L2239) | `DashboardScreen` | `_on_history_date_picked()` | [`L2239`](screens/dashboard_screen.py#L2239) | Callback triggered when user selects a date in history date picker. |
| [`screens/dashboard_screen.py`](screens/dashboard_screen.py#L2244) | `DashboardScreen` | `open_price_history_screen()` | [`L2244`](screens/dashboard_screen.py#L2244) | Navigates user to full-screen dedicated price & production history view. |
| [`screens/dashboard_screen.py`](screens/dashboard_screen.py#L2256) | `DashboardScreen` | `load_history()` | [`L2256`](screens/dashboard_screen.py#L2256) | Fetches time-series data and renders interactive Matplotlib trend charts. |
| [`screens/dashboard_screen.py`](screens/dashboard_screen.py#L2506) | `DashboardScreen` | `load_profile()` | [`L2506`](screens/dashboard_screen.py#L2506) | Loads user profile tab with account details, role badge, and preferences. |
| [`screens/dashboard_screen.py`](screens/dashboard_screen.py#L2609) | `DashboardScreen` | `open_edit_profile_dialog()` | [`L2609`](screens/dashboard_screen.py#L2609) | Opens modal dialog enabling user to update their name and district. |
| [`screens/dashboard_screen.py`](screens/dashboard_screen.py#L2690) | `DashboardScreen` | `edit_crops()` | [`L2690`](screens/dashboard_screen.py#L2690) | Navigates user to crop selection screen to modify followed crops. |
| [`screens/dashboard_screen.py`](screens/dashboard_screen.py#L2694) | `DashboardScreen` | `go_feedback()` | [`L2694`](screens/dashboard_screen.py#L2694) | Navigates user to app feedback and rating submission screen. |
| [`screens/dashboard_screen.py`](screens/dashboard_screen.py#L2698) | `DashboardScreen` | `logout()` | [`L2698`](screens/dashboard_screen.py#L2698) | Clears active session cache and returns user to login screen. |
| [`screens/price_production_history_screen.py`](screens/price_production_history_screen.py#L403) | `PriceProductionHistoryScreen` | `on_pre_enter()` | [`L403`](screens/price_production_history_screen.py#L403) | Screen lifecycle hook: loads crops and initializes historical query controls. |
| [`screens/price_production_history_screen.py`](screens/price_production_history_screen.py#L414) | `PriceProductionHistoryScreen` | `go_back()` | [`L414`](screens/price_production_history_screen.py#L414) | Navigates back to main dashboard. |
| [`screens/price_production_history_screen.py`](screens/price_production_history_screen.py#L419) | `PriceProductionHistoryScreen` | `open_crop_menu()` | [`L419`](screens/price_production_history_screen.py#L419) | Opens dropdown menu to pick crop for historical query. |
| [`screens/price_production_history_screen.py`](screens/price_production_history_screen.py#L440) | `PriceProductionHistoryScreen` | `select_crop()` | [`L440`](screens/price_production_history_screen.py#L440) | Sets chosen crop and reloads historical price/production charts. |
| [`screens/price_production_history_screen.py`](screens/price_production_history_screen.py#L446) | `PriceProductionHistoryScreen` | `show_date_picker()` | [`L446`](screens/price_production_history_screen.py#L446) | Opens date picker dialog to select reference evaluation date. |
| [`screens/price_production_history_screen.py`](screens/price_production_history_screen.py#L454) | `PriceProductionHistoryScreen` | `on_date_selected()` | [`L454`](screens/price_production_history_screen.py#L454) | Callback when date is selected; recalculates historical windows. |
| [`screens/price_production_history_screen.py`](screens/price_production_history_screen.py#L458) | `PriceProductionHistoryScreen` | `load_data()` | [`L458`](screens/price_production_history_screen.py#L458) | Queries price and production records and renders comparative visualizations. |
| [`screens/feedback_screen.py`](screens/feedback_screen.py#L285) | `FeedbackScreen` | `on_pre_enter()` | [`L285`](screens/feedback_screen.py#L285) | Prepares feedback form state and clears previous input before display. |
| [`screens/feedback_screen.py`](screens/feedback_screen.py#L301) | `FeedbackScreen` | `on_enter()` | [`L301`](screens/feedback_screen.py#L301) | Screen lifecycle hook: animates form entry and focuses text area. |
| [`screens/feedback_screen.py`](screens/feedback_screen.py#L304) | `FeedbackScreen` | `reset_state()` | [`L304`](screens/feedback_screen.py#L304) | Resets star rating, selected topic pills, and comments to defaults. |
| [`screens/feedback_screen.py`](screens/feedback_screen.py#L312) | `FeedbackScreen` | `_build_emoji_row()` | [`L312`](screens/feedback_screen.py#L312) | Builds animated emoji sentiment selector corresponding to ratings (1-5). |
| [`screens/feedback_screen.py`](screens/feedback_screen.py#L327) | `FeedbackScreen` | `_build_star_row()` | [`L327`](screens/feedback_screen.py#L327) | Builds interactive star rating widget with hover and click state. |
| [`screens/feedback_screen.py`](screens/feedback_screen.py#L342) | `FeedbackScreen` | `_build_topic_chips()` | [`L342`](screens/feedback_screen.py#L342) | Builds category chips (e.g., UI, Accuracy, Performance) for feedback tagging. |
| [`screens/feedback_screen.py`](screens/feedback_screen.py#L360) | `FeedbackScreen` | `_build_quick_pills()` | [`L360`](screens/feedback_screen.py#L360) | Builds predefined quick-feedback comment pills for fast user input. |
| [`screens/feedback_screen.py`](screens/feedback_screen.py#L383) | `FeedbackScreen` | `set_rating()` | [`L383`](screens/feedback_screen.py#L383) | Sets selected numerical star rating and updates emoji highlight. |
| [`screens/feedback_screen.py`](screens/feedback_screen.py#L409) | `FeedbackScreen` | `toggle_topic()` | [`L409`](screens/feedback_screen.py#L409) | Toggles active state of category topic chip. |
| [`screens/feedback_screen.py`](screens/feedback_screen.py#L426) | `FeedbackScreen` | `toggle_pill()` | [`L426`](screens/feedback_screen.py#L426) | Toggles predefined feedback pill and syncs into message text. |
| [`screens/feedback_screen.py`](screens/feedback_screen.py#L442) | `FeedbackScreen` | `_sync_message_from_selections()` | [`L442`](screens/feedback_screen.py#L442) | Synchronizes selected quick pills into feedback comment text area. |
| [`screens/feedback_screen.py`](screens/feedback_screen.py#L459) | `FeedbackScreen` | `_extract_custom_user_notes()` | [`L459`](screens/feedback_screen.py#L459) | Extracts custom user text distinct from automated quick pill text. |
| [`screens/feedback_screen.py`](screens/feedback_screen.py#L473) | `FeedbackScreen` | `clear_form()` | [`L473`](screens/feedback_screen.py#L473) | Clears all form controls, ratings, and feedback comments. |
| [`screens/feedback_screen.py`](screens/feedback_screen.py#L479) | `FeedbackScreen` | `send()` | [`L479`](screens/feedback_screen.py#L479) | Validates input, submits feedback record to database, and shows confirmation. |
| [`screens/feedback_screen.py`](screens/feedback_screen.py#L507) | `FeedbackScreen` | `go_back()` | [`L507`](screens/feedback_screen.py#L507) | Navigates back to main dashboard. |
| [`screens/admin_dashboard_screen.py`](screens/admin_dashboard_screen.py#L223) | `AdminDashboardScreen` | `on_pre_enter()` | [`L223`](screens/admin_dashboard_screen.py#L223) | Screen lifecycle hook: verifies admin session, updates stats banner, and loads users. |
| [`screens/admin_dashboard_screen.py`](screens/admin_dashboard_screen.py#L235) | `AdminDashboardScreen` | `_update_banner()` | [`L235`](screens/admin_dashboard_screen.py#L235) | Updates top statistics banner showing total users, active count, and average rating. |
| [`screens/admin_dashboard_screen.py`](screens/admin_dashboard_screen.py#L250) | `AdminDashboardScreen` | `go_to_create_user()` | [`L250`](screens/admin_dashboard_screen.py#L250) | Navigates admin to user creation screen. |
| [`screens/admin_dashboard_screen.py`](screens/admin_dashboard_screen.py#L259) | `AdminDashboardScreen` | `go_to_feedback()` | [`L259`](screens/admin_dashboard_screen.py#L259) | Navigates admin to feedback review and moderation screen. |
| [`screens/admin_dashboard_screen.py`](screens/admin_dashboard_screen.py#L268) | `AdminDashboardScreen` | `logout()` | [`L268`](screens/admin_dashboard_screen.py#L268) | Clears admin session and returns to login screen. |
| [`screens/admin_dashboard_screen.py`](screens/admin_dashboard_screen.py#L277) | `AdminDashboardScreen` | `_setup_role_filter_chips()` | [`L277`](screens/admin_dashboard_screen.py#L277) | Constructs role filter chips (All, Farmer, Trader, Policymaker, Admin). |
| [`screens/admin_dashboard_screen.py`](screens/admin_dashboard_screen.py#L297) | `AdminDashboardScreen` | `set_role_filter()` | [`L297`](screens/admin_dashboard_screen.py#L297) | Applies selected role filter and refreshes user management list. |
| [`screens/admin_dashboard_screen.py`](screens/admin_dashboard_screen.py#L305) | `AdminDashboardScreen` | `on_search_text_changed()` | [`L305`](screens/admin_dashboard_screen.py#L305) | Filters displayed user cards in real time as search query changes. |
| [`screens/admin_dashboard_screen.py`](screens/admin_dashboard_screen.py#L309) | `AdminDashboardScreen` | `load_users()` | [`L309`](screens/admin_dashboard_screen.py#L309) | Fetches user accounts from database according to active filters and search query. |
| [`screens/admin_dashboard_screen.py`](screens/admin_dashboard_screen.py#L344) | `AdminDashboardScreen` | `_build_user_card()` | [`L344`](screens/admin_dashboard_screen.py#L344) | Constructs detailed user card with avatar, role badge, status switch, and actions. |
| [`screens/admin_dashboard_screen.py`](screens/admin_dashboard_screen.py#L443) | `AdminDashboardScreen` | `toggle_user_status()` | [`L443`](screens/admin_dashboard_screen.py#L443) | Toggles user account between active and suspended with confirmation check. |
| [`screens/admin_dashboard_screen.py`](screens/admin_dashboard_screen.py#L452) | `AdminDashboardScreen` | `_is_me()` | [`L452`](screens/admin_dashboard_screen.py#L452) | Checks if a given user record corresponds to the currently logged-in administrator. |
| [`screens/admin_dashboard_screen.py`](screens/admin_dashboard_screen.py#L457) | `AdminDashboardScreen` | `open_role_change_menu()` | [`L457`](screens/admin_dashboard_screen.py#L457) | Opens dropdown menu enabling admin to modify a user's assigned role. |
| [`screens/admin_dashboard_screen.py`](screens/admin_dashboard_screen.py#L472) | `AdminDashboardScreen` | `change_user_role()` | [`L472`](screens/admin_dashboard_screen.py#L472) | Updates user role in database and refreshes user card display. |
| [`screens/admin_dashboard_screen.py`](screens/admin_dashboard_screen.py#L480) | `AdminDashboardScreen` | `confirm_delete_user()` | [`L480`](screens/admin_dashboard_screen.py#L480) | Displays confirmation dialog before permanently deleting a user account. |
| [`screens/admin_dashboard_screen.py`](screens/admin_dashboard_screen.py#L504) | `AdminDashboardScreen` | `_do_delete()` | [`L504`](screens/admin_dashboard_screen.py#L504) | Executes permanent deletion of user account and related records from database. |
| [`screens/admin_create_user_screen.py`](screens/admin_create_user_screen.py#L257) | `AdminCreateUserScreen` | `on_pre_enter()` | [`L257`](screens/admin_create_user_screen.py#L257) | Screen lifecycle hook: loads regions from database and resets form fields. |
| [`screens/admin_create_user_screen.py`](screens/admin_create_user_screen.py#L267) | `AdminCreateUserScreen` | `reset_form()` | [`L267`](screens/admin_create_user_screen.py#L267) | Resets all input fields, error labels, and dropdown selections to defaults. |
| [`screens/admin_create_user_screen.py`](screens/admin_create_user_screen.py#L281) | `AdminCreateUserScreen` | `open_role_menu()` | [`L281`](screens/admin_create_user_screen.py#L281) | Opens dropdown menu to select role for new account. |
| [`screens/admin_create_user_screen.py`](screens/admin_create_user_screen.py#L297) | `AdminCreateUserScreen` | `pick_role()` | [`L297`](screens/admin_create_user_screen.py#L297) | Sets selected role in creation form state. |
| [`screens/admin_create_user_screen.py`](screens/admin_create_user_screen.py#L303) | `AdminCreateUserScreen` | `open_region_menu()` | [`L303`](screens/admin_create_user_screen.py#L303) | Opens dropdown menu to assign regional district to new user. |
| [`screens/admin_create_user_screen.py`](screens/admin_create_user_screen.py#L321) | `AdminCreateUserScreen` | `pick_region()` | [`L321`](screens/admin_create_user_screen.py#L321) | Sets selected district in creation form state. |
| [`screens/admin_create_user_screen.py`](screens/admin_create_user_screen.py#L327) | `AdminCreateUserScreen` | `submit_form()` | [`L327`](screens/admin_create_user_screen.py#L327) | Validates input and creates new pre-activated user account in database. |
| [`screens/admin_create_user_screen.py`](screens/admin_create_user_screen.py#L369) | `AdminCreateUserScreen` | `go_to_admin_dashboard()` | [`L369`](screens/admin_create_user_screen.py#L369) | Navigates back to admin management dashboard. |
| [`screens/admin_create_user_screen.py`](screens/admin_create_user_screen.py#L377) | `AdminCreateUserScreen` | `logout()` | [`L377`](screens/admin_create_user_screen.py#L377) | Logs out admin and redirects to login screen. |
| [`screens/admin_feedback_screen.py`](screens/admin_feedback_screen.py#L219) | `AdminFeedbackScreen` | `on_pre_enter()` | [`L219`](screens/admin_feedback_screen.py#L219) | Screen lifecycle hook: loads feedback records and updates rating statistics. |
| [`screens/admin_feedback_screen.py`](screens/admin_feedback_screen.py#L229) | `AdminFeedbackScreen` | `set_filter()` | [`L229`](screens/admin_feedback_screen.py#L229) | Filters feedback list by review status (All, Unreviewed, Reviewed). |
| [`screens/admin_feedback_screen.py`](screens/admin_feedback_screen.py#L246) | `AdminFeedbackScreen` | `load_feedback()` | [`L246`](screens/admin_feedback_screen.py#L246) | Fetches feedback entries from database with user profile joins. |
| [`screens/admin_feedback_screen.py`](screens/admin_feedback_screen.py#L295) | `AdminFeedbackScreen` | `render_cards()` | [`L295`](screens/admin_feedback_screen.py#L295) | Renders feedback cards with user info, star rating, comment text, and review badge. |
| [`screens/admin_feedback_screen.py`](screens/admin_feedback_screen.py#L338) | `AdminFeedbackScreen` | `_build_feedback_card()` | [`L338`](screens/admin_feedback_screen.py#L338) | Constructs individual feedback review card widget with moderation actions. |
| [`screens/admin_feedback_screen.py`](screens/admin_feedback_screen.py#L528) | `AdminFeedbackScreen` | `_mark_reviewed()` | [`L528`](screens/admin_feedback_screen.py#L528) | Marks a specific feedback submission as reviewed by admin. |
| [`screens/admin_feedback_screen.py`](screens/admin_feedback_screen.py#L537) | `AdminFeedbackScreen` | `go_to_admin_dashboard()` | [`L537`](screens/admin_feedback_screen.py#L537) | Navigates back to admin management dashboard. |
| [`screens/admin_feedback_screen.py`](screens/admin_feedback_screen.py#L545) | `AdminFeedbackScreen` | `logout()` | [`L545`](screens/admin_feedback_screen.py#L545) | Logs out admin and redirects to login screen. |

---

### ⚙️ Machine Learning Engines, Utilities & Helpers

> LSTM/RF inference pipelines, SARIMA time-series models, automated rule engines, chart renderers, UI animations, and security validators.

| Script / File | Scope / Class | Function / Method | Line | Description / Purpose |
| :--- | :--- | :--- | :---: | :--- |
| [`utils/alert_engine.py`](utils/alert_engine.py#L38) | *Module* | `generate_alerts()` | [`L38`](utils/alert_engine.py#L38) | Analyzes price trends, anomaly Z-scores, and climate indicators to trigger alerts. |
| [`utils/animations.py`](utils/animations.py#L19) | *Module* | `fade_in()` | [`L19`](utils/animations.py#L19) | Animates widget opacity from 0 to 1 with configurable transition duration. |
| [`utils/animations.py`](utils/animations.py#L29) | *Module* | `stagger_fade_in()` | [`L29`](utils/animations.py#L29) | Sequentially fades in a collection of widgets with staggered delay offsets. |
| [`utils/animations.py`](utils/animations.py#L35) | *Module* | `button_press_bounce()` | [`L35`](utils/animations.py#L35) | Provides tap/click squash-and-rebound physics feedback on interactive buttons. |
| [`utils/animations.py`](utils/animations.py#L45) | *Module* | `slide_up_fade_in()` | [`L45`](utils/animations.py#L45) | Animates a widget sliding upwards from a lower offset while smoothly fading in. |
| [`utils/animations.py`](utils/animations.py#L70) | *Module* | `bounce_scale()` | [`L70`](utils/animations.py#L70) | Scales a widget down slightly and springs back to original size on user tap. |
| [`utils/animations.py`](utils/animations.py#L94) | *Module* | `shake()` | [`L94`](utils/animations.py#L94) | Produces horizontal shake vibration animation to indicate validation error. |
| [`utils/animations.py`](utils/animations.py#L111) | *Module* | `pulse_color()` | [`L111`](utils/animations.py#L111) | Alternates background color between two states continuously to draw attention. |
| [`utils/animations.py`](utils/animations.py#L122) | *Module* | `ripple_flash()` | [`L122`](utils/animations.py#L122) | Flashes widget background briefly with highlight tint on user selection. |
| [`utils/animations.py`](utils/animations.py#L131) | *Module* | `fade_out_remove()` | [`L131`](utils/animations.py#L131) | Fades out a widget to zero opacity and invokes a removal callback upon completion. |
| [`utils/auth_utils.py`](utils/auth_utils.py#L23) | *Module* | `hash_password()` | [`L23`](utils/auth_utils.py#L23) | Generates a secure cryptographic password hash using bcrypt/pbkdf2. |
| [`utils/auth_utils.py`](utils/auth_utils.py#L27) | *Module* | `verify_password()` | [`L27`](utils/auth_utils.py#L27) | Verifies a plaintext password against a stored cryptographic hash. |
| [`utils/auth_utils.py`](utils/auth_utils.py#L34) | *Module* | `generate_confirmation_token()` | [`L34`](utils/auth_utils.py#L34) | Generates a cryptographically random, URL-safe email confirmation token. |
| [`utils/auth_utils.py`](utils/auth_utils.py#L38) | *Module* | `send_confirmation_email()` | [`L38`](utils/auth_utils.py#L38) | Dispatches account activation email containing the verification link. |
| [`utils/auth_utils.py`](utils/auth_utils.py#L75) | *Module* | `token_is_expired()` | [`L75`](utils/auth_utils.py#L75) | Validates whether a confirmation token has passed its expiration window. |
| [`utils/chart_utils.py`](utils/chart_utils.py#L25) | *Module* | `_style_axes()` | [`L25`](utils/chart_utils.py#L25) | Applies dark/light modern typography, grid styling, and padding to Matplotlib axes. |
| [`utils/chart_utils.py`](utils/chart_utils.py#L41) | *Module* | `_fig_to_widget()` | [`L41`](utils/chart_utils.py#L41) | Renders a Matplotlib Figure into an in-memory PNG buffer and wraps it in a Kivy Image widget. |
| [`utils/chart_utils.py`](utils/chart_utils.py#L62) | *Module* | `build_line_chart()` | [`L62`](utils/chart_utils.py#L62) | Builds a stylized anti-aliased line chart with gradient fill for price time-series. |
| [`utils/chart_utils.py`](utils/chart_utils.py#L101) | *Module* | `build_bar_chart()` | [`L101`](utils/chart_utils.py#L101) | Builds a stylized vertical bar chart with rounded edges for seasonal production. |
| [`utils/chart_utils.py`](utils/chart_utils.py#L142) | *Module* | `build_comparison_bar()` | [`L142`](utils/chart_utils.py#L142) | Generates grouped side-by-side bar chart comparing actual vs forecast metrics. |
| [`utils/layout_helpers.py`](utils/layout_helpers.py#L10) | *Module* | `center_scroll_content()` | [`L10`](utils/layout_helpers.py#L10) | Adjusts scroll view container layout to center content vertically and horizontally. |
| [`utils/layout_helpers.py`](utils/layout_helpers.py#L59) | *Module* | `show_snackbar()` | [`L59`](utils/layout_helpers.py#L59) | Constructs and displays a styled KivyMD floating snackbar notification with custom text. |
| [`utils/ml_engine.py`](utils/ml_engine.py#L71) | *Module* | `_load_keras_model()` | [`L71`](utils/ml_engine.py#L71) | Safely loads Keras/TensorFlow sequential and functional models from file disk. |
| [`utils/ml_engine.py`](utils/ml_engine.py#L90) | *Module* | `_ensure_loaded()` | [`L90`](utils/ml_engine.py#L90) | Thread-safe loader ensuring LSTM and Random Forest models and scalers are loaded in memory. |
| [`utils/ml_engine.py`](utils/ml_engine.py#L138) | *Module* | `_load_sarima()` | [`L138`](utils/ml_engine.py#L138) | Lazy-loads per-crop SARIMA seasonal time-series models on demand. |
| [`utils/ml_engine.py`](utils/ml_engine.py#L157) | *Module* | `_current_season()` | [`L157`](utils/ml_engine.py#L157) | Determines current Sri Lankan cultivation season (Maha or Yala) based on date. |
| [`utils/ml_engine.py`](utils/ml_engine.py#L163) | *Module* | `_build_lstm_sequence()` | [`L163`](utils/ml_engine.py#L163) | Prepares scaled 13-week lookback tensor window for LSTM neural network inference. |
| [`utils/ml_engine.py`](utils/ml_engine.py#L218) | *Module* | `predict_price()` | [`L218`](utils/ml_engine.py#L218) | Performs multi-step wholesale vegetable price forecast using trained LSTM models. |
| [`utils/ml_engine.py`](utils/ml_engine.py#L266) | *Module* | `predict_production()` | [`L266`](utils/ml_engine.py#L266) | Predicts seasonal harvest production volume (Mt) using Random Forest ensemble regressor. |
| [`utils/ml_engine.py`](utils/ml_engine.py#L318) | *Module* | `predict_price_sarima()` | [`L318`](utils/ml_engine.py#L318) | Generates multi-week seasonal price trajectory using SARIMA time-series model. |
| [`utils/ml_engine.py`](utils/ml_engine.py#L349) | *Module* | `run_all_predictions()` | [`L349`](utils/ml_engine.py#L349) | Executes complete end-to-end inference pipeline for all tracked crops in a region. |
| [`utils/ml_engine.py`](utils/ml_engine.py#L429) | *Module* | `preload_models()` | [`L429`](utils/ml_engine.py#L429) | Preloads all neural network and regression model weights into RAM in background. |
| [`utils/recommendation_engine.py`](utils/recommendation_engine.py#L28) | *Module* | `generate_recommendations()` | [`L28`](utils/recommendation_engine.py#L28) | Generates tailored agronomic advice, harvesting guidance, and market alerts from predictions. |
| [`utils/validators.py`](utils/validators.py#L20) | *Module* | `is_valid_email_format()` | [`L20`](utils/validators.py#L20) | Checks whether email matches RFC-compliant email regular expression. |
| [`utils/validators.py`](utils/validators.py#L24) | *Module* | `email_already_registered()` | [`L24`](utils/validators.py#L24) | Queries database to verify if an email address is already registered. |
| [`utils/validators.py`](utils/validators.py#L35) | *Module* | `check_password_strength()` | [`L35`](utils/validators.py#L35) | Evaluates password against length, digit, casing, and special character criteria. |
| [`utils/validators.py`](utils/validators.py#L59) | *Module* | `is_password_acceptable()` | [`L59`](utils/validators.py#L59) | Returns boolean indicating whether password meets mandatory security policy. |

---

## 👤 Author & License

- **Developers / Maintainers**: [Kushan Laksitha](https://github.com/KushanLaksitha)
                                [Tharusha Dilantha](https://github.com/tharush4d)
                                [Dinuri Gayara](https://github.com/DGayara)
                                [Ashan Oshadha](https://github.com/ashanoshada)
                                [Thilini Samaranayaka](https://github.com/thilinisamaranayaka)
                                
- **Repository**: [Demo](https://github.com/KushanLaksitha/demo)
- **License**: Distributed under the MIT License. See `LICENSE` for details.

---

*Made with Team VectaMind for Sri Lankan Agriculture.*