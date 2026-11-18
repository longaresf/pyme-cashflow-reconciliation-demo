import pandas as pd
import pytest

from src.cashflow_model import (
    calculate_aging,
    calculate_dso,
    cash_at_30_days,
    project_cashflow,
)


def test_dso_uses_receivables_to_sales_ratio():
    assert calculate_dso(15_000, 45_000, 90) == 30.0
    assert calculate_dso(100, 0, 90) == 0.0


def test_aging_sums_open_balances_by_due_date():
    rows = pd.DataFrame(
        [
            {
                "invoice_id": "A",
                "due_date": "2025-07-01",
                "total_amount": 100,
                "bank_amount": 20,
            },
            {
                "invoice_id": "B",
                "due_date": "2025-05-15",
                "total_amount": 200,
                "bank_amount": 0,
            },
        ]
    )
    aging = calculate_aging(rows, as_of=pd.Timestamp("2025-07-01").date())
    amounts = dict(zip(aging["aging_bucket"].astype(str), aging["amount"]))
    assert amounts["Current"] == 80
    assert amounts["31-60 days"] == 200


def test_forecast_delinquency_reduces_expected_receipts():
    invoices = pd.DataFrame(
        [
            {
                "invoice_id": "A",
                "due_date": "2025-01-01",
                "total_amount": 1_000,
                "bank_amount": 0,
            }
        ]
    )
    bank = pd.DataFrame(columns=["value_date", "credit", "debit"])
    no_delinquency = project_cashflow(
        invoices,
        bank,
        expected_delinquency_pct=0,
        weeks=13,
        starting_cash=500,
        as_of=pd.Timestamp("2025-01-01").date(),
    )
    high_delinquency = project_cashflow(
        invoices,
        bank,
        expected_delinquency_pct=50,
        weeks=13,
        starting_cash=500,
        as_of=pd.Timestamp("2025-01-01").date(),
    )
    assert no_delinquency["projected_inflows"].sum() == 1_000
    assert high_delinquency["projected_inflows"].sum() == 500


def test_delinquency_bounds_are_validated():
    with pytest.raises(ValueError):
        project_cashflow(pd.DataFrame(), pd.DataFrame(), expected_delinquency_pct=110)


def test_30_day_cash_uses_exact_horizon_across_weekly_projection():
    projection = pd.DataFrame(
        {
            "net_cashflow": [70.0] * 5,
            "ending_cash": [170.0, 240.0, 310.0, 380.0, 450.0],
        }
    )
    assert cash_at_30_days(projection) == 400.0
