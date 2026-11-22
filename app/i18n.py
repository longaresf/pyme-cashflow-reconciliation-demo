"""Internationalization (i18n) and visual styling definitions."""

from __future__ import annotations

from typing import Any

import plotly.graph_objects as go

LANG_ES = "es"
LANG_EN = "en"
DEFAULT_LANGUAGE = LANG_ES

LANGUAGE_CHOICES = ["Español", "English"]

TRANSLATIONS: dict[str, dict[str, str]] = {
    LANG_ES: {
        # App metadata & headers
        "app_page_title": "Control de Flujo de Caja PYME",
        "app_title": "Control de Flujo de Caja PYME",
        "app_subtitle": "Conciliación de facturas a 3 vías y proyección móvil de liquidez a 13 semanas",
        # Sidebar
        "sidebar_lang_label": "Idioma / Language",
        "sidebar_delinquency_label": "Morosidad esperada de cobranza",
        "sidebar_delinquency_help": (
            "Porcentaje de cuentas por cobrar vencidas que se proyecta caerán fuera "
            "de la ventana de cobranza."
        ),
        "sidebar_sources": (
            "Fuentes: {sii:,} facturas SII · {erp:,} registros ERP · {bank:,} transacciones bancarias"
        ),
        # Top KPI metrics
        "metric_total_invoiced": "Total facturado",
        "metric_auto_reconciled": "Auto-conciliado",
        "metric_discrepancy_exposure": "Exposición a discrepancias",
        "metric_projected_cash_30d": "Caja proyectada · 30 días",
        # Tabs
        "tab_reconciliation": "Monitor de conciliación",
        "tab_cashflow": "Proyección de caja a 13 semanas",
        "tab_dso": "Analítica de cobranza y DSO",
        # Tab 1: Reconciliation Monitor
        "funnel_title": "Embudo de conciliación",
        "bank_allocation_title": "Asignación bancaria",
        "metric_unmatched_bank": "Transferencias entrantes no conciliadas",
        "bank_all_allocated": "Todas las transferencias entrantes fueron asignadas.",
        "exceptions_title": "Excepciones y cobranzas a nivel de factura",
        "filter_status_label": "Filtrar por estado de conciliación",
        "all_invoices_option": "Todas las facturas",
        # Tab 2: Cashflow
        "cashflow_title": "Panorama de liquidez a 13 semanas",
        "cashflow_caption": (
            "Las cobranzas esperadas se reducen según la tasa supuesta de morosidad; "
            "los egresos operacionales utilizan la tasa reciente de cargos bancarios."
        ),
        "waterfall_name": "Saldo de caja",
        "opening_cash": "Saldo inicial",
        "closing_cash": "Saldo final",
        "waterfall_yaxis": "Saldo de caja (CLP)",
        # Tab 3: DSO & Aging
        "metric_dso_90d": "DSO (base 90 días)",
        "dso_days_unit": "{days:.1f} días",
        "aging_chart_x": "Antigüedad de la deuda",
        "aging_chart_y": "Saldo pendiente (CLP)",
        "static_chart_caption": "Reporte estático de retraso de pagos y DSO mensual",
        "download_chart_png": "Descargar gráfico estadístico (PNG)",
        "download_exceptions_excel": "Descargar reporte de excepciones (Excel)",
        # Excel Workbook sheets
        "excel_sheet_exceptions": "Excepciones facturas",
        "excel_sheet_unmatched": "Abonos bancarios no asignados",
        # General column / chart terms
        "invoice_count": "Cantidad Facturas",
        "status": "Estado",
        # Download filenames
        "filename_chart_png": "desempeno_cobranzas_es.png",
        "filename_exceptions_excel": "excepciones_conciliacion_es.xlsx",
    },
    LANG_EN: {
        # App metadata & headers
        "app_page_title": "SMB Cashflow Control",
        "app_title": "SMB Cashflow Control",
        "app_subtitle": "Three-way invoice reconciliation and a rolling 13-week liquidity view",
        # Sidebar
        "sidebar_lang_label": "Language / Idioma",
        "sidebar_delinquency_label": "Expected collection delinquency",
        "sidebar_delinquency_help": (
            "Share of outstanding receivables expected to fall outside "
            "the forecast collection window."
        ),
        "sidebar_sources": (
            "Sources: {sii:,} tax invoices · {erp:,} ERP entries · {bank:,} bank transactions"
        ),
        # Top KPI metrics
        "metric_total_invoiced": "Total invoiced",
        "metric_auto_reconciled": "Auto-reconciled",
        "metric_discrepancy_exposure": "Discrepancy exposure",
        "metric_projected_cash_30d": "Projected cash · 30 days",
        # Tabs
        "tab_reconciliation": "Reconciliation monitor",
        "tab_cashflow": "13-week cash forecast",
        "tab_dso": "Collection & DSO analytics",
        # Tab 1: Reconciliation Monitor
        "funnel_title": "Reconciliation funnel",
        "bank_allocation_title": "Bank allocation",
        "metric_unmatched_bank": "Unmatched incoming transfers",
        "bank_all_allocated": "All incoming transfers were allocated.",
        "exceptions_title": "Invoice-level exceptions and collections",
        "filter_status_label": "Filter by reconciliation status",
        "all_invoices_option": "All invoices",
        # Tab 2: Cashflow
        "cashflow_title": "13-week liquidity outlook",
        "cashflow_caption": (
            "Expected collections are reduced by the selected delinquency assumption; "
            "operating outflows use the recent bank debit run rate."
        ),
        "waterfall_name": "Cash balance",
        "opening_cash": "Opening cash",
        "closing_cash": "Closing cash",
        "waterfall_yaxis": "Cash balance (CLP)",
        # Tab 3: DSO & Aging
        "metric_dso_90d": "DSO (90-day basis)",
        "dso_days_unit": "{days:.1f} days",
        "aging_chart_x": "Age of receivable",
        "aging_chart_y": "Open balance (CLP)",
        "static_chart_caption": "Static payment-delay and monthly DSO report",
        "download_chart_png": "Download statistical chart (PNG)",
        "download_exceptions_excel": "Download exception report (Excel)",
        # Excel Workbook sheets
        "excel_sheet_exceptions": "Invoice exceptions",
        "excel_sheet_unmatched": "Unmatched bank credits",
        # General column / chart terms
        "invoice_count": "Invoice Count",
        "status": "Status",
        # Download filenames
        "filename_chart_png": "collection_performance_en.png",
        "filename_exceptions_excel": "reconciliation_exceptions_en.xlsx",
    },
}

STATUS_LABELS: dict[str, dict[str, str]] = {
    LANG_ES: {
        "reconciled": "Conciliado",
        "unpaid": "No pagado",
        "partial_payment": "Pago parcial",
        "amount_mismatch": "Diferencia de monto",
        "date_mismatch": "Diferencia de fecha",
        "erp_missing": "Falta en ERP",
    },
    LANG_EN: {
        "reconciled": "Reconciled",
        "unpaid": "Unpaid",
        "partial_payment": "Partial payment",
        "amount_mismatch": "Amount mismatch",
        "date_mismatch": "Date mismatch",
        "erp_missing": "Missing in ERP",
    },
}

MATCH_METHOD_LABELS: dict[str, dict[str, str]] = {
    LANG_ES: {
        "reference": "Referencia exacta",
        "fuzzy": "Aproximado (monto y fecha)",
        "none": "Ninguno",
    },
    LANG_EN: {
        "reference": "Reference match",
        "fuzzy": "Fuzzy match",
        "none": "None",
    },
}

AGING_BUCKET_LABELS: dict[str, dict[str, str]] = {
    LANG_ES: {
        "Current": "Al día",
        "1-30 days": "1-30 días",
        "31-60 days": "31-60 días",
        "61-90 days": "61-90 días",
        "90+ days": "90+ días",
    },
    LANG_EN: {
        "Current": "Current",
        "1-30 days": "1-30 days",
        "31-60 days": "31-60 days",
        "61-90 days": "61-90 days",
        "90+ days": "90+ days",
    },
}

COLUMN_LABELS: dict[str, dict[str, str]] = {
    LANG_ES: {
        "invoice_id": "ID Factura",
        "customer_id": "ID Cliente",
        "invoice_date": "Fecha Factura",
        "due_date": "Fecha Vencimiento",
        "total_amount": "Monto Total",
        "erp_amount": "Monto ERP",
        "bank_amount": "Monto Banco",
        "erp_variance": "Varianza ERP",
        "bank_variance": "Varianza Banco",
        "reconciliation_status": "Estado Conciliación",
        "bank_match_method": "Método Coincidencia",
        "transaction_id": "ID Transacción",
        "value_date": "Fecha Valor",
        "description": "Descripción",
        "credit": "Abono (CLP)",
        "counterparty": "Contraparte",
        "week_start": "Inicio de Semana",
        "projected_inflows": "Ingresos Proyectados",
        "projected_outflows": "Egresos Proyectados",
        "net_cashflow": "Flujo Neto",
        "ending_cash": "Saldo Final",
        "invoice_count": "Cantidad Facturas",
        "status": "Estado",
    },
    LANG_EN: {
        "invoice_id": "Invoice ID",
        "customer_id": "Customer ID",
        "invoice_date": "Invoice Date",
        "due_date": "Due Date",
        "total_amount": "Total Amount",
        "erp_amount": "ERP Amount",
        "bank_amount": "Bank Amount",
        "erp_variance": "ERP Variance",
        "bank_variance": "Bank Variance",
        "reconciliation_status": "Reconciliation Status",
        "bank_match_method": "Match Method",
        "transaction_id": "Transaction ID",
        "value_date": "Value Date",
        "description": "Description",
        "credit": "Credit (CLP)",
        "counterparty": "Counterparty",
        "week_start": "Week Start",
        "projected_inflows": "Projected Inflows",
        "projected_outflows": "Projected Outflows",
        "net_cashflow": "Net Cashflow",
        "ending_cash": "Ending Cash",
        "invoice_count": "Invoice Count",
        "status": "Status",
    },
}


def t(key: str, lang: str = DEFAULT_LANGUAGE, **kwargs: Any) -> str:
    """Retrieve localized text for a key, falling back to English or key itself."""
    lang_dict = TRANSLATIONS.get(lang, TRANSLATIONS[DEFAULT_LANGUAGE])
    template = lang_dict.get(key, TRANSLATIONS.get(LANG_EN, {}).get(key, key))
    if kwargs:
        return template.format(**kwargs)
    return template


def get_status_label(status: str, lang: str = DEFAULT_LANGUAGE) -> str:
    """Get user-facing label for reconciliation status code."""
    status_str = str(status)
    return STATUS_LABELS.get(lang, {}).get(
        status_str, STATUS_LABELS[LANG_EN].get(status_str, status_str)
    )


def get_match_method_label(method: str, lang: str = DEFAULT_LANGUAGE) -> str:
    """Get user-facing label for bank match method(s)."""
    if not method or method == "none":
        return MATCH_METHOD_LABELS.get(lang, {}).get("none", "None")
    parts = [part.strip() for part in str(method).split(",") if part.strip()]
    labels = MATCH_METHOD_LABELS.get(lang, MATCH_METHOD_LABELS[LANG_EN])
    return ", ".join(labels.get(part, part) for part in parts)


def get_aging_bucket_label(bucket: str, lang: str = DEFAULT_LANGUAGE) -> str:
    """Get user-facing label for aging bucket."""
    bucket_str = str(bucket)
    return AGING_BUCKET_LABELS.get(lang, {}).get(
        bucket_str, AGING_BUCKET_LABELS[LANG_EN].get(bucket_str, bucket_str)
    )


def get_column_label(col: str, lang: str = DEFAULT_LANGUAGE) -> str:
    """Get user-facing column header for table display."""
    return COLUMN_LABELS.get(lang, {}).get(col, col)


def format_week_label(dt: Any, lang: str = DEFAULT_LANGUAGE) -> str:
    """Format week date nicely for waterfall chart."""
    month_names_es = {
        1: "Ene",
        2: "Feb",
        3: "Mar",
        4: "Abr",
        5: "May",
        6: "Jun",
        7: "Jul",
        8: "Ago",
        9: "Sep",
        10: "Oct",
        11: "Nov",
        12: "Dic",
    }
    month_names_en = {
        1: "Jan",
        2: "Feb",
        3: "Mar",
        4: "Apr",
        5: "May",
        6: "Jun",
        7: "Jul",
        8: "Aug",
        9: "Sep",
        10: "Oct",
        11: "Nov",
        12: "Dec",
    }
    m = dt.month
    d = dt.day
    if lang == LANG_ES:
        return f"{d:02d} {month_names_es.get(m, '')}"
    return f"{month_names_en.get(m, '')} {d:02d}"


# High-contrast CSS styles for Streamlit components
HIGH_CONTRAST_CSS = """
<style>
/* Root application containers: enforce high-contrast dark palette */
.stApp,
[data-testid="stAppViewContainer"],
.main {
    background-color: #0E1117 !important;
    color: #F1F5F9 !important;
}

/* Page container padding: Ensure top content is completely clear of the Streamlit navbar */
.block-container {
    padding-top: 3.75rem !important;
    padding-bottom: 2rem !important;
}

/* Ensure the fixed top header is transparent and does not obscure content */
header[data-testid="stHeader"] {
    background: transparent !important;
    z-index: 10 !important;
}

/* App Header Container: absolute clarity, solid high contrast */
.app-header-container {
    margin-bottom: 1.5rem !important;
    padding: 0 !important;
    display: block !important;
    visibility: visible !important;
    opacity: 1 !important;
}

.app-header-container .app-title-text,
.app-title-text,
h1.app-title-text,
[data-testid="stMarkdownContainer"] .app-title-text,
[data-testid="stMarkdownContainer"] h1.app-title-text {
    color: #F8FAFC !important;
    -webkit-text-fill-color: #F8FAFC !important;
    font-size: 2.25rem !important;
    font-weight: 800 !important;
    line-height: 1.25 !important;
    letter-spacing: -0.02em !important;
    margin: 0 0 0.4rem 0 !important;
    padding: 0 !important;
    display: block !important;
    visibility: visible !important;
    opacity: 1 !important;
}

.app-header-container .app-subtitle-text,
.app-subtitle-text,
p.app-subtitle-text,
[data-testid="stMarkdownContainer"] .app-subtitle-text,
[data-testid="stMarkdownContainer"] p.app-subtitle-text {
    color: #CBD5E1 !important;
    -webkit-text-fill-color: #CBD5E1 !important;
    font-size: 1.05rem !important;
    font-weight: 500 !important;
    line-height: 1.4 !important;
    margin: 0 !important;
    padding: 0 !important;
    display: block !important;
    visibility: visible !important;
    opacity: 1 !important;
}

/* Ensure all headings across app are 100% visible with high contrast */
h1, h2, h3, h4, h5, h6,
[data-testid="stHeadingWithActionElements"] h1,
[data-testid="stHeadingWithActionElements"] h2,
[data-testid="stHeadingWithActionElements"] h3,
[data-testid="stMarkdownContainer"] h1,
[data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3 {
    color: #F8FAFC !important;
    -webkit-text-fill-color: #F8FAFC !important;
    font-weight: 700 !important;
    visibility: visible !important;
    opacity: 1 !important;
    display: block !important;
}

/* Child elements inside headings: inherit light color without breaking inline flow */
h1 *, h2 *, h3 *, h4 *, h5 *, h6 *,
[data-testid="stHeadingWithActionElements"] h1 *,
[data-testid="stHeadingWithActionElements"] h2 *,
[data-testid="stHeadingWithActionElements"] h3 *,
[data-testid="stMarkdownContainer"] h1 *,
[data-testid="stMarkdownContainer"] h2 *,
[data-testid="stMarkdownContainer"] h3 * {
    color: #F8FAFC !important;
    -webkit-text-fill-color: #F8FAFC !important;
    font-weight: 700 !important;
    visibility: visible !important;
    opacity: 1 !important;
}

/* Captions and subtitles across app */
[data-testid="stCaptionContainer"],
[data-testid="stCaptionContainer"] p,
[data-testid="stCaptionContainer"] *,
.stCaption,
.stCaption *,
[data-testid="stMarkdownContainer"] p:not(.app-subtitle-text) {
    color: #CBD5E1 !important;
    -webkit-text-fill-color: #CBD5E1 !important;
    visibility: visible !important;
    opacity: 1 !important;
}

/* Metric card containers */
[data-testid="stMetric"] {
    background-color: #161B22 !important;
    border: 1px solid #30363D !important;
    border-radius: 10px !important;
    padding: 16px 20px !important;
    box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.4) !important;
}

/* Metric labels: light slate for high legibility */
[data-testid="stMetricLabel"],
[data-testid="stMetricLabel"] *,
[data-testid="stMetricLabelText"] {
    color: #CBD5E1 !important;
    -webkit-text-fill-color: #CBD5E1 !important;
    font-size: 0.875rem !important;
    font-weight: 600 !important;
    visibility: visible !important;
    opacity: 1 !important;
}

/* Metric values: intense light for maximum contrast */
[data-testid="stMetricValue"],
[data-testid="stMetricValue"] *,
[data-testid="stMetricValue"] div {
    color: #F8FAFC !important;
    -webkit-text-fill-color: #F8FAFC !important;
    font-size: 1.65rem !important;
    font-weight: 700 !important;
    visibility: visible !important;
    opacity: 1 !important;
}

/* Metric delta indicator */
[data-testid="stMetricDelta"],
[data-testid="stMetricDelta"] * {
    font-weight: 600 !important;
}

/* Sidebar styling and contrast */
[data-testid="stSidebar"] {
    background-color: #161B22 !important;
    border-right: 1px solid #30363D !important;
}

[data-testid="stSidebar"] label,
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p,
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] span {
    color: #F8FAFC !important;
    -webkit-text-fill-color: #F8FAFC !important;
    font-weight: 600 !important;
}

[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {
    color: #CBD5E1 !important;
    -webkit-text-fill-color: #CBD5E1 !important;
}

/* Widget labels (selectboxes, sliders) */
[data-testid="stWidgetLabel"] p,
[data-testid="stWidgetLabel"] label {
    color: #F8FAFC !important;
    -webkit-text-fill-color: #F8FAFC !important;
    font-weight: 600 !important;
}

/* Tabs styling */
[data-baseweb="tab-list"] {
    border-bottom: 1px solid #30363D !important;
    gap: 8px !important;
}

button[data-baseweb="tab"] {
    color: #CBD5E1 !important;
    -webkit-text-fill-color: #CBD5E1 !important;
    font-weight: 600 !important;
    visibility: visible !important;
    opacity: 1 !important;
}

button[data-baseweb="tab"][aria-selected="true"] {
    color: #F8FAFC !important;
    -webkit-text-fill-color: #F8FAFC !important;
    font-weight: 700 !important;
    border-bottom: 2px solid #38BDF8 !important;
    visibility: visible !important;
    opacity: 1 !important;
}

/* Alert notifications (st.success, st.info, st.warning, st.error) */
[data-testid="stAlert"] {
    background-color: #161B22 !important;
    border: 1px solid #30363D !important;
    border-radius: 8px !important;
    color: #F8FAFC !important;
}

[data-testid="stAlert"] p,
[data-testid="stAlert"] div {
    color: #F8FAFC !important;
}

/* Secondary buttons & download buttons */
button[kind="secondary"],
.stButton > button:not([kind="primary"]),
.stDownloadButton > button:not([kind="primary"]) {
    background-color: #161B22 !important;
    border: 1px solid #30363D !important;
    color: #F8FAFC !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    transition: all 0.15s ease-in-out !important;
}

button[kind="secondary"]:hover,
.stButton > button:not([kind="primary"]):hover,
.stDownloadButton > button:not([kind="primary"]):hover {
    background-color: #1E293B !important;
    border-color: #38BDF8 !important;
    color: #F8FAFC !important;
}

/* Primary buttons */
button[kind="primary"],
.stButton > button[kind="primary"],
.stDownloadButton > button[kind="primary"] {
    background-color: #0284C7 !important;
    border: 1px solid #38BDF8 !important;
    color: #F8FAFC !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    transition: all 0.15s ease-in-out !important;
}

button[kind="primary"]:hover,
.stButton > button[kind="primary"]:hover,
.stDownloadButton > button[kind="primary"]:hover {
    background-color: #0369A1 !important;
    border-color: #7DD3FC !important;
    color: #FFFFFF !important;
}

/* Plotly chart container styling: clear solid dark background */
.js-plotly-plot {
    border-radius: 8px;
    background-color: #161B22 !important;
}
</style>
"""


def apply_plotly_theme(fig: go.Figure) -> go.Figure:
    """Apply high-contrast dark theme with dark background and legible light text."""
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#161B22",
        plot_bgcolor="#161B22",
        font={
            "family": "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
            "color": "#F1F5F9",
            "size": 12,
        },
        title_font={"color": "#F8FAFC", "size": 14},
        legend={
            "font": {"color": "#CBD5E1", "size": 11},
            "title_font": {"color": "#F8FAFC", "size": 12},
        },
    )
    fig.update_xaxes(
        gridcolor="#30363D",
        linecolor="#30363D",
        tickfont={"color": "#CBD5E1", "size": 11},
        title_font={"color": "#F8FAFC", "size": 12},
    )
    fig.update_yaxes(
        gridcolor="#30363D",
        linecolor="#30363D",
        tickfont={"color": "#CBD5E1", "size": 11},
        title_font={"color": "#F8FAFC", "size": 12},
    )
    return fig
