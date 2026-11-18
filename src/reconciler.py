"""DuckDB-backed three-way reconciliation for tax, ERP, and bank records."""

from __future__ import annotations

import re
from dataclasses import dataclass

import duckdb
import pandas as pd

_REMITTANCE_PATTERN = re.compile(r"([A-Z0-9-]+):(\d+(?:\.\d{1,2})?)")


@dataclass(frozen=True)
class ReconciliationResult:
    invoices: pd.DataFrame
    unmatched_bank: pd.DataFrame


def _empty_bank() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "transaction_id",
            "booking_date",
            "value_date",
            "description",
            "counterparty",
            "credit",
            "debit",
            "remittance_details",
        ]
    )


def _allocate_bank(
    bank: pd.DataFrame,
    sii: pd.DataFrame,
    *,
    amount_tolerance: float,
    date_window_days: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    bank = bank.copy() if bank is not None else _empty_bank()
    if bank.empty:
        return pd.DataFrame(
            columns=["invoice_id", "paid_amount", "payment_date", "match_method"]
        ), bank
    bank["value_date"] = pd.to_datetime(bank["value_date"], errors="coerce")
    bank["credit"] = pd.to_numeric(bank["credit"], errors="coerce").fillna(0.0)
    paid: list[dict[str, object]] = []
    referenced_transactions: set[object] = set()
    known_invoice_ids = set(sii["invoice_id"])
    for transaction in bank.itertuples(index=False):
        details = str(getattr(transaction, "remittance_details", "") or "")
        matches = list(_REMITTANCE_PATTERN.finditer(details))
        if not matches:
            continue
        transaction_allocated = False
        for match in matches:
            if match.group(1) not in known_invoice_ids:
                continue
            transaction_allocated = True
            paid.append(
                {
                    "invoice_id": match.group(1),
                    "paid_amount": round(float(match.group(2)), 2),
                    "payment_date": transaction.value_date,
                    "match_method": "reference",
                    "transaction_id": transaction.transaction_id,
                }
            )
        if transaction_allocated:
            referenced_transactions.add(transaction.transaction_id)

    available = bank[
        (bank["credit"] > 0)
        & (~bank["transaction_id"].isin(referenced_transactions))
        & bank["value_date"].notna()
    ]
    claimed_transactions: set[object] = set()
    if not available.empty:
        for invoice in sii.itertuples(index=False):
            invoice_date = pd.Timestamp(invoice.invoice_date)
            due_date = pd.Timestamp(invoice.due_date)
            candidates = available.copy()
            candidates["amount_delta"] = (
                candidates["credit"] - float(invoice.total_amount)
            ).abs()
            candidates["day_delta"] = (
                candidates["value_date"] - due_date
            ).dt.days.abs()
            candidates = candidates[
                (
                    candidates["amount_delta"]
                    <= max(amount_tolerance, abs(float(invoice.total_amount)) * 0.01)
                )
                & (candidates["value_date"] >= invoice_date)
                & (candidates["day_delta"] <= date_window_days)
                & (~candidates["transaction_id"].isin(claimed_transactions))
            ].sort_values(["amount_delta", "day_delta"])
            if len(candidates) == 1:
                candidate = candidates.iloc[0]
                claimed_transactions.add(candidate["transaction_id"])
                paid.append(
                    {
                        "invoice_id": invoice.invoice_id,
                        "paid_amount": float(candidate["credit"]),
                        "payment_date": candidate["value_date"],
                        "match_method": "fuzzy",
                        "transaction_id": candidate["transaction_id"],
                    }
                )

    allocated = pd.DataFrame(
        paid,
        columns=[
            "invoice_id",
            "paid_amount",
            "payment_date",
            "match_method",
            "transaction_id",
        ],
    )
    used_transactions = referenced_transactions | claimed_transactions
    unmatched = bank[
        (bank["credit"] > 0) & (~bank["transaction_id"].isin(used_transactions))
    ].copy()
    return allocated, unmatched


def reconcile(
    sii: pd.DataFrame,
    erp: pd.DataFrame,
    bank: pd.DataFrame | None = None,
    *,
    amount_tolerance: float = 0.01,
    date_window_days: int = 7,
) -> ReconciliationResult:
    """Join all sources, classifying exact, fuzzy, partial, unpaid, and exception cases."""
    required_sii = {"invoice_id", "invoice_date", "due_date", "total_amount"}
    required_erp = {"invoice_id", "entry_date", "total_amount"}
    if not required_sii.issubset(sii.columns):
        raise ValueError(
            f"SII data is missing columns: {sorted(required_sii - set(sii.columns))}"
        )
    if not required_erp.issubset(erp.columns):
        raise ValueError(
            f"ERP data is missing columns: {sorted(required_erp - set(erp.columns))}"
        )
    if amount_tolerance < 0 or date_window_days < 0:
        raise ValueError("Amount and date tolerances must be non-negative.")

    tax = sii.copy()
    ledger = erp.copy()
    tax["invoice_date"] = pd.to_datetime(tax["invoice_date"], errors="coerce")
    tax["due_date"] = pd.to_datetime(tax["due_date"], errors="coerce")
    tax["total_amount"] = pd.to_numeric(tax["total_amount"], errors="coerce")
    ledger["entry_date"] = pd.to_datetime(ledger["entry_date"], errors="coerce")
    ledger["total_amount"] = pd.to_numeric(ledger["total_amount"], errors="coerce")
    allocated, unmatched = _allocate_bank(
        bank if bank is not None else _empty_bank(),
        tax,
        amount_tolerance=amount_tolerance,
        date_window_days=date_window_days,
    )
    connection = duckdb.connect(database=":memory:")
    try:
        connection.register("tax_source", tax)
        connection.register("erp_source", ledger)
        connection.register("allocations", allocated)
        result = connection.execute(
            """
            WITH bank_by_invoice AS (
                SELECT
                    invoice_id,
                    SUM(paid_amount) AS bank_amount,
                    MIN(payment_date) AS first_payment_date,
                    STRING_AGG(DISTINCT match_method, ',') AS bank_match_method
                FROM allocations
                GROUP BY invoice_id
            )
            SELECT
                s.*,
                e.total_amount AS erp_amount,
                e.entry_date AS erp_entry_date,
                (e.invoice_id IS NOT NULL) AS erp_present,
                COALESCE(b.bank_amount, 0) AS bank_amount,
                b.first_payment_date,
                COALESCE(b.bank_match_method, 'none') AS bank_match_method
            FROM tax_source AS s
            LEFT JOIN erp_source AS e USING (invoice_id)
            LEFT JOIN bank_by_invoice AS b USING (invoice_id)
            ORDER BY s.invoice_date, s.invoice_id
            """
        ).df()
    finally:
        connection.close()

    result["erp_variance"] = (result["erp_amount"] - result["total_amount"]).round(2)
    result["bank_variance"] = (result["total_amount"] - result["bank_amount"]).round(2)
    date_delta = (result["erp_entry_date"] - result["invoice_date"]).dt.days.abs()
    conditions = [
        ~result["erp_present"],
        result["erp_variance"].abs() > amount_tolerance,
        date_delta > date_window_days,
        result["bank_amount"] >= result["total_amount"] - amount_tolerance,
        result["bank_amount"] > 0,
    ]
    result["reconciliation_status"] = [
        "erp_missing"
        if missing
        else "amount_mismatch"
        if amount_error
        else "date_mismatch"
        if date_error
        else "reconciled"
        if fully_paid
        else "partial_payment"
        if partial
        else "unpaid"
        for missing, amount_error, date_error, fully_paid, partial in zip(*conditions)
    ]
    result["automatically_matched"] = result["reconciliation_status"].eq("reconciled")
    return ReconciliationResult(invoices=result, unmatched_bank=unmatched)
