"""Static collection-performance charts for downloadable reporting."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from src.cashflow_model import calculate_dso


def create_collection_report(
    reconciliation: pd.DataFrame,
    output_path: Path,
) -> Path:
    """Render payment-delay distribution and monthly DSO as a PNG report."""
    data = reconciliation.copy()
    data["invoice_date"] = pd.to_datetime(data["invoice_date"], errors="coerce")
    data["first_payment_date"] = pd.to_datetime(
        data["first_payment_date"], errors="coerce"
    )
    data["total_amount"] = pd.to_numeric(data["total_amount"], errors="coerce").fillna(
        0
    )
    data["bank_amount"] = pd.to_numeric(data["bank_amount"], errors="coerce").fillna(0)
    data["payment_days"] = (data["first_payment_date"] - data["invoice_date"]).dt.days
    data["outstanding"] = (data["total_amount"] - data["bank_amount"]).clip(lower=0)
    paid = data.dropna(subset=["payment_days"])
    data["invoice_month"] = data["invoice_date"].dt.to_period("M").astype(str)
    monthly = data.groupby("invoice_month", as_index=False).agg(
        receivables=("outstanding", "sum"),
        sales=("total_amount", "sum"),
        invoice_count=("invoice_id", "count"),
    )
    monthly["dso"] = monthly.apply(
        lambda row: calculate_dso(row["receivables"], row["sales"], 30),
        axis=1,
    )

    sns.set_theme(style="whitegrid", palette="deep")
    figure, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    if paid.empty:
        axes[0].text(
            0.5,
            0.5,
            "No settled invoices in the selected dataset",
            ha="center",
            va="center",
        )
        axes[0].set_axis_off()
    else:
        sns.histplot(
            data=paid, x="payment_days", bins=18, kde=True, ax=axes[0], color="#167D9A"
        )
        axes[0].set_title("Days from invoice to first payment")
        axes[0].set_xlabel("Days")
        axes[0].set_ylabel("Invoice count")
    if monthly.empty:
        axes[1].text(0.5, 0.5, "No invoice history available", ha="center", va="center")
        axes[1].set_axis_off()
    else:
        sns.barplot(
            data=monthly, x="invoice_month", y="dso", ax=axes[1], color="#E99B3D"
        )
        axes[1].set_title("Monthly DSO proxy")
        axes[1].set_xlabel("Invoice month")
        axes[1].set_ylabel("Days")
        axes[1].tick_params(axis="x", rotation=45)
    figure.suptitle("Collection performance", fontsize=14, fontweight="bold")
    figure.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output_path, dpi=160, bbox_inches="tight")
    plt.close(figure)
    return output_path
