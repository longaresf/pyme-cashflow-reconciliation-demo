"""Generate three-way reconciliation inputs from public retail data or synthetic data."""

from __future__ import annotations

import logging
import os
from datetime import timedelta
from pathlib import Path

import numpy as np
import pandas as pd

LOGGER = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
SII_FILE = RAW_DIR / "tax_registry_sii.csv"
ERP_FILE = RAW_DIR / "erp_sales_ledger.csv"
BANK_FILE = RAW_DIR / "bank_statement.csv"


def _read_retail_dataset(csv_path: Path) -> pd.DataFrame:
    """Adapt common Online Retail-style rows into invoice-level sales."""
    source = pd.read_csv(csv_path, low_memory=False)
    column_map = {str(column).strip().lower(): column for column in source.columns}

    def find_column(*candidates: str) -> str | None:
        for candidate in candidates:
            if candidate in column_map:
                return column_map[candidate]
        return None

    invoice_col = find_column("invoiceno", "invoice", "invoice_id")
    date_col = find_column("invoicedate", "invoice_date", "date")
    quantity_col = find_column("quantity", "qty")
    price_col = find_column("unitprice", "unit_price", "price")
    customer_col = find_column("customerid", "customer_id", "customer")
    if not all((invoice_col, date_col, quantity_col, price_col)):
        raise ValueError(
            "The selected Kaggle CSV must include invoice, date, quantity, and unit price columns."
        )

    rows = source[
        [invoice_col, date_col, quantity_col, price_col]
        + ([customer_col] if customer_col else [])
    ].copy()
    rows.columns = ["invoice", "date", "quantity", "unit_price"] + (
        ["customer"] if customer_col else []
    )
    rows["date"] = pd.to_datetime(rows["date"], errors="coerce")
    rows["quantity"] = pd.to_numeric(rows["quantity"], errors="coerce")
    rows["unit_price"] = pd.to_numeric(rows["unit_price"], errors="coerce")
    rows = rows.dropna(subset=["invoice", "date", "quantity", "unit_price"])
    rows = rows[(rows["quantity"] > 0) & (rows["unit_price"] > 0)]
    rows["amount"] = rows["quantity"] * rows["unit_price"]
    grouped = rows.groupby("invoice", as_index=False).agg(
        invoice_date=("date", "min"),
        total_amount=("amount", "sum"),
        customer=("customer", "first") if customer_col else ("invoice", "first"),
    )
    grouped = grouped[grouped["total_amount"] > 0].reset_index(drop=True)
    amount_to_clp = float(os.getenv("KAGGLE_AMOUNT_TO_CLP", "1200"))
    if amount_to_clp <= 0:
        raise ValueError("KAGGLE_AMOUNT_TO_CLP must be greater than zero.")
    grouped["total_amount"] = grouped["total_amount"] * amount_to_clp
    return grouped


def _try_kaggle_source() -> pd.DataFrame | None:
    """Use Kaggle only when explicitly configured; otherwise keep startup offline."""
    dataset = os.getenv("KAGGLE_DATASET")
    if not dataset:
        return None
    if not (os.getenv("KAGGLE_USERNAME") and os.getenv("KAGGLE_KEY")):
        LOGGER.info(
            "Kaggle dataset configured without credentials; using deterministic sample data."
        )
        return None
    try:
        import kagglehub

        downloaded = Path(kagglehub.dataset_download(dataset))
        csv_files = sorted(downloaded.rglob("*.csv"))
        if not csv_files:
            raise FileNotFoundError(
                f"Kaggle dataset {dataset!r} contains no CSV files."
            )
        LOGGER.info("Adapting Kaggle dataset %s from %s", dataset, csv_files[0].name)
        return _read_retail_dataset(csv_files[0])
    except (ImportError, OSError, ValueError, RuntimeError) as error:
        LOGGER.warning(
            "Kaggle source unavailable (%s); generating deterministic sample data.",
            error,
        )
        return None


def _synthetic_orders(
    count: int, seed: int, reference_date: pd.Timestamp
) -> pd.DataFrame:
    """Create reproducible invoice inputs without external credentials or services."""
    rng = np.random.default_rng(seed)
    invoice_dates = reference_date - pd.to_timedelta(
        rng.integers(1, 241, size=count), unit="D"
    )
    customer_numbers = rng.integers(1, max(12, count // 5), size=count)
    amounts = np.round(rng.lognormal(mean=6.9, sigma=0.72, size=count), 2)
    return pd.DataFrame(
        {
            "invoice": [f"INV-{number:05d}" for number in range(1, count + 1)],
            "invoice_date": invoice_dates,
            "total_amount": amounts,
            "customer": [f"CUST-{number:04d}" for number in customer_numbers],
        }
    )


def build_sources(
    orders: pd.DataFrame | None = None,
    *,
    seed: int = 2025,
    invoice_count: int = 300,
    reference_date: pd.Timestamp | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Build SII, ERP, and bank dataframes, injecting a controlled 5% ERP error rate."""
    reference = pd.Timestamp(
        reference_date
        if reference_date is not None
        else pd.Timestamp.today().normalize()
    )
    if orders is None:
        orders = _try_kaggle_source()
    if orders is None:
        orders = _synthetic_orders(invoice_count, seed, reference)
    orders = orders.copy().reset_index(drop=True)
    required = {"invoice", "invoice_date", "total_amount", "customer"}
    if not required.issubset(orders.columns):
        raise ValueError(
            f"Order data must contain these columns: {', '.join(sorted(required))}."
        )
    orders["invoice_date"] = pd.to_datetime(orders["invoice_date"]).dt.normalize()
    orders["total_amount"] = pd.to_numeric(
        orders["total_amount"], errors="raise"
    ).round(2)
    orders = orders[
        (orders["total_amount"] > 0) & orders["invoice"].notna()
    ].reset_index(drop=True)
    if orders.empty:
        raise ValueError(
            "No positive-value invoices are available to generate the demo data."
        )

    rng = np.random.default_rng(seed + 1)
    orders["due_date"] = orders["invoice_date"] + timedelta(days=30)
    orders["tax_amount"] = (orders["total_amount"] * 0.19 / 1.19).round(2)
    orders["net_amount"] = (orders["total_amount"] - orders["tax_amount"]).round(2)
    sii = orders.rename(columns={"invoice": "invoice_id", "customer": "customer_id"})[
        [
            "invoice_id",
            "customer_id",
            "invoice_date",
            "due_date",
            "net_amount",
            "tax_amount",
            "total_amount",
        ]
    ].copy()
    sii["status"] = "issued"
    sii["currency"] = "CLP"

    erp = sii[
        [
            "invoice_id",
            "customer_id",
            "invoice_date",
            "due_date",
            "net_amount",
            "tax_amount",
            "total_amount",
        ]
    ].copy()
    erp["entry_date"] = erp["invoice_date"]
    anomaly_count = max(1, round(len(erp) * 0.05)) if len(erp) else 0
    anomaly_indices = rng.choice(
        erp.index.to_numpy(), size=anomaly_count, replace=False
    )
    anomaly_kinds = ["date_shift", "amount_difference", "omitted"]
    erp["anomaly_type"] = "none"
    for position, row_index in enumerate(anomaly_indices):
        kind = anomaly_kinds[position % len(anomaly_kinds)]
        erp.loc[row_index, "anomaly_type"] = kind
        if kind == "date_shift":
            erp.loc[row_index, "entry_date"] += timedelta(
                days=int(rng.choice([-14, -10, 10, 14]))
            )
        elif kind == "amount_difference":
            adjustment = float(rng.choice([-0.15, -0.07, 0.11, 0.25]))
            erp.loc[row_index, "total_amount"] = round(
                erp.loc[row_index, "total_amount"] + adjustment, 2
            )
            erp.loc[row_index, "net_amount"] = round(
                erp.loc[row_index, "net_amount"] + adjustment, 2
            )
    erp = (
        erp[erp["anomaly_type"] != "omitted"]
        .drop(columns="anomaly_type")
        .reset_index(drop=True)
    )

    bank_rows: list[dict[str, object]] = []
    payment_candidates: list[dict[str, object]] = []
    for row in sii.itertuples(index=False):
        if rng.random() > 0.82:
            continue
        payment_date = max(
            row.invoice_date,
            row.due_date + timedelta(days=int(rng.integers(-4, 25))),
        )
        if payment_date > reference:
            continue
        payment_amount = float(row.total_amount)
        is_partial = rng.random() < 0.10
        if is_partial:
            payment_amount = round(payment_amount * float(rng.uniform(0.35, 0.75)), 2)
        payment_candidates.append(
            {
                "invoice_id": row.invoice_id,
                "customer_id": row.customer_id,
                "payment_date": payment_date,
                "amount": payment_amount,
            }
        )

    # Consolidate same-customer, same-day settlements into realistic batch deposits.
    payment_frame = pd.DataFrame(payment_candidates)
    if not payment_frame.empty:
        payment_frame["batch_key"] = payment_frame["customer_id"].astype(
            str
        ) + payment_frame["payment_date"].astype(str)
        for batch_number, (_, batch) in enumerate(
            payment_frame.groupby("batch_key", sort=True), start=1
        ):
            references = "|".join(
                f"{item.invoice_id}:{item.amount:.2f}"
                for item in batch.itertuples(index=False)
            )
            description = "Customer batch deposit"
            if rng.random() < 0.08:
                references = ""
                description = "Unidentified incoming transfer"
            bank_rows.append(
                {
                    "transaction_id": f"BNK-{batch_number:05d}",
                    "booking_date": batch["payment_date"].min(),
                    "value_date": batch["payment_date"].min(),
                    "description": description,
                    "counterparty": batch["customer_id"].iloc[0],
                    "credit": round(float(batch["amount"].sum()), 2),
                    "debit": 0.0,
                    "remittance_details": references,
                }
            )

    # Add historical operating outflows for the cash forecast's run-rate estimate.
    expense_dates = pd.date_range(reference - timedelta(days=180), reference, freq="7D")
    for number, expense_date in enumerate(expense_dates, start=1):
        expense = round(float(rng.uniform(3_500, 7_500)), 2)
        bank_rows.append(
            {
                "transaction_id": f"EXP-{number:04d}",
                "booking_date": expense_date,
                "value_date": expense_date,
                "description": "Operating expense",
                "counterparty": "Operating costs",
                "credit": 0.0,
                "debit": expense,
                "remittance_details": "",
            }
        )
    bank = pd.DataFrame(
        bank_rows,
        columns=[
            "transaction_id",
            "booking_date",
            "value_date",
            "description",
            "counterparty",
            "credit",
            "debit",
            "remittance_details",
        ],
    )
    return sii, erp, bank


def generate_data(
    *,
    output_dir: Path = RAW_DIR,
    seed: int = 2025,
    invoice_count: int = 300,
    reference_date: pd.Timestamp | None = None,
) -> tuple[Path, Path, Path]:
    """Create the three source CSVs and return their paths."""
    sii, erp, bank = build_sources(
        seed=seed, invoice_count=invoice_count, reference_date=reference_date
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = (
        output_dir / "tax_registry_sii.csv",
        output_dir / "erp_sales_ledger.csv",
        output_dir / "bank_statement.csv",
    )
    for frame, path in zip((sii, erp, bank), paths):
        frame.to_csv(path, index=False, date_format="%Y-%m-%d")
        LOGGER.info("Wrote %s rows to %s", len(frame), path)
    return paths


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    generate_data()


if __name__ == "__main__":
    main()
