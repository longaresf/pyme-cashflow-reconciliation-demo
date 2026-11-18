"""Executive Streamlit dashboard for SMB cash-flow reconciliation."""

from __future__ import annotations

from io import BytesIO

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.cashflow_model import (
    calculate_aging,
    calculate_dso,
    cash_at_30_days,
    project_cashflow,
)
from src.data_loader import BANK_FILE, ERP_FILE, PROCESSED_DIR, SII_FILE, generate_data
from src.reconciler import ReconciliationResult, reconcile
from src.static_charts import create_collection_report

DB_FILE = PROCESSED_DIR / "reconciliation.duckdb"
CHART_FILE = PROCESSED_DIR / "collection_performance.png"


def _format_money(value: float) -> str:
    return f"${value:,.0f} CLP"


@st.cache_data(show_spinner=False)
def load_inputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if not all(path.exists() for path in (SII_FILE, ERP_FILE, BANK_FILE)):
        generate_data()
    return tuple(pd.read_csv(path) for path in (SII_FILE, ERP_FILE, BANK_FILE))


def _exception_workbook(result: ReconciliationResult) -> bytes:
    exception_rows = result.invoices[
        result.invoices["reconciliation_status"].isin(
            ["erp_missing", "amount_mismatch", "date_mismatch"]
        )
    ]
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        exception_rows.to_excel(writer, sheet_name="Invoice exceptions", index=False)
        result.unmatched_bank.to_excel(
            writer, sheet_name="Unmatched bank credits", index=False
        )
    return output.getvalue()


def _render_reconciliation(result: ReconciliationResult) -> None:
    invoices = result.invoices
    statuses = (
        invoices["reconciliation_status"]
        .value_counts()
        .rename_axis("status")
        .reset_index(name="invoice_count")
    )
    left, right = st.columns([1.05, 1])
    with left:
        st.subheader("Reconciliation funnel")
        funnel = px.funnel(
            statuses.sort_values("invoice_count", ascending=False),
            x="invoice_count",
            y="status",
            color="status",
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        funnel.update_layout(
            showlegend=False, margin={"l": 12, "r": 12, "t": 10, "b": 10}
        )
        st.plotly_chart(funnel, use_container_width=True)
    with right:
        st.subheader("Bank allocation")
        st.metric("Unmatched incoming transfers", str(len(result.unmatched_bank)))
        if not result.unmatched_bank.empty:
            st.dataframe(
                result.unmatched_bank[
                    [
                        "transaction_id",
                        "value_date",
                        "description",
                        "credit",
                        "counterparty",
                    ]
                ],
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.success("All incoming transfers were allocated.")

    st.subheader("Invoice-level exceptions and collections")
    choices = ["All invoices"] + sorted(
        invoices["reconciliation_status"].unique().tolist()
    )
    selected = st.selectbox("Filter by reconciliation status", choices)
    filtered = (
        invoices
        if selected == "All invoices"
        else invoices[invoices["reconciliation_status"] == selected]
    )
    display_columns = [
        "invoice_id",
        "customer_id",
        "invoice_date",
        "due_date",
        "total_amount",
        "erp_amount",
        "bank_amount",
        "erp_variance",
        "bank_variance",
        "reconciliation_status",
        "bank_match_method",
    ]
    st.dataframe(filtered[display_columns], use_container_width=True, hide_index=True)


def _render_cashflow(
    result: ReconciliationResult,
    bank: pd.DataFrame,
    delinquency: float,
) -> None:
    forecast = project_cashflow(
        result.invoices, bank, expected_delinquency_pct=delinquency
    )
    st.subheader("13-week liquidity outlook")
    st.caption(
        "Expected collections are reduced by the selected delinquency assumption; "
        "operating outflows use the recent bank debit run rate."
    )
    measures = ["absolute"] + ["relative"] * len(forecast) + ["total"]
    labels = (
        ["Opening cash"]
        + [week.strftime("%b %d") for week in forecast["week_start"]]
        + ["Closing cash"]
    )
    values = [float(forecast.iloc[0]["ending_cash"] - forecast.iloc[0]["net_cashflow"])]
    values.extend(forecast["net_cashflow"].astype(float).tolist())
    values.append(0.0)
    waterfall = go.Figure(
        go.Waterfall(
            name="Cash balance",
            orientation="v",
            measure=measures,
            x=labels,
            y=values,
            text=[_format_money(value) for value in values],
            textposition="outside",
            increasing={"marker": {"color": "#2C9C69"}},
            decreasing={"marker": {"color": "#D45D5D"}},
            totals={"marker": {"color": "#236B8E"}},
            connector={"line": {"color": "#9AA6B2"}},
        )
    )
    waterfall.update_layout(
        yaxis_title="Cash balance (CLP)",
        showlegend=False,
        margin={"l": 10, "r": 10, "t": 25, "b": 10},
        xaxis={"tickangle": -35},
    )
    st.plotly_chart(waterfall, use_container_width=True)
    st.dataframe(forecast, use_container_width=True, hide_index=True)


def _render_dso(result: ReconciliationResult) -> None:
    invoices = result.invoices.copy()
    invoices["invoice_date"] = pd.to_datetime(invoices["invoice_date"])
    invoices["due_date"] = pd.to_datetime(invoices["due_date"])
    invoices["outstanding"] = (
        invoices["total_amount"].fillna(0) - invoices["bank_amount"].fillna(0)
    ).clip(lower=0)
    current_date = pd.Timestamp.today().normalize()
    recent_sales = invoices.loc[
        invoices["invoice_date"] >= current_date - pd.Timedelta(days=90), "total_amount"
    ].sum()
    dso = calculate_dso(invoices["outstanding"].sum(), recent_sales, 90)
    aging = calculate_aging(invoices)
    left, right = st.columns([1, 1.15])
    with left:
        st.metric("DSO (90-day basis)", f"{dso:.1f} days")
        chart = px.bar(
            aging,
            x="aging_bucket",
            y="amount",
            color="aging_bucket",
            labels={
                "aging_bucket": "Age of receivable",
                "amount": "Open balance (CLP)",
            },
            color_discrete_sequence=px.colors.sequential.Teal,
        )
        chart.update_layout(
            showlegend=False, margin={"l": 10, "r": 10, "t": 10, "b": 10}
        )
        st.plotly_chart(chart, use_container_width=True)
    with right:
        create_collection_report(invoices, CHART_FILE)
        st.image(str(CHART_FILE), caption="Static payment-delay and monthly DSO report")
        st.download_button(
            "Download statistical chart (PNG)",
            data=CHART_FILE.read_bytes(),
            file_name="collection_performance.png",
            mime="image/png",
        )

    st.download_button(
        "Download exception report (Excel)",
        data=_exception_workbook(result),
        file_name="reconciliation_exceptions.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary",
    )


def main() -> None:
    st.set_page_config(
        page_title="SMB Cashflow Control",
        page_icon="💼",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(
        """
        <style>
        .block-container {padding-top: 1.5rem; padding-bottom: 2rem;}
        [data-testid="stMetric"] {background: #f5f8fa; border: 1px solid #e6edf2;
          padding: 14px 16px; border-radius: 10px;}
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.title("SMB Cashflow Control")
    st.caption("Three-way invoice reconciliation and a rolling 13-week liquidity view")

    sii, erp, bank = load_inputs()
    result = reconcile(sii, erp, bank)
    invoices = result.invoices
    delinquency = st.sidebar.slider(
        "Expected collection delinquency",
        min_value=0,
        max_value=60,
        value=10,
        step=5,
        help=(
            "Share of outstanding receivables expected to fall outside "
            "the forecast collection window."
        ),
    )
    st.sidebar.caption(
        "Sources: "
        f"{len(sii):,} tax invoices · "
        f"{len(erp):,} ERP entries · "
        f"{len(bank):,} bank transactions"
    )

    total_billed = float(invoices["total_amount"].sum())
    auto_pct = (
        float(invoices["automatically_matched"].mean() * 100)
        if not invoices.empty
        else 0
    )
    exception_mask = invoices["reconciliation_status"].isin(
        ["erp_missing", "amount_mismatch", "date_mismatch"]
    )
    missing_erp = invoices["reconciliation_status"].eq("erp_missing")
    discrepancy = float(
        invoices.loc[exception_mask & ~missing_erp, "erp_variance"]
        .abs()
        .fillna(0)
        .sum()
        + invoices.loc[missing_erp, "total_amount"].sum()
        + result.unmatched_bank["credit"].sum()
    )
    forecast = project_cashflow(
        invoices,
        bank,
        expected_delinquency_pct=delinquency,
    )
    cards = st.columns(4)
    cards[0].metric("Total invoiced", _format_money(total_billed))
    cards[1].metric("Auto-reconciled", f"{auto_pct:.1f}%")
    cards[2].metric("Discrepancy exposure", _format_money(discrepancy))
    cards[3].metric(
        "Projected cash · 30 days", _format_money(cash_at_30_days(forecast))
    )

    reconciliation_tab, cashflow_tab, dso_tab = st.tabs(
        [
            "Reconciliation monitor",
            "13-week cash forecast",
            "Collection & DSO analytics",
        ]
    )
    with reconciliation_tab:
        _render_reconciliation(result)
    with cashflow_tab:
        _render_cashflow(result, bank, delinquency)
    with dso_tab:
        _render_dso(result)

    # Keep a lightweight processed database artifact available for inspection.
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    import duckdb

    with duckdb.connect(str(DB_FILE)) as connection:
        connection.register("reconciled_invoices", invoices)
        connection.execute(
            "CREATE OR REPLACE TABLE reconciliation AS SELECT * FROM reconciled_invoices"
        )


if __name__ == "__main__":
    main()
