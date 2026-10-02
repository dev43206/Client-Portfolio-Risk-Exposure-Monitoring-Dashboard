# Client Exposure Monitoring

An isolated, educational Streamlit section that summarizes client portfolio market values against assigned credit limits. It uses the supplied position market values and does not price instruments.

## Architecture

- `models.py`: typed `Client` and `Position` records.
- `data.py`: deterministic sample clients and positions as Pandas DataFrames.
- `calculations.py`: portfolio exposure, credit utilization, available credit, and client summary calculations.
- `risk.py`: transparent utilization threshold classification.
- `ui.py`: selector, KPIs, summary and positions tables, and limit comparison chart.
- `app.py`: adds the section to existing sidebar navigation; the original dashboard remains on its existing path.

## Formulas and assumptions

- Portfolio market value is the sum of supplied position `market_value` values.
- Current exposure is `max(total portfolio market value, 0)`. This is a simplified educational assumption, not a counterparty exposure model.
- Utilization is `current_exposure / credit_limit * 100`. For a zero or negative credit limit, utilization is reported as 0% to avoid division by zero; this does not imply a valid line of credit.
- Available credit is `credit_limit - current_exposure` and can be negative.
- Risk status: `<50% LOW`, `50% to <80% MEDIUM`, `80% to <100% HIGH`, and `>=100% BREACH`.
- Risk profile (Conservative, Moderate, Aggressive) is a client classification, not a prediction.

## Example output

The included ABC Capital sample has a $1,000,000 credit limit and $710,000 exposure, giving 71% utilization and MEDIUM status, with $290,000 available credit.

## Integration and limitations

Choose **Client Exposure Monitoring** in the sidebar to display the sample view. Select **Portfolio Risk Dashboard** for the existing financial analysis. Supported instrument labels include Equity, Bond, FX, Option, and IRS; all use supplied market values. This module does not implement PFE, ISDA SIMM, regulatory initial margin, production counterparty credit risk, or real derivatives pricing.
