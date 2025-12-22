# Commercial Investment Financial Analysis Application

A Streamlit-based application for detailed investment feasibility analysis, supporting both Levered and Unlevered valuation methods.

## Features
- **Project Structure**: SQLite database with JSON import/export.
- **Financial Modeling**: CAPEX, OPEX, Revenue, detailed Loan schedules, Leasing, Grants.
- **Analysis**: NPV, IRR, Payback, Sensitivity Analysis, Monte Carlo Simulation.
- **Reporting**: P&L, Cash Flow, Balance Sheet (simplified), PDF/Excel exports.

## Installation
1.  Create a virtual environment: `python -m venv .venv`
2.  Activate it: `source .venv/bin/activate` (or `.venv\Scripts\activate` on Windows)
3.  Install dependencies: `pip install -r requirements.txt`

## Running
`streamlit run app.py`

## Testing
`pytest`
