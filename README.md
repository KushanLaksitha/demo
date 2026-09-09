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