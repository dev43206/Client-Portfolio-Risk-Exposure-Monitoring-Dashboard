# Client Portfolio Risk & Exposure Monitoring Dashboard

An interactive financial risk analytics and client exposure monitoring platform built with **Python** and **Streamlit**.

The project combines **portfolio market-risk analytics** with a client-level **exposure and credit-limit monitoring module** backed by a **SQLite database**.

It uses historical market data from Yahoo Finance through `yfinance` and provides risk metrics such as volatility, Sharpe ratio, Value at Risk (VaR), drawdown, correlation, stress testing, and Monte Carlo simulation.

The client monitoring module extends the platform by storing client information, portfolio positions, credit limits, and exposure snapshots in a relational SQL database.

> **Note:** This is an educational risk analytics project. The exposure and credit-limit calculations are simplified and are not intended to represent production banking or regulatory risk models.

---

## Dashboard Overview

The platform has two major components:

### 1. Portfolio Risk Analytics

Analyzes market and portfolio risk using historical market data.

### 2. Client Exposure Monitoring

Monitors client portfolios against their assigned credit limits and provides a simplified risk classification.

```text
                    Financial Risk Platform
                            │
              ┌─────────────┴─────────────┐
              │                           │
              ▼                           ▼
       Portfolio Risk               Client Exposure
          Analytics                   Monitoring
              │                           │
      ┌───────┼────────┐          ┌───────┼────────┐
      ▼       ▼        ▼          ▼       ▼        ▼
     VaR   Volatility  Stress   Exposure Credit   Risk
                      Testing             Limit   Status
              │                           │
              └─────────────┬─────────────┘
                            ▼
                    Streamlit Dashboard
```

---

# Features

## Portfolio Risk Analytics

### Live Market Data

* Retrieves historical market data using `yfinance`
* Supports single and multi-asset portfolios
* Uses adjusted closing prices
* Handles invalid or unavailable tickers

### Return Analysis

* Daily returns
* Cumulative returns
* Portfolio returns
* Annualized returns

### Volatility

Calculates annualized volatility using:

```text
Annualized Volatility = Daily Return Std. Dev. × √252
```

### Sharpe Ratio

Calculates risk-adjusted performance using:

```text
Sharpe Ratio =
(Annualized Return − Risk-Free Rate)
/
Annualized Volatility
```

### Value at Risk (VaR)

Provides historical Value at Risk at a configurable confidence level.

For example:

```text
1-Day 95% VaR = 2%

```

This means that, based on the historical return distribution, losses greater than 2% occurred in approximately 5% of observations.

### Maximum Drawdown

Measures the largest peak-to-trough decline in portfolio value.

### Correlation Analysis

Provides a correlation matrix and heatmap showing how assets move relative to each other.

### Rolling Risk Metrics

Provides:

* Rolling volatility
* Rolling Sharpe ratio

This helps analyze how portfolio risk changes over time.

### Benchmark Analysis

Compares the portfolio against a selected benchmark and calculates:

* Beta
* Alpha
* Relative performance

### Risk Contribution

Decomposes portfolio volatility into the contribution of individual assets.

### Historical Stress Testing

Tests portfolio performance against historical market stress periods such as:

* COVID-19 market crash
* 2022 bear market

### Monte Carlo Simulation

Generates multiple simulated portfolio paths to estimate a range of possible future portfolio values.

### Efficient Frontier

Generates portfolios with different risk/return combinations and identifies portfolios with:

* Maximum Sharpe ratio
* Minimum volatility

### Fama-French Three-Factor Analysis

Analyzes portfolio returns using:

* Market factor
* SMB
* HML

---

# Client Exposure Monitoring

A new client-level exposure monitoring module has been added to extend the portfolio risk analytics functionality.

The module provides a simplified view of a client's financial exposure relative to an assigned credit limit.

## Client Information

Each client contains:

* Client ID
* Client name
* Risk profile
* Credit limit

Example:

```text
Client: ABC Capital
Risk Profile: Moderate
Credit Limit: $2,000,000
```

## Portfolio Positions

Each client can have multiple positions across different financial instruments.

Supported demonstration instruments include:

* Equities
* Bonds
* FX
* Options
* Interest Rate Swaps (IRS)

The project uses supplied market values for these positions rather than implementing complex derivative pricing models.

## Current Exposure

For the simplified project model:

```text
Current Exposure = max(Total Portfolio Market Value, 0)
```

This is an educational simplification used for demonstrating client exposure monitoring.

## Credit Utilization

Credit utilization is calculated as:

```text
Credit Utilization =
Current Exposure / Credit Limit × 100
```

Example:

```text
Current Exposure = $1,450,000
Credit Limit     = $2,000,000

Credit Utilization = 72.5%
```

## Available Credit

```text
Available Credit =
Credit Limit − Current Exposure
```

## Risk Classification

The dashboard uses simple project-defined thresholds:

| Utilization | Risk Status |
| ----------- | ----------- |
| < 50%       | LOW         |
| 50% – <80%  | MEDIUM      |
| 80% – <100% | HIGH        |
| ≥ 100%      | BREACH      |

These thresholds are **simplified educational rules** and are not intended to represent regulatory or institutional credit-risk limits.

---

# SQL Database

A SQLite database has been added to persist client and portfolio information.

The database stores:

```text
Clients
   ↓
Positions
   ↓
Exposure Snapshots
```

## Database Tables

### `clients`

Stores:

* Client ID
* Client name
* Risk profile
* Credit limit

### `positions`

Stores:

* Position ID
* Client ID
* Instrument
* Symbol
* Quantity
* Price
* Market value

### `exposure_snapshots`

Stores historical exposure-monitoring results:

* Snapshot ID
* Client ID
* Current exposure
* Credit limit
* Utilization
* Risk status
* Snapshot date

## Database Architecture

```text
                 SQLite Database
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
     clients       positions    exposure_snapshots
        │              │              │
        └──────────────┼──────────────┘
                       ▼
                Python SQL Layer
                       │
                       ▼
              Client Exposure Module
                       │
                       ▼
               Streamlit Dashboard
```

Parameterized SQL queries are used for retrieving and storing database information.

---

# Client Exposure Workflow

```text
Client Selection
       ↓
Retrieve Client Information
       ↓
Retrieve Portfolio Positions
       ↓
Calculate Portfolio Market Value
       ↓
Calculate Current Exposure
       ↓
Compare Against Credit Limit
       ↓
Calculate Credit Utilization
       ↓
Classify Risk Status
       ↓
Display Risk Dashboard
       ↓
Optionally Save Exposure Snapshot
```

---

# Technology Stack

### Programming

* **Python**

### Financial/Data Analysis

* **Pandas**
* **NumPy**
* **SciPy**

### Market Data

* **yfinance**

### Database

* **SQLite**
* **SQL**
* Python `sqlite3`

### Visualization

* **Plotly**

### Dashboard

* **Streamlit**

---

# Project Structure

```text
Client-Portfolio-Risk-Exposure-Monitoring/
│
├── app.py
│
├── src/
│   ├── data_loader.py
│   ├── metrics.py
│   └── factor_analysis.py
│
├── client_exposure/
│   ├── __init__.py
│   ├── models.py
│   ├── data.py
│   ├── calculations.py
│   ├── risk.py
│   ├── ui.py
│   └── README.md
│
├── database/
│   ├── __init__.py
│   ├── connection.py
│   ├── schema.sql
│   ├── seed.py
│   ├── queries.py
│   └── README.md
│
├── data/
│   └── risk_dashboard.db
│
├── requirements.txt
│
└── README.md
```

---

# Risk Metrics Explained

## Volatility

Measures how much asset returns fluctuate over time.

```text
Annualized Volatility =
Standard Deviation of Daily Returns × √252
```

Higher volatility indicates greater historical variation in returns.

## Sharpe Ratio

Measures excess return relative to volatility.

```text
Sharpe =
(Annualized Return − Risk-Free Rate)
/
Annualized Volatility
```

## Value at Risk

VaR estimates a loss threshold at a specified confidence level based on historical returns.

## Maximum Drawdown

Measures the largest decline from a historical portfolio peak to a subsequent trough.

## Correlation

Measures how two assets' returns move relative to each other.

Values range from:

```text
-1 → Perfect negative relationship
 0 → No linear relationship
+1 → Perfect positive relationship
```

## Monte Carlo Simulation

Generates multiple possible future portfolio paths based on historical return characteristics.

## Stress Testing

Evaluates how the portfolio would have behaved during historical market stress periods.

## Risk Contribution

Measures how much each asset contributes to overall portfolio volatility.

## Client Exposure

Measures the simplified current financial exposure of a client portfolio.

## Credit Utilization

Measures how much of the client's assigned credit limit is currently being used.

---

# Installation

## 1. Clone the Repository

```bash
git clone <your-repository-url>
cd Client-Portfolio-Risk-Exposure-Monitoring
```

## 2. Create a Virtual Environment

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

### Linux/macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## 4. Initialize the Database

```bash
python -m database.seed
```

This creates the SQLite database and inserts the demonstration client and portfolio data.

## 5. Run the Application

```bash
streamlit run app.py
```

The application will be available at:

```text
http://localhost:8501
```

---

# Example Client Risk View

```text
Client: ABC Capital

Credit Limit:       $2,000,000
Current Exposure:   $1,450,000
Available Credit:   $550,000
Utilization:        72.5%
Risk Status:        MEDIUM
```

Portfolio:

```text
Instrument       Market Value
--------------------------------
Equity             $800,000
Bond               $400,000
FX                 $150,000
Option              $50,000
IRS                 $50,000
--------------------------------
Total            $1,450,000
```

---

# Design Principles

The project follows a modular architecture:

```text
Data Layer
    ↓
Calculation Layer
    ↓
Risk Classification
    ↓
Database Layer
    ↓
Streamlit Presentation Layer
```

The client exposure module is kept separate from the original portfolio risk analytics to minimize changes to the existing application.

The SQL layer is responsible for persistence, while Python is responsible for risk calculations and business logic.

---

# Limitations

This project is intended for **educational and portfolio-demonstration purposes**.

The following are simplified and are **not production implementations**:

* Client exposure calculation
* Credit-risk thresholds
* Risk classification
* Derivative market values
* Portfolio assumptions

This project does **not** implement full:

* Potential Future Exposure (PFE)
* ISDA SIMM
* Regulatory Initial Margin
* Credit Valuation Adjustment (CVA)
* Full CDS pricing
* Full IRS valuation
* Production counterparty credit-risk models

These would require significantly more detailed market, legal, collateral and regulatory modeling.

---

# Future Improvements

Possible extensions include:

* Potential Future Exposure (PFE) calculation
* Initial Margin modeling
* Counterparty credit-risk simulation
* CVA calculation
* More detailed IRS and CDS valuation
* PostgreSQL support
* Automated daily risk reports
* Email/alert notifications
* Role-based access control
* Real-time exposure monitoring
* Excel/VBA reporting integration

---

# Disclaimer

This project is for **educational and portfolio-demonstration purposes only**.

It does not constitute financial advice, investment advice, or a production banking/financial risk-management system.
