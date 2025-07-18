# 🚢 AIS Marine Traffic Analyzer

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-green.svg)

A web application for analyzing AIS (Automatic Identification System) data from marinecadastre.gov with advanced data mining and risk prediction capabilities.

## ✨ Features

- 📥 **Download AIS data** from marinecadastre.gov
- 🔍 **Filter data** by vessel type, geographic area
- 🗺️ **Interactive maps** with vessel positions
  - Basic map
  - Advanced map with layers
  - Direct integration with Marine Cadastre
- 📊 **Advanced analytics**
  - Correlation analysis
  - Temporal pattern detection
  - Vessel group identification
- 🚨 **Risk analysis**
  - Risk score calculation
  - Risk heatmap
  - Risky route prediction
- 🔮 **Hidden pattern mining**
  - Anomaly detection
  - Cluster analysis

## 🛠️ Architecture

```
datapy/
├── analytics.py         # Advanced analytics functions
├── api_endpoints.py     # API endpoint handlers
├── data/                # Data storage
│   └── sample_data.py   # Sample data generator
├── main.py              # Main FastAPI application
├── requirements.txt     # Dependencies
├── risk_analysis.py     # Risk analysis functions
├── run.py               # Application entry point
└── static/              # Static assets
    ├── css/             # CSS stylesheets
    └── js/              # JavaScript files
```

## 📋 Data Structure

| Category | Parameters |
|----------|------------|
| **Vessel Information** | MMSI, VesselName, VesselType, Length, Width, Draft |
| **Position Data** | LAT, LON, SOG, COG, BaseDateTime, Status, Destination |
| **Risk Analysis** | RiskScore, CollisionRisk, WeatherRisk, RouteDeviation, SpeedAnomaly, NavigationHazard |

## 🔄 Data Flow

```mermaid
graph TD
    A[AIS Data Source] -->|Download| B[Raw Data]
    B -->|Filter| C[Filtered Data]
    C -->|Analyze| D[Analytics]
    C -->|Calculate Risk| E[Risk Analysis]
    C -->|Mine Patterns| F[Hidden Patterns]
    D --> G[Visualization]
    E --> G
    F --> G
```

## 📊 Risk Analysis Model

The risk analysis model calculates a comprehensive risk score based on five key factors:

- **Collision Risk** (30%): Based on vessel density in the area
- **Weather Risk** (20%): Simulated weather conditions
- **Route Deviation** (15%): Deviation from normal routes
- **Speed Anomaly** (20%): Abnormal speed detection
- **Navigation Hazard** (15%): Proximity to navigation hazards

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- pip

### Installation

1. Clone the repository:
```bash
git clone https://github.com/tranhao-wq/AIS-NOAA-Track.git
cd AIS-NOAA-Track
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python run.py
```

4. Open your browser and navigate to:
```
http://localhost:8000
```

## 🖥️ App Screens

### AIS Marine Traffic Analyzer (Desktop)

#### 📂 Data Loading
```
+-------------------------------------------------------------+
| [📂 Data Loading] [📊 Data Analysis] [🕵️‍♂️ Hidden Data] [⚠️ Risk] |
+-------------------------------------------------------------+
|  Data Options:  [Load CSV] [Sample Data] [Show Chart]       |
|  File: [__________________________]                         |
+-------------------------------------------------------------+
|  Data Table:                                               |
|  +---------+---------+---------+---------+                 |
|  | Col1    | Col2    | Col3    | ...     |                 |
|  +---------+---------+---------+---------+                 |
|  | ...     | ...     | ...     | ...     |                 |
|  +---------+---------+---------+---------+                 |
+-------------------------------------------------------------+
|  Info: Records: 0   Columns: 0                             |
+-------------------------------------------------------------+
| Status bar: Ready                                          |
+-------------------------------------------------------------+
```

#### 📊 Data Analysis
```
+-------------------------------------------------------------+
| [📂 Data Loading] [📊 Data Analysis] [🕵️‍♂️ Hidden Data] [⚠️ Risk] |
+-------------------------------------------------------------+
|  Analysis Options: [Detect Patterns] [Detect Anomalies]     |
|  [Show Analysis Chart]                                      |
+-------------------------------------------------------------+
|  Analysis Results:                                          |
|  +-------------------------------------+                   |
|  | Text/Chart/Result Area              |                   |
|  +-------------------------------------+                   |
+-------------------------------------------------------------+
| Status bar: Ready                                          |
+-------------------------------------------------------------+
```

#### 🕵️‍♂️ Hidden Data Mining
```
+-------------------------------------------------------------+
| [📂 Data Loading] [📊 Data Analysis] [🕵️‍♂️ Hidden Data] [⚠️ Risk] |
+-------------------------------------------------------------+
|  Hidden Data Options: [Mine Patterns] [Show Correlations]   |
+-------------------------------------------------------------+
|  Hidden Data Results:                                       |
|  +-------------------------------------+                   |
|  | Text/Chart/Result Area              |                   |
|  +-------------------------------------+                   |
+-------------------------------------------------------------+
| Status bar: Ready                                          |
+-------------------------------------------------------------+
```

#### ⚠️ Risk Analysis
```
+-------------------------------------------------------------+
| [📂 Data Loading] [📊 Data Analysis] [🕵️‍♂️ Hidden Data] [⚠️ Risk] |
+-------------------------------------------------------------+
|  Risk Options: [Calc Risk Score] [Risky Routes] [Show Map]  |
+-------------------------------------------------------------+
|  Risk Results:                                              |
|  +-------------------------------------+                   |
|  | Text/Chart/Map Area                 |                   |
|  +-------------------------------------+                   |
+-------------------------------------------------------------+
| Status bar: Ready                                          |
+-------------------------------------------------------------+
```

---

### SpecObj-DR17 Analyzer

#### 📂 Data Loading & Processing
```
+--------------------------------------------------------------------------------------+
| [📂 Data] [📊 Sample] [🕵️‍♂️ Hidden] [🤖 Prediction] [🧭 Direction]                      |
+--------------------------------------------------------------------------------------+
|  Data Options: [Choose File] [Sample Size] [Sample Data]                             |
|  File: [__________________________]                                                 |
+--------------------------------------------------------------------------------------+
|  Data Table:                                                                        |
|  +---------+---------+---------+---------+---------+---------+                      |
|  | objid   | ra      | dec     | z       | class   | ...     |                      |
|  +---------+---------+---------+---------+---------+---------+                      |
|  | ...     | ...     | ...     | ...     | ...     | ...     |                      |
|  +---------+---------+---------+---------+---------+---------+                      |
+--------------------------------------------------------------------------------------+
| Status bar: Ready                                                                    |
+--------------------------------------------------------------------------------------+
```

#### 📊 Sample Analysis
```
+--------------------------------------------------------------------------------------+
| [📂 Data] [📊 Sample] [🕵️‍♂️ Hidden] [🤖 Prediction] [🧭 Direction]                      |
+--------------------------------------------------------------------------------------+
|  Sample Analysis: [Basic Stats] [Class Dist] [Correlation]                           |
+--------------------------------------------------------------------------------------+
|  Results:                                                                            |
|  +---------------------------------------------+                                     |
|  | Text/Chart/Result Area                      |                                     |
|  +---------------------------------------------+                                     |
+--------------------------------------------------------------------------------------+
| Status bar: Ready                                                                    |
+--------------------------------------------------------------------------------------+
```

#### 🕵️‍♂️ Hidden Data Mining
```
+--------------------------------------------------------------------------------------+
| [📂 Data] [📊 Sample] [🕵️‍♂️ Hidden] [🤖 Prediction] [🧭 Direction]                      |
+--------------------------------------------------------------------------------------+
|  Hidden Data: [Anomaly Detection] [Clustering] [Hidden Patterns]                     |
+--------------------------------------------------------------------------------------+
|  Results:                                                                            |
|  +---------------------------------------------+                                     |
|  | Text/Chart/Result Area                      |                                     |
|  +---------------------------------------------+                                     |
+--------------------------------------------------------------------------------------+
| Status bar: Ready                                                                    |
+--------------------------------------------------------------------------------------+
```

#### 🤖 Behavior Prediction
```
+--------------------------------------------------------------------------------------+
| [📂 Data] [📊 Sample] [🕵️‍♂️ Hidden] [🤖 Prediction] [🧭 Direction]                      |
+--------------------------------------------------------------------------------------+
|  Prediction: [Train Model] [Predict Redshift] [Predict Magnitude]                    |
|  Params: RA [____] DEC [____]                                                        |
+--------------------------------------------------------------------------------------+
|  Results:                                                                            |
|  +---------------------------------------------+                                     |
|  | Text/Chart/Result Area                      |                                     |
|  +---------------------------------------------+                                     |
+--------------------------------------------------------------------------------------+
| Status bar: Ready                                                                    |
+--------------------------------------------------------------------------------------+
```

#### 🧭 Direction Analysis
```
+--------------------------------------------------------------------------------------+
| [📂 Data] [📊 Sample] [🕵️‍♂️ Hidden] [🤖 Prediction] [🧭 Direction]                      |
+--------------------------------------------------------------------------------------+
|  Direction: [Direction Analysis] [Velocity] [Trajectory]                             |
+--------------------------------------------------------------------------------------+
|  Results:                                                                            |
|  +---------------------------------------------+                                     |
|  | Text/Chart/Result Area                      |                                     |
|  +---------------------------------------------+                                     |
+--------------------------------------------------------------------------------------+
| Status bar: Ready                                                                    |
+--------------------------------------------------------------------------------------+
```

## 📸 Screenshots

![Dashboard](https://via.placeholder.com/800x450.png?text=AIS+Marine+Traffic+Analyzer+Dashboard)
![Risk Map](https://via.placeholder.com/800x450.png?text=Risk+Analysis+Map)

## 🔒 Security

- All data is processed locally
- No external API keys required
- No sensitive information is collected

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.