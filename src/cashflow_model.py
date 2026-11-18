"""Receivables aging, DSO, and a 13-week liquidity projection."""

from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import pandas as pd


def calculate_dso(
    accounts_receivable: float,
    credit_sales: float,
    period_days: int = 90,
) -> float:
    """Calculate days sales outstanding as receivables / credit sales * period days."""
    if credit_sales <= 0 or period_days <= 0:
        return 0.0
    return round(
        max(0.0, float(accounts_receivable)) / float(credit_sales) * period_days, 2
    )


def calculate_aging(
    reconciliation: pd.DataFrame,
    *,
    as_of: date | None = None,
) -> pd.DataFrame:
    """Aggregate open invoice balances into standard receivables aging buckets."""
    today = pd.Timestamp(as_of or date.today()).normalize()
    data = reconciliation.copy()
    data["due_date"] = pd.to_datetime(data["due_date"], errors="coerce")
    data["outstanding_amount"] = (
        pd.to_numeric(data["total_amount"], errors="coerce").fillna(0)
        - pd.to_numeric(data["bank_amount"], errors="coerce").fillna(0)
    ).clip(lower=0)
    data = data[data["outstanding_amount"] > 0]
    days_overdue = (today - data["due_date"]).dt.days.clip(lower=0)
    data["aging_bucket"] = pd.cut(
        days_overdue,
        bins=[-1, 0, 30, 60, 90, np.inf],
        labels=["Current", "1-30 days", "31-60 days", "61-90 days", "90+ days"],
    )
    buckets = ["Current", "1-30 days", "31-60 days", "61-90 days", "90+ days"]
    return (
        data.groupby("aging_bucket", observed=False)["outstanding_amount"]
        .sum()
        .reindex(buckets, fill_value=0)
        .rename("amount")
        .reset_index()
    )


def project_cashflow(
    reconciliation: pd.DataFrame,
    bank: pd.DataFrame,
    *,
    expected_delinquency_pct: float = 10.0,
    weeks: int = 13,
    starting_cash: float | None = None,
    as_of: date | None = None,
) -> pd.DataFrame:
    """Forecast weekly cash by expected collections less the recent bank debit run rate."""
    if not 0 <= expected_delinquency_pct <= 100:
        raise ValueError("Expected delinquency must be between 0 and 100 percent.")
    if weeks <= 0:
        raise ValueError("The projection horizon must contain at least one week.")
    today = pd.Timestamp(as_of or date.today()).normalize()
    bank_data = bank.copy()
    bank_data["value_date"] = pd.to_datetime(bank_data["value_date"], errors="coerce")
    bank_data["credit"] = pd.to_numeric(bank_data["credit"], errors="coerce").fillna(0)
    bank_data["debit"] = pd.to_numeric(bank_data["debit"], errors="coerce").fillna(0)
    if starting_cash is None:
        starting_cash = max(
            0.0,
            25_000.0
            + float(bank_data["credit"].sum())
            - float(bank_data["debit"].sum()),
        )

    recent_start = today - timedelta(days=90)
    recent_debits = bank_data.loc[
        bank_data["value_date"].between(recent_start, today), "debit"
    ].sum()
    weekly_outflows = float(recent_debits) / 13.0

    invoices = reconciliation.copy()
    invoices["due_date"] = pd.to_datetime(invoices["due_date"], errors="coerce")
    invoices["total_amount"] = pd.to_numeric(
        invoices["total_amount"], errors="coerce"
    ).fillna(0)
    invoices["bank_amount"] = pd.to_numeric(
        invoices["bank_amount"], errors="coerce"
    ).fillna(0)
    invoices["outstanding"] = (invoices["total_amount"] - invoices["bank_amount"]).clip(
        lower=0
    )
    invoices = invoices[invoices["outstanding"] > 0].copy()
    delay_days = round(21 * expected_delinquency_pct / 100)
    invoices["expected_date"] = invoices["due_date"].apply(
        lambda due: max(due, today) + timedelta(days=delay_days)
    )
    invoices["expected_receipt"] = invoices["outstanding"] * (
        1 - expected_delinquency_pct / 100
    )

    first_week = today
    week_starts = [first_week + timedelta(weeks=index) for index in range(weeks)]
    records: list[dict[str, object]] = []
    balance = float(starting_cash)
    for week_start in week_starts:
        week_end = week_start + timedelta(days=6)
        inflows = invoices.loc[
            invoices["expected_date"].between(week_start, week_end), "expected_receipt"
        ].sum()
        outflows = weekly_outflows
        balance += float(inflows) - outflows
        records.append(
            {
                "week_start": week_start.date(),
                "projected_inflows": round(float(inflows), 2),
                "projected_outflows": round(float(outflows), 2),
                "net_cashflow": round(float(inflows) - outflows, 2),
                "ending_cash": round(balance, 2),
            }
        )
    return pd.DataFrame(records)


def cash_at_30_days(projection: pd.DataFrame) -> float:
    """Estimate cash after 30 days by prorating the weekly net-cashflow profile."""
    if projection.empty:
        return 0.0
    opening_cash = float(
        projection.iloc[0]["ending_cash"] - projection.iloc[0]["net_cashflow"]
    )
    remaining_days = min(30, len(projection) * 7)
    forecast_net = 0.0
    for row in projection.itertuples(index=False):
        days_in_period = min(7, remaining_days)
        if days_in_period <= 0:
            break
        forecast_net += float(row.net_cashflow) * days_in_period / 7
        remaining_days -= days_in_period
    return round(opening_cash + forecast_net, 2)
