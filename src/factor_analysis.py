import io
import os
import random
import sys
import time
import urllib.error
import urllib.request
import zipfile

import numpy as np
import pandas as pd

if __package__ is None or __package__ == "":
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

from src.metrics import TRADING_DAYS

FAMA_FRENCH_URL = (
    "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"
    "F-F_Research_Data_Factors_daily_CSV.zip"
)

MAX_RETRIES = 3


def load_fama_french_factors(start, end):
    """Download and parse the Fama-French 3-factor daily dataset.

    Retries the download up to MAX_RETRIES times on failure, since cloud
    deployments occasionally see transient errors on the first attempt.
    Returns a DataFrame indexed by date with columns [Mkt-RF, SMB, HML, RF],
    expressed as decimals, filtered to the [start, end] range.
    """
    zip_bytes = None
    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with urllib.request.urlopen(FAMA_FRENCH_URL, timeout=30) as response:
                zip_bytes = response.read()
            if zip_bytes:
                break
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_error = exc
            zip_bytes = None

        if attempt < MAX_RETRIES:
            time.sleep(random.uniform(1.0, 2.0))

    if not zip_bytes:
        raise RuntimeError(
            f"Could not download Fama-French factor data after {MAX_RETRIES} attempts: {last_error}"
        )

    try:
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            csv_name = next(name for name in zf.namelist() if name.lower().endswith(".csv"))
            with zf.open(csv_name) as f:
                raw_text = f.read().decode("latin-1")
    except (zipfile.BadZipFile, StopIteration) as exc:
        raise RuntimeError(f"Could not read the Fama-French data archive: {exc}") from exc

    rows = []
    for line in raw_text.splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) >= 5 and parts[0].isdigit() and len(parts[0]) == 8:
            rows.append(parts[:5])

    if not rows:
        raise RuntimeError("No daily Fama-French data rows found in the downloaded file.")

    df = pd.DataFrame(rows, columns=["Date", "Mkt-RF", "SMB", "HML", "RF"])
    df["Date"] = pd.to_datetime(df["Date"], format="%Y%m%d")
    df = df.set_index("Date").sort_index()

    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce") / 100.0

    df = df.dropna()
    df = df.loc[str(start):str(end)]

    if df.empty:
        raise RuntimeError("No Fama-French factor data available for the selected date range.")

    return df


def factor_regression(portfolio_returns, factors):
    """OLS regression of portfolio excess returns on Mkt-RF, SMB, HML.

    Returns a dict with annualised alpha, the three factor betas, and R-squared.
    """
    aligned = pd.concat([portfolio_returns.rename("portfolio"), factors], axis=1, join="inner").dropna()

    if len(aligned) < 4:
        raise ValueError("Not enough overlapping observations between portfolio and factor data.")

    excess_returns = aligned["portfolio"] - aligned["RF"]
    factor_matrix = aligned[["Mkt-RF", "SMB", "HML"]].values
    design_matrix = np.column_stack([np.ones(len(factor_matrix)), factor_matrix])
    y = excess_returns.values

    coeffs, _, _, _ = np.linalg.lstsq(design_matrix, y, rcond=None)
    intercept, beta_mkt, beta_smb, beta_hml = coeffs

    y_pred = design_matrix @ coeffs
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - y.mean()) ** 2)
    r_squared = 1 - ss_res / ss_tot if ss_tot != 0 else 0.0

    return {
        "alpha": intercept * TRADING_DAYS,
        "beta_mkt": beta_mkt,
        "beta_smb": beta_smb,
        "beta_hml": beta_hml,
        "r_squared": r_squared,
    }