import pandas as pd

from src.data_loader import build_sources
from src.reconciler import reconcile


def _tax_row(invoice_id="INV-00001", amount=100.0, due_date="2025-01-31"):
    return {
        "invoice_id": invoice_id,
        "customer_id": "CUST-0001",
        "invoice_date": "2025-01-01",
        "due_date": due_date,
        "total_amount": amount,
    }


def _erp_row(invoice_id="INV-00001", amount=100.0, entry_date="2025-01-01"):
    return {"invoice_id": invoice_id, "total_amount": amount, "entry_date": entry_date}


def _bank_row(amount=100.0, details="INV-00001:100.00", value_date="2025-01-31"):
    return {
        "transaction_id": "BNK-00001",
        "value_date": value_date,
        "credit": amount,
        "debit": 0.0,
        "remittance_details": details,
    }


def test_exact_three_way_match_is_reconciled():
    result = reconcile(
        pd.DataFrame([_tax_row()]),
        pd.DataFrame([_erp_row()]),
        pd.DataFrame([_bank_row()]),
    )
    invoice = result.invoices.iloc[0]
    assert invoice["reconciliation_status"] == "reconciled"
    assert invoice["bank_match_method"] == "reference"
    assert invoice["automatically_matched"]


def test_fuzzy_match_requires_amount_and_date_window():
    result = reconcile(
        pd.DataFrame([_tax_row()]),
        pd.DataFrame([_erp_row()]),
        pd.DataFrame([_bank_row(amount=100.4, details="", value_date="2025-02-02")]),
    )
    assert result.invoices.iloc[0]["reconciliation_status"] == "reconciled"
    assert result.invoices.iloc[0]["bank_match_method"] == "fuzzy"


def test_out_of_window_unidentified_transfer_remains_unmatched():
    result = reconcile(
        pd.DataFrame([_tax_row()]),
        pd.DataFrame([_erp_row()]),
        pd.DataFrame([_bank_row(details="", value_date="2025-03-20")]),
    )
    assert result.invoices.iloc[0]["reconciliation_status"] == "unpaid"
    assert len(result.unmatched_bank) == 1


def test_erp_omission_is_reported_as_exception():
    result = reconcile(
        pd.DataFrame([_tax_row()]),
        pd.DataFrame(columns=["invoice_id", "total_amount", "entry_date"]),
        pd.DataFrame(),
    )
    assert result.invoices.iloc[0]["reconciliation_status"] == "erp_missing"


def test_generator_injects_five_percent_mixed_erp_anomalies(monkeypatch):
    monkeypatch.delenv("KAGGLE_DATASET", raising=False)
    monkeypatch.delenv("KAGGLE_USERNAME", raising=False)
    monkeypatch.delenv("KAGGLE_KEY", raising=False)
    sii, erp, _ = build_sources(
        invoice_count=60,
        seed=7,
        reference_date=pd.Timestamp("2025-01-01"),
    )
    merged = sii.merge(erp, on="invoice_id", suffixes=("_sii", "_erp"))
    missing_count = len(sii) - len(erp)
    amount_difference_count = (
        merged["total_amount_sii"] != merged["total_amount_erp"]
    ).sum()
    date_difference_count = (
        pd.to_datetime(merged["invoice_date_sii"])
        != pd.to_datetime(merged["entry_date"])
    ).sum()
    assert missing_count + amount_difference_count + date_difference_count == 3
