"""Static collection-performance charts for downloadable reporting."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from src.cashflow_model import calculate_dso

STATIC_CHART_TEXTS: dict[str, dict[str, str]] = {
    "es": {
        "hist_title": "Días desde facturación a primer pago",
        "hist_xlabel": "Días",
        "hist_ylabel": "Cantidad de facturas",
        "hist_empty": "No hay facturas pagadas en el conjunto de datos",
        "bar_title": "DSO mensual estimado",
        "bar_xlabel": "Mes de facturación",
        "bar_ylabel": "Días",
        "bar_empty": "No hay historial de facturas disponible",
        "suptitle": "Desempeño de cobranzas",
    },
    "en": {
        "hist_title": "Days from invoice to first payment",
        "hist_xlabel": "Days",
        "hist_ylabel": "Invoice count",
        "hist_empty": "No settled invoices in the selected dataset",
        "bar_title": "Monthly DSO proxy",
        "bar_xlabel": "Invoice month",
        "bar_ylabel": "Days",
        "bar_empty": "No invoice history available",
        "suptitle": "Collection performance",
    },
}


def create_collection_report(
    reconciliation: pd.DataFrame,
    output_path: Path,
    lang: str = "es",
) -> Path:
    """Render payment-delay distribution and monthly DSO as a high-contrast PNG report."""
    texts = STATIC_CHART_TEXTS.get(lang, STATIC_CHART_TEXTS["en"])
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
    figure.patch.set_facecolor("#FFFFFF")
    axes[0].set_facecolor("#FFFFFF")
    axes[1].set_facecolor("#FFFFFF")

    if paid.empty:
        axes[0].text(
            0.5,
            0.5,
            texts["hist_empty"],
            ha="center",
            va="center",
            color="#334155",
            fontsize=11,
        )
        axes[0].set_axis_off()
    else:
        sns.histplot(
            data=paid, x="payment_days", bins=18, kde=True, ax=axes[0], color="#0D9488"
        )
        axes[0].set_title(
            texts["hist_title"], color="#0F172A", fontweight="bold", fontsize=11
        )
        axes[0].set_xlabel(texts["hist_xlabel"], color="#334155", fontsize=10)
        axes[0].set_ylabel(texts["hist_ylabel"], color="#334155", fontsize=10)
        axes[0].tick_params(colors="#334155")

    if monthly.empty:
        axes[1].text(
            0.5,
            0.5,
            texts["bar_empty"],
            ha="center",
            va="center",
            color="#334155",
            fontsize=11,
        )
        axes[1].set_axis_off()
    else:
        sns.barplot(
            data=monthly, x="invoice_month", y="dso", ax=axes[1], color="#2563EB"
        )
        axes[1].set_title(
            texts["bar_title"], color="#0F172A", fontweight="bold", fontsize=11
        )
        axes[1].set_xlabel(texts["bar_xlabel"], color="#334155", fontsize=10)
        axes[1].set_ylabel(texts["bar_ylabel"], color="#334155", fontsize=10)
        axes[1].tick_params(axis="x", rotation=45, colors="#334155")
        axes[1].tick_params(axis="y", colors="#334155")

    figure.suptitle(texts["suptitle"], fontsize=13, fontweight="bold", color="#0F172A")
    figure.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output_path, dpi=160, bbox_inches="tight", facecolor="#FFFFFF")
    plt.close(figure)
    return output_path
