"""Executive Streamlit dashboard for SMB cash-flow reconciliation."""

from __future__ import annotations

from io import BytesIO

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

try:
    from app.i18n import (
        DEFAULT_LANGUAGE,
        HIGH_CONTRAST_CSS,
        LANG_EN,
        LANG_ES,
        LANGUAGE_CHOICES,
        apply_plotly_theme,
        format_week_label,
        get_aging_bucket_label,
        get_column_label,
        get_match_method_label,
        get_status_label,
        t,
    )
except ImportError:
    from i18n import (  # type: ignore[no-redef]
        DEFAULT_LANGUAGE,
        HIGH_CONTRAST_CSS,
        LANG_EN,
        LANG_ES,
        LANGUAGE_CHOICES,
        apply_plotly_theme,
        format_week_label,
        get_aging_bucket_label,
        get_column_label,
        get_match_method_label,
        get_status_label,
        t,
    )

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


def _exception_workbook(
    result: ReconciliationResult, lang: str = DEFAULT_LANGUAGE
) -> bytes:
    exception_rows = result.invoices[
        result.invoices["reconciliation_status"].isin(
            ["erp_missing", "amount_mismatch", "date_mismatch"]
        )
    ]
    sheet_exceptions = t("excel_sheet_exceptions", lang)
    sheet_unmatched = t("excel_sheet_unmatched", lang)
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        exception_rows.to_excel(writer, sheet_name=sheet_exceptions, index=False)
        result.unmatched_bank.to_excel(writer, sheet_name=sheet_unmatched, index=False)
    return output.getvalue()


def _render_reconciliation(
    result: ReconciliationResult, lang: str = DEFAULT_LANGUAGE
) -> None:
    invoices = result.invoices
    statuses = (
        invoices["reconciliation_status"]
        .value_counts()
        .rename_axis("status")
        .reset_index(name="invoice_count")
    )
    statuses["status_display"] = statuses["status"].map(
        lambda s: get_status_label(s, lang)
    )

    left, right = st.columns([1.05, 1])
    with left:
        st.subheader(t("funnel_title", lang))
        funnel = px.funnel(
            statuses.sort_values("invoice_count", ascending=False),
            x="invoice_count",
            y="status_display",
            color="status_display",
            labels={
                "invoice_count": get_column_label("invoice_count", lang),
                "status_display": get_column_label("status", lang),
            },
            color_discrete_sequence=px.colors.qualitative.Bold,
        )
        funnel.update_layout(
            showlegend=False,
            margin={"l": 12, "r": 12, "t": 10, "b": 10},
        )
        apply_plotly_theme(funnel)
        st.plotly_chart(funnel, use_container_width=True)

    with right:
        st.subheader(t("bank_allocation_title", lang))
        st.metric(
            t("metric_unmatched_bank", lang),
            str(len(result.unmatched_bank)),
        )
        if not result.unmatched_bank.empty:
            bank_cols = [
                "transaction_id",
                "value_date",
                "description",
                "credit",
                "counterparty",
            ]
            bank_display = result.unmatched_bank[bank_cols].rename(
                columns={col: get_column_label(col, lang) for col in bank_cols}
            )
            st.dataframe(
                bank_display,
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.success(t("bank_all_allocated", lang))

    st.subheader(t("exceptions_title", lang))
    unique_statuses = sorted(invoices["reconciliation_status"].unique().tolist())
    status_choices = ["all"] + unique_statuses

    def _format_status(choice: str) -> str:
        if choice == "all":
            return t("all_invoices_option", lang)
        return get_status_label(choice, lang)

    selected = st.selectbox(
        t("filter_status_label", lang),
        options=status_choices,
        format_func=_format_status,
    )
    filtered = (
        invoices
        if selected == "all"
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
    display_df = filtered[display_columns].copy()
    display_df["reconciliation_status"] = display_df["reconciliation_status"].map(
        lambda s: get_status_label(s, lang)
    )
    display_df["bank_match_method"] = display_df["bank_match_method"].map(
        lambda m: get_match_method_label(m, lang)
    )
    st.dataframe(
        display_df.rename(
            columns={col: get_column_label(col, lang) for col in display_columns}
        ),
        use_container_width=True,
        hide_index=True,
    )


def _render_cashflow(
    result: ReconciliationResult,
    bank: pd.DataFrame,
    delinquency: float,
    lang: str = DEFAULT_LANGUAGE,
) -> None:
    forecast = project_cashflow(
        result.invoices, bank, expected_delinquency_pct=delinquency
    )
    st.subheader(t("cashflow_title", lang))
    st.caption(t("cashflow_caption", lang))

    measures = ["absolute"] + ["relative"] * len(forecast) + ["total"]
    labels = (
        [t("opening_cash", lang)]
        + [format_week_label(week, lang=lang) for week in forecast["week_start"]]
        + [t("closing_cash", lang)]
    )
    values = [float(forecast.iloc[0]["ending_cash"] - forecast.iloc[0]["net_cashflow"])]
    values.extend(forecast["net_cashflow"].astype(float).tolist())
    values.append(0.0)

    waterfall = go.Figure(
        go.Waterfall(
            name=t("waterfall_name", lang),
            orientation="v",
            measure=measures,
            x=labels,
            y=values,
            text=[_format_money(value) for value in values],
            textposition="outside",
            textfont={"color": "#F8FAFC", "size": 11},
            increasing={"marker": {"color": "#16A34A"}},
            decreasing={"marker": {"color": "#DC2626"}},
            totals={"marker": {"color": "#2563EB"}},
            connector={"line": {"color": "#94A3B8"}},
        )
    )
    waterfall.update_layout(
        yaxis_title=t("waterfall_yaxis", lang),
        showlegend=False,
        margin={"l": 10, "r": 10, "t": 25, "b": 10},
        xaxis={"tickangle": -35},
    )
    apply_plotly_theme(waterfall)
    st.plotly_chart(waterfall, use_container_width=True)

    forecast_cols = [
        "week_start",
        "projected_inflows",
        "projected_outflows",
        "net_cashflow",
        "ending_cash",
    ]
    forecast_display = forecast[forecast_cols].rename(
        columns={col: get_column_label(col, lang) for col in forecast_cols}
    )
    st.dataframe(forecast_display, use_container_width=True, hide_index=True)


def _render_dso(result: ReconciliationResult, lang: str = DEFAULT_LANGUAGE) -> None:
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
        st.metric(
            t("metric_dso_90d", lang),
            t("dso_days_unit", lang, days=dso),
        )
        aging_display = aging.copy()
        aging_display["aging_bucket_display"] = (
            aging_display["aging_bucket"]
            .astype(str)
            .map(lambda b: get_aging_bucket_label(b, lang))
        )
        chart = px.bar(
            aging_display,
            x="aging_bucket_display",
            y="amount",
            color="aging_bucket_display",
            labels={
                "aging_bucket_display": t("aging_chart_x", lang),
                "amount": t("aging_chart_y", lang),
            },
            color_discrete_sequence=px.colors.sequential.Teal,
        )
        chart.update_layout(
            showlegend=False,
            margin={"l": 10, "r": 10, "t": 10, "b": 10},
        )
        apply_plotly_theme(chart)
        st.plotly_chart(chart, use_container_width=True)

    with right:
        create_collection_report(invoices, CHART_FILE, lang=lang)
        st.image(str(CHART_FILE), caption=t("static_chart_caption", lang))
        st.download_button(
            t("download_chart_png", lang),
            data=CHART_FILE.read_bytes(),
            file_name=t("filename_chart_png", lang),
            mime="image/png",
        )

    st.download_button(
        t("download_exceptions_excel", lang),
        data=_exception_workbook(result, lang=lang),
        file_name=t("filename_exceptions_excel", lang),
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary",
    )


def main() -> None:
    current_lang = st.session_state.get("app_language", DEFAULT_LANGUAGE)
    st.set_page_config(
        page_title=t("app_page_title", current_lang),
        page_icon="💼",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    # Inject high contrast CSS at the start of app rendering
    st.markdown(HIGH_CONTRAST_CSS, unsafe_allow_html=True)

    # Dynamic language selector in sidebar (default: Español)
    selected_language_name = st.sidebar.selectbox(
        t("sidebar_lang_label", current_lang),
        options=LANGUAGE_CHOICES,
        index=0 if current_lang == LANG_ES else 1,
    )
    lang = LANG_ES if selected_language_name == "Español" else LANG_EN
    st.session_state["app_language"] = lang

    # Native, high-contrast title and subtitle styled via HIGH_CONTRAST_CSS
    st.title(t("app_title", lang))
    st.caption(t("app_subtitle", lang))

    sii, erp, bank = load_inputs()

    result = reconcile(sii, erp, bank)
    invoices = result.invoices

    delinquency = st.sidebar.slider(
        t("sidebar_delinquency_label", lang),
        min_value=0,
        max_value=60,
        value=10,
        step=5,
        help=t("sidebar_delinquency_help", lang),
    )
    st.sidebar.caption(
        t("sidebar_sources", lang, sii=len(sii), erp=len(erp), bank=len(bank))
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

    # Top KPI cards with high visual contrast
    cards = st.columns(4)
    cards[0].metric(t("metric_total_invoiced", lang), _format_money(total_billed))
    cards[1].metric(t("metric_auto_reconciled", lang), f"{auto_pct:.1f}%")
    cards[2].metric(t("metric_discrepancy_exposure", lang), _format_money(discrepancy))
    cards[3].metric(
        t("metric_projected_cash_30d", lang), _format_money(cash_at_30_days(forecast))
    )

    # Localized tabs
    reconciliation_tab, cashflow_tab, dso_tab = st.tabs(
        [
            t("tab_reconciliation", lang),
            t("tab_cashflow", lang),
            t("tab_dso", lang),
        ]
    )
    with reconciliation_tab:
        _render_reconciliation(result, lang=lang)
    with cashflow_tab:
        _render_cashflow(result, bank, delinquency, lang=lang)
    with dso_tab:
        _render_dso(result, lang=lang)

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
