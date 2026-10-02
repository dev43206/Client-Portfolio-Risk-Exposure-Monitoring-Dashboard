from datetime import date

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.data_loader import load_prices
from src.factor_analysis import factor_regression, load_fama_french_factors
from src.optimization import optimize_max_sharpe, optimize_min_volatility
from src.metrics import (
    alpha,
    annualised_volatility,
    beta,
    cumulative_returns,
    daily_returns,
    drawdown_series,
    efficient_frontier,
    historical_var,
    max_drawdown,
    monte_carlo_simulation,
    portfolio_returns,
    risk_contribution,
    rolling_sharpe,
    rolling_volatility,
    sharpe_ratio,
    stress_test,
)
from client_exposure.ui import render_client_exposure

st.set_page_config(page_title="Financial Risk Dashboard", layout="wide")

STRESS_SCENARIOS = {
    "COVID Crash 2020": ("2020-02-19", "2020-03-23"),
    "2022 Bear Market": ("2022-01-01", "2022-10-12"),
}

PRESET_PORTFOLIOS = {
    "Big Tech": "AAPL, MSFT, GOOGL, AMZN, META",
    "Index Funds": "SPY, QQQ, VTI",
    "Balanced": "SPY, AAPL, JPM, JNJ, XOM",
}

COMMON_TICKERS = {
    "Apple": "AAPL",
    "Microsoft": "MSFT",
    "Alphabet (Google)": "GOOGL",
    "Amazon": "AMZN",
    "Meta (Facebook)": "META",
    "Tesla": "TSLA",
    "Nvidia": "NVDA",
    "Netflix": "NFLX",
    "Berkshire Hathaway": "BRK-B",
    "JPMorgan Chase": "JPM",
    "Johnson & Johnson": "JNJ",
    "ExxonMobil": "XOM",
    "Visa": "V",
    "Walmart": "WMT",
    "Procter & Gamble": "PG",
    "Coca-Cola": "KO",
    "Disney": "DIS",
    "S&P 500 ETF": "SPY",
    "Nasdaq 100 ETF": "QQQ",
    "Total US Market ETF": "VTI",
}


@st.cache_data
def get_prices(tickers, start, end):
    return load_prices(tickers, start, end)


@st.cache_data
def get_factors(start, end):
    return load_fama_french_factors(start, end)


def main():
    st.title("Financial Risk Dashboard")

    section = st.sidebar.radio(
        "Dashboard section",
        ["Portfolio Risk Dashboard", "Client Exposure Monitoring"],
    )
    if section == "Client Exposure Monitoring":
        render_client_exposure()
        return

    with st.sidebar:
        st.header("Portfolio Settings")

        if "tickers_input" not in st.session_state:
            st.session_state.tickers_input = "AAPL, MSFT, SPY"

        st.caption("Quick presets:")
        preset_cols = st.columns(len(PRESET_PORTFOLIOS))
        for col, (label, preset_tickers) in zip(preset_cols, PRESET_PORTFOLIOS.items()):
            if col.button(label, use_container_width=True):
                st.session_state.tickers_input = preset_tickers

        tickers_input = st.text_input("Tickers (comma separated)", key="tickers_input")
        tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]

        with st.expander("Common tickers reference"):
            reference_df = pd.DataFrame(
                {"Ticker": list(COMMON_TICKERS.values())},
                index=pd.Index(list(COMMON_TICKERS.keys()), name="Company"),
            )
            st.dataframe(reference_df, use_container_width=True)

        default_start = date(2019, 1, 1)
        start_date = st.date_input("Start date", value=default_start)
        end_date = st.date_input("End date", value=date.today())

        st.subheader("Weights")
        weights = []
        for ticker in tickers:
            w = st.number_input(
                f"{ticker} weight",
                min_value=0.0,
                max_value=1.0,
                value=round(1 / len(tickers), 2) if tickers else 0.0,
                step=0.05,
                key=f"weight_{ticker}",
            )
            weights.append(w)

        rf_rate = st.slider("Risk-free rate (annual)", min_value=0.0, max_value=0.10, value=0.02, step=0.005, format="%.3f")
        var_confidence = st.slider("VaR confidence level", min_value=0.90, max_value=0.99, value=0.95, step=0.01)

        st.subheader("Benchmark")
        benchmark_ticker = st.text_input("Benchmark ticker", value="SPY").strip().upper()

    if not tickers:
        st.info("Enter at least one ticker to begin.")
        return

    if sum(weights) == 0:
        st.warning("Weights sum to zero — please assign at least one positive weight.")
        return

    if start_date >= end_date:
        st.warning("Start date must be before end date.")
        return

    try:
        prices = get_prices(tickers, start_date, end_date)
    except Exception as exc:
        st.error(
            f"Failed to load price data: {exc}\n\n"
            "Double-check that your ticker symbols are correct — see the 'Common tickers "
            "reference' in the sidebar, or click one of the quick preset buttons above."
        )
        return

    missing = [t for t in tickers if t not in prices.columns]
    if missing:
        st.warning(
            f"No data found for: {', '.join(missing)}. They will be excluded from the analysis. "
            "Check the spelling against the 'Common tickers reference' in the sidebar, or try a "
            "preset portfolio if you're not sure what to enter."
        )
        prices = prices.drop(columns=missing, errors="ignore")
        tickers = [t for t in tickers if t in prices.columns]
        weights = [w for t, w in zip(tickers, weights)]

    if prices.empty or not tickers:
        st.error(
            "No valid price data available for the selected tickers/date range. "
            "Try one of the quick preset portfolios in the sidebar, or check the 'Common "
            "tickers reference' for valid symbols."
        )
        return

    returns = daily_returns(prices)
    port_returns = portfolio_returns(returns, weights)

    annual_return = port_returns.mean() * 252
    annual_vol = annualised_volatility(port_returns)
    sharpe = sharpe_ratio(port_returns, rf=rf_rate)
    var_value = historical_var(port_returns, confidence=var_confidence)
    mdd = max_drawdown(port_returns)

    (
        tab_overview,
        tab_risk,
        tab_rolling,
        tab_benchmark,
        tab_risk_contrib,
        tab_stress,
        tab_monte_carlo,
        tab_frontier,
        tab_optimization,
        tab_factor,
    ) = st.tabs(
        [
            "Overview",
            "Risk",
            "Rolling Metrics",
            "Benchmark",
            "Risk Contribution",
            "Stress Test",
            "Monte Carlo",
            "Efficient Frontier",
            "Optimization",
            "Factor Analysis",
        ]
    )

    with tab_overview:
        st.caption("A snapshot of overall portfolio performance and key risk metrics.")
        st.subheader("Portfolio KPIs")
        cols = st.columns(5)
        cols[0].metric("Annualised Return", f"{annual_return:.2%}")
        cols[1].metric("Annualised Volatility", f"{annual_vol:.2%}")
        cols[2].metric("Sharpe Ratio", f"{sharpe:.2f}")
        cols[3].metric(f"VaR ({var_confidence:.0%})", f"{var_value:.2%}")
        cols[4].metric("Max Drawdown", f"{mdd:.2%}")

        st.subheader("Cumulative Returns")
        cum_returns = cumulative_returns(returns)
        fig_cum = go.Figure()
        for ticker in cum_returns.columns:
            fig_cum.add_trace(go.Scatter(x=cum_returns.index, y=cum_returns[ticker], mode="lines", name=ticker))
        port_cum = cumulative_returns(port_returns)
        fig_cum.add_trace(go.Scatter(x=port_cum.index, y=port_cum, mode="lines", name="Portfolio", line=dict(width=3, dash="dash")))
        fig_cum.update_layout(yaxis_tickformat=".0%", xaxis_title="Date", yaxis_title="Cumulative Return")
        st.plotly_chart(fig_cum, use_container_width=True)

    with tab_risk:
        st.caption("Drawdown history, cross-asset correlation, and a per-asset risk breakdown.")
        col_left, col_right = st.columns(2)

        with col_left:
            st.subheader("Portfolio Drawdown")
            dd = drawdown_series(port_returns)
            fig_dd = go.Figure()
            fig_dd.add_trace(go.Scatter(x=dd.index, y=dd, mode="lines", fill="tozeroy", name="Drawdown", line=dict(color="firebrick")))
            fig_dd.update_layout(yaxis_tickformat=".0%", xaxis_title="Date", yaxis_title="Drawdown")
            st.plotly_chart(fig_dd, use_container_width=True)

        with col_right:
            st.subheader("Correlation Heatmap")
            corr = returns.corr()
            fig_corr = go.Figure(
                data=go.Heatmap(
                    z=corr.values,
                    x=corr.columns,
                    y=corr.columns,
                    colorscale="RdBu_r",
                    zmin=-1,
                    zmax=1,
                    text=np.round(corr.values, 2),
                    texttemplate="%{text}",
                )
            )
            st.plotly_chart(fig_corr, use_container_width=True)

        st.subheader("Per-Asset Risk Metrics")
        asset_vol = annualised_volatility(returns)
        asset_sharpe = returns.apply(lambda col: sharpe_ratio(col, rf=rf_rate))
        asset_var = returns.apply(lambda col: historical_var(col, confidence=var_confidence))
        asset_mdd = returns.apply(lambda col: max_drawdown(col))

        metrics_df = pd.DataFrame(
            {
                "Volatility": asset_vol,
                "Sharpe": asset_sharpe,
                "VaR": asset_var,
                "Max Drawdown": asset_mdd,
            }
        )

        fig_bar = go.Figure()
        for metric in metrics_df.columns:
            fig_bar.add_trace(go.Bar(x=metrics_df.index, y=metrics_df[metric], name=metric))
        fig_bar.update_layout(barmode="group", xaxis_title="Asset", yaxis_title="Value")
        st.plotly_chart(fig_bar, use_container_width=True)

    with tab_rolling:
        st.caption("How the portfolio's risk and risk-adjusted return have evolved over time.")
        rolling_window = st.slider("Rolling window (trading days)", min_value=21, max_value=252, value=63, step=1)

        if len(port_returns) <= rolling_window:
            st.warning("Not enough history for this rolling window — choose a smaller window or a wider date range.")
        else:
            roll_vol = rolling_volatility(port_returns, window=rolling_window)
            roll_sharpe = rolling_sharpe(port_returns, window=rolling_window, rf=rf_rate)

            st.subheader("Rolling Annualised Volatility")
            fig_roll_vol = go.Figure()
            fig_roll_vol.add_trace(go.Scatter(x=roll_vol.index, y=roll_vol, mode="lines", name="Rolling Volatility"))
            fig_roll_vol.update_layout(yaxis_tickformat=".0%", xaxis_title="Date", yaxis_title="Annualised Volatility")
            st.plotly_chart(fig_roll_vol, use_container_width=True)

            st.subheader("Rolling Sharpe Ratio")
            fig_roll_sharpe = go.Figure()
            fig_roll_sharpe.add_trace(go.Scatter(x=roll_sharpe.index, y=roll_sharpe, mode="lines", name="Rolling Sharpe"))
            fig_roll_sharpe.update_layout(xaxis_title="Date", yaxis_title="Sharpe Ratio")
            st.plotly_chart(fig_roll_sharpe, use_container_width=True)

    with tab_benchmark:
        st.caption("Portfolio performance versus a benchmark, with annualised Alpha and Beta.")
        if not benchmark_ticker:
            st.info("Enter a benchmark ticker in the sidebar to compare against.")
        else:
            try:
                benchmark_prices = get_prices([benchmark_ticker], start_date, end_date)
            except Exception as exc:
                st.error(
                    f"Failed to load benchmark data: {exc}\n\n"
                    "Double-check the benchmark ticker symbol — see the 'Common tickers "
                    "reference' in the sidebar (e.g. SPY, QQQ, VTI are common benchmarks)."
                )
                benchmark_prices = None

            if benchmark_prices is not None:
                if benchmark_ticker not in benchmark_prices.columns:
                    st.warning(
                        f"No data found for benchmark '{benchmark_ticker}'. Check the spelling, "
                        "or try a common benchmark like SPY, QQQ, or VTI."
                    )
                else:
                    benchmark_returns = daily_returns(benchmark_prices)[benchmark_ticker]
                    aligned = pd.concat([port_returns, benchmark_returns], axis=1, join="inner")
                    aligned.columns = ["Portfolio", "Benchmark"]

                    if aligned.empty:
                        st.warning("No overlapping dates between the portfolio and the benchmark.")
                    else:
                        port_aligned = aligned["Portfolio"]
                        bench_aligned = aligned["Benchmark"]

                        beta_value = beta(port_aligned, bench_aligned)
                        alpha_value = alpha(port_aligned, bench_aligned, rf=rf_rate)

                        st.subheader(f"Portfolio vs {benchmark_ticker}")
                        bcols = st.columns(2)
                        bcols[0].metric("Alpha (annualised)", f"{alpha_value:.2%}")
                        bcols[1].metric("Beta", f"{beta_value:.2f}")

                        cum_port = cumulative_returns(port_aligned)
                        cum_bench = cumulative_returns(bench_aligned)
                        fig_bench = go.Figure()
                        fig_bench.add_trace(go.Scatter(x=cum_port.index, y=cum_port, mode="lines", name="Portfolio"))
                        fig_bench.add_trace(go.Scatter(x=cum_bench.index, y=cum_bench, mode="lines", name=benchmark_ticker))
                        fig_bench.update_layout(yaxis_tickformat=".0%", xaxis_title="Date", yaxis_title="Cumulative Return")
                        st.plotly_chart(fig_bench, use_container_width=True)

    with tab_risk_contrib:
        st.caption("How much each asset contributes to total portfolio risk, versus its capital weight.")
        try:
            rc = risk_contribution(returns, weights)
            total_rc = rc.sum()

            weights_arr = np.array(weights, dtype=float)
            weights_norm = weights_arr / weights_arr.sum()
            rc_share = rc / total_rc if total_rc != 0 else rc * 0

            st.subheader("Risk Contribution by Asset")
            fig_rc = go.Figure(go.Bar(x=rc.values, y=rc.index, orientation="h"))
            fig_rc.update_layout(xaxis_tickformat=".1%", xaxis_title="Annualised Risk Contribution", yaxis_title="Asset")
            st.plotly_chart(fig_rc, use_container_width=True)

            st.subheader("Weight vs. Share of Portfolio Risk")
            comparison_df = pd.DataFrame(
                {"Weight": weights_norm, "Risk Contribution %": rc_share.values},
                index=rc.index,
            )
            st.dataframe(comparison_df.style.format("{:.2%}"), use_container_width=True)

            if len(tickers) < 2:
                st.caption("With a single asset, it carries 100% of portfolio risk by definition.")
        except Exception as exc:
            st.error(f"Failed to compute risk contribution: {exc}")

    with tab_stress:
        st.caption("How the portfolio would have performed during past extreme market scenarios.")
        try:
            stress_results = stress_test(returns, weights, STRESS_SCENARIOS)
            valid_results = {name: value for name, value in stress_results.items() if value is not None}
            missing_scenarios = [name for name, value in stress_results.items() if value is None]

            if not valid_results:
                st.info("None of the loaded price history overlaps with the predefined stress scenarios.")
            else:
                st.subheader("Portfolio Return During Historical Stress Scenarios")
                names = list(valid_results.keys())
                values = list(valid_results.values())
                colors = ["crimson" if v < 0 else "seagreen" for v in values]

                fig_stress = go.Figure(go.Bar(x=names, y=values, marker_color=colors, width=0.45))
                fig_stress.update_layout(
                    yaxis_tickformat=".1%",
                    xaxis_title="Scenario",
                    yaxis_title="Portfolio Return",
                    height=320 if len(names) == 1 else 420,
                )
                st.plotly_chart(fig_stress, use_container_width=True)

                for name in names:
                    start, end = STRESS_SCENARIOS[name]
                    st.caption(f"**{name}**: {start} to {end}")

            if missing_scenarios:
                st.warning(
                    f"No overlapping data for: {', '.join(missing_scenarios)} "
                    "(outside the selected date range)."
                )
        except Exception as exc:
            st.error(f"Failed to run stress test: {exc}")

    with tab_monte_carlo:
        st.caption("A distribution of possible future outcomes, based on thousands of simulated paths.")
        mc_cols = st.columns(2)
        n_simulations = mc_cols[0].slider("Number of simulations", min_value=100, max_value=2000, value=500, step=100)
        n_days = mc_cols[1].slider("Number of days", min_value=30, max_value=504, value=252, step=1)

        try:
            sim_paths = monte_carlo_simulation(returns, weights, n_simulations=n_simulations, n_days=n_days)

            st.subheader("Simulated Portfolio Value Paths")
            x_combined, y_combined = [], []
            for col in sim_paths.columns:
                x_combined.extend(sim_paths.index.tolist())
                y_combined.extend(sim_paths[col].tolist())
                x_combined.append(None)
                y_combined.append(None)

            fig_mc = go.Figure()
            fig_mc.add_trace(
                go.Scatter(
                    x=x_combined,
                    y=y_combined,
                    mode="lines",
                    line=dict(width=1, color="rgba(31,119,180,0.08)"),
                    showlegend=False,
                    hoverinfo="skip",
                )
            )
            fig_mc.update_layout(xaxis_title="Day", yaxis_title="Portfolio Value (starting at 1.0)")
            st.plotly_chart(fig_mc, use_container_width=True)

            final_values = sim_paths.iloc[-1]

            st.subheader("Distribution of Simulated Final Values")
            fig_hist = go.Figure(go.Histogram(x=final_values, nbinsx=50))
            fig_hist.update_layout(xaxis_title="Final Portfolio Value", yaxis_title="Frequency")
            st.plotly_chart(fig_hist, use_container_width=True)

            p5 = np.percentile(final_values, 5)
            p50 = np.percentile(final_values, 50)
            p95 = np.percentile(final_values, 95)

            st.subheader("Final Value Percentiles")
            pcols = st.columns(3)
            pcols[0].metric("5th Percentile", f"{p5:.2f}")
            pcols[1].metric("Median", f"{p50:.2f}")
            pcols[2].metric("95th Percentile", f"{p95:.2f}")
        except Exception as exc:
            st.error(f"Failed to run Monte Carlo simulation: {exc}")

    with tab_frontier:
        st.caption("Portfolio optimisation — the best possible risk/return combinations for these assets.")
        if len(tickers) < 2:
            st.info(
                "The efficient frontier needs at least two assets — with a single asset, every "
                "portfolio is the same point, so there is no frontier to plot."
            )
        else:
            try:
                frontier_df, max_sharpe_portfolio, min_vol_portfolio = efficient_frontier(
                    returns, n_portfolios=5000, rf=rf_rate
                )

                st.subheader("Simulated Portfolios")
                fig_frontier = go.Figure()
                fig_frontier.add_trace(
                    go.Scatter(
                        x=frontier_df["volatility"],
                        y=frontier_df["return"],
                        mode="markers",
                        marker=dict(
                            size=4,
                            color=frontier_df["sharpe"],
                            colorscale="Viridis",
                            showscale=True,
                            colorbar=dict(title="Sharpe", x=1.02, xpad=10),
                        ),
                        name="Simulated Portfolios",
                        hoverinfo="skip",
                    )
                )
                fig_frontier.add_trace(
                    go.Scatter(
                        x=[max_sharpe_portfolio["volatility"]],
                        y=[max_sharpe_portfolio["return"]],
                        mode="markers",
                        marker=dict(size=18, color="gold", symbol="star", line=dict(width=1, color="black")),
                        name="Max Sharpe",
                    )
                )
                fig_frontier.add_trace(
                    go.Scatter(
                        x=[min_vol_portfolio["volatility"]],
                        y=[min_vol_portfolio["return"]],
                        mode="markers",
                        marker=dict(size=16, color="cyan", symbol="star", line=dict(width=1, color="black")),
                        name="Min Volatility",
                    )
                )
                fig_frontier.add_trace(
                    go.Scatter(
                        x=[annual_vol],
                        y=[annual_return],
                        mode="markers",
                        marker=dict(size=14, color="red", symbol="diamond", line=dict(width=1, color="black")),
                        name="Your Portfolio",
                    )
                )
                fig_frontier.update_layout(
                    xaxis_title="Annualised Volatility",
                    yaxis_title="Annualised Return",
                    xaxis_tickformat=".0%",
                    yaxis_tickformat=".0%",
                    legend=dict(orientation="h", yanchor="bottom", y=-0.35, xanchor="center", x=0.5),
                    margin=dict(b=110, r=80),
                )
                st.plotly_chart(fig_frontier, use_container_width=True)

                st.subheader("Optimal Portfolios")
                opt_cols = st.columns(2)
                opt_labels = ["Max Sharpe Portfolio", "Min Volatility Portfolio"]
                opt_portfolios = [max_sharpe_portfolio, min_vol_portfolio]
                for col, label, portfolio in zip(opt_cols, opt_labels, opt_portfolios):
                    with col:
                        st.markdown(f"**{label}**")
                        st.metric("Return", f"{portfolio['return']:.2%}")
                        st.metric("Volatility", f"{portfolio['volatility']:.2%}")
                        st.metric("Sharpe", f"{portfolio['sharpe']:.2f}")
                        weight_df = pd.DataFrame(
                            {"Weight": [portfolio[f"weight_{t}"] for t in tickers]}, index=tickers
                        )
                        st.dataframe(weight_df.style.format("{:.1%}"), use_container_width=True)
            except Exception as exc:
                st.error(f"Failed to compute the efficient frontier: {exc}")

    with tab_optimization:
        st.caption("Find the optimal allocation that maximizes the Sharpe ratio or minimizes volatility for these assets.")

        obj = st.radio(
            "Optimization objective",
            ["Max Sharpe Ratio", "Min Volatility"],
            horizontal=True,
        )

        if len(tickers) == 1:
            st.info(
                f"Single-asset portfolio: the only possible allocation is 100% in {tickers[0]}. "
                "Metrics below reflect that allocation."
            )

        try:
            if obj == "Max Sharpe Ratio":
                opt_weights, opt_ret, opt_vol, opt_sharpe = optimize_max_sharpe(returns, rf=rf_rate)
            else:
                opt_weights, opt_ret, opt_vol, opt_sharpe = optimize_min_volatility(returns, rf=rf_rate)

            weights_arr = np.array(weights, dtype=float)
            current_weights = weights_arr / weights_arr.sum()

            st.subheader("Current Portfolio")
            cur_cols = st.columns(3)
            cur_cols[0].metric("Annualised Return", f"{annual_return:.2%}")
            cur_cols[1].metric("Annualised Volatility", f"{annual_vol:.2%}")
            cur_cols[2].metric("Sharpe Ratio", f"{sharpe:.2f}")

            st.subheader("Optimized Portfolio")
            opt_cols = st.columns(3)
            opt_cols[0].metric(
                "Annualised Return",
                f"{opt_ret:.2%}",
                delta=f"{opt_ret - annual_return:+.2%}",
            )
            opt_cols[1].metric(
                "Annualised Volatility",
                f"{opt_vol:.2%}",
                delta=f"{opt_vol - annual_vol:+.2%}",
                delta_color="inverse",
            )
            opt_cols[2].metric(
                "Sharpe Ratio",
                f"{opt_sharpe:.2f}",
                delta=f"{opt_sharpe - sharpe:+.2f}",
            )

            st.subheader("Weight Comparison")
            weight_df = pd.DataFrame(
                {
                    "Current Weight": current_weights,
                    "Optimized Weight": opt_weights,
                    "Change": opt_weights - current_weights,
                },
                index=tickers,
            )
            st.dataframe(
                weight_df.style.format(
                    {"Current Weight": "{:.1%}", "Optimized Weight": "{:.1%}", "Change": "{:+.1%}"}
                ),
                use_container_width=True,
            )

            st.subheader("Rebalancing Suggestions")
            threshold = 0.01
            for ticker, curr_w, opt_w in zip(tickers, current_weights, opt_weights):
                diff = opt_w - curr_w
                if diff > threshold:
                    st.markdown(f"- **{ticker}**: Increase from {curr_w:.1%} → {opt_w:.1%} ({diff:+.1%})")
                elif diff < -threshold:
                    st.markdown(f"- **{ticker}**: Reduce from {curr_w:.1%} → {opt_w:.1%} ({diff:+.1%})")
                else:
                    st.markdown(f"- **{ticker}**: Maintain current allocation (~{opt_w:.1%})")

            st.caption(
                "_For educational purposes only, not financial advice. "
                "Past data does not guarantee future results._"
            )

        except Exception as exc:
            st.error(f"Optimization failed: {exc}")

    with tab_factor:
        st.caption("Fama-French three-factor attribution: how much of the portfolio's return comes from Market, SMB, and HML exposure.")
        try:
            factors = get_factors(start_date, end_date)
            result = factor_regression(port_returns, factors)

            st.subheader("Fama-French Three-Factor Regression")
            fcols = st.columns(5)
            fcols[0].metric("Alpha (annualised)", f"{result['alpha']:.2%}")
            fcols[1].metric("Market Beta", f"{result['beta_mkt']:.2f}")
            fcols[2].metric("SMB Beta", f"{result['beta_smb']:.2f}")
            fcols[3].metric("HML Beta", f"{result['beta_hml']:.2f}")
            fcols[4].metric("R-squared", f"{result['r_squared']:.2f}")

            st.subheader("Factor Exposures")
            fig_factors = go.Figure(
                go.Bar(
                    x=["Market (Mkt-RF)", "SMB", "HML"],
                    y=[result["beta_mkt"], result["beta_smb"], result["beta_hml"]],
                )
            )
            fig_factors.update_layout(xaxis_title="Factor", yaxis_title="Beta (Loading)")
            st.plotly_chart(fig_factors, use_container_width=True)

            st.markdown(
                "- **Market (Mkt-RF)**: sensitivity to overall stock market risk — a beta above 1 means the "
                "portfolio amplifies market moves, below 1 means it's more defensive.\n"
                "- **SMB (Small Minus Big)**: exposure to small-cap stocks versus large-cap stocks — a "
                "positive loading means the portfolio behaves more like small-cap stocks.\n"
                "- **HML (High Minus Low)**: exposure to value stocks versus growth stocks — a positive "
                "loading means the portfolio tilts toward cheap/value stocks rather than growth stocks."
            )
        except Exception as exc:
            st.error(f"Failed to run factor analysis: {exc}")


if __name__ == "__main__":
    main()
