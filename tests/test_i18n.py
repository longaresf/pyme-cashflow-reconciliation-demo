"""Unit tests for the i18n module and language consistency."""

import datetime

import plotly.graph_objects as go

from app.i18n import (
    HIGH_CONTRAST_CSS,
    LANG_EN,
    LANG_ES,
    TRANSLATIONS,
    apply_plotly_theme,
    format_week_label,
    get_aging_bucket_label,
    get_column_label,
    get_match_method_label,
    get_status_label,
    t,
)


def test_translations_parity_between_languages():
    """Ensure every key present in Spanish exists in English and vice-versa."""
    es_keys = set(TRANSLATIONS[LANG_ES].keys())
    en_keys = set(TRANSLATIONS[LANG_EN].keys())
    missing_in_en = es_keys - en_keys
    missing_in_es = en_keys - es_keys
    assert not missing_in_en, f"Keys missing in English: {missing_in_en}"
    assert not missing_in_es, f"Keys missing in Spanish: {missing_in_es}"


def test_title_and_subtitle_exact_values():
    """Verify that title and subtitle have the exact expected values in ES and EN."""
    assert t("app_title", LANG_ES) == "Control de Flujo de Caja PYME"
    assert (
        t("app_subtitle", LANG_ES)
        == "Conciliación de facturas a 3 vías y proyección móvil de liquidez a 13 semanas"
    )
    assert t("app_title", LANG_EN) == "SMB Cashflow Control"
    assert (
        t("app_subtitle", LANG_EN)
        == "Three-way invoice reconciliation and a rolling 13-week liquidity view"
    )


def test_status_labels_parity():
    """Ensure all reconciliation statuses are mapped in both languages."""
    statuses = [
        "reconciled",
        "unpaid",
        "partial_payment",
        "amount_mismatch",
        "date_mismatch",
        "erp_missing",
    ]
    for status in statuses:
        assert get_status_label(status, LANG_ES) != status
        assert get_status_label(status, LANG_EN) != ""
        assert get_status_label(status, LANG_ES) != get_status_label(status, LANG_EN)


def test_match_method_labels():
    """Ensure match methods format correctly in both languages."""
    assert get_match_method_label("reference", LANG_ES) == "Referencia exacta"
    assert get_match_method_label("fuzzy", LANG_EN) == "Fuzzy match"
    assert "Referencia exacta" in get_match_method_label("reference,fuzzy", LANG_ES)


def test_aging_bucket_labels():
    """Ensure aging bucket translations work properly."""
    assert get_aging_bucket_label("Current", LANG_ES) == "Al día"
    assert get_aging_bucket_label("Current", LANG_EN) == "Current"
    assert get_aging_bucket_label("31-60 days", LANG_ES) == "31-60 días"


def test_column_labels():
    """Ensure column labels translate properly."""
    assert get_column_label("invoice_id", LANG_ES) == "ID Factura"
    assert get_column_label("invoice_id", LANG_EN) == "Invoice ID"
    assert get_column_label("net_cashflow", LANG_ES) == "Flujo Neto"
    assert get_column_label("invoice_count", LANG_ES) == "Cantidad Facturas"
    assert get_column_label("invoice_count", LANG_EN) == "Invoice Count"
    assert get_column_label("status", LANG_ES) == "Estado"
    assert get_column_label("status", LANG_EN) == "Status"


def test_download_filenames_localized():
    """Verify download filenames are localized for both languages."""
    assert t("filename_chart_png", LANG_ES) == "desempeno_cobranzas_es.png"
    assert t("filename_chart_png", LANG_EN) == "collection_performance_en.png"
    assert t("filename_exceptions_excel", LANG_ES) == "excepciones_conciliacion_es.xlsx"
    assert (
        t("filename_exceptions_excel", LANG_EN) == "reconciliation_exceptions_en.xlsx"
    )


def test_sidebar_lang_label_exact_values():
    """Verify sidebar language selector label is localized."""
    assert t("sidebar_lang_label", LANG_ES) == "Idioma / Language"
    assert t("sidebar_lang_label", LANG_EN) == "Language / Idioma"


def test_interpolation_with_t_helper():
    """Test string format interpolation in t()."""
    text_es = t("sidebar_sources", LANG_ES, sii=10, erp=10, bank=10)
    assert "10 facturas SII" in text_es
    text_en = t("sidebar_sources", LANG_EN, sii=10, erp=10, bank=10)
    assert "10 tax invoices" in text_en


def test_format_week_label():
    """Test date formatting in Spanish and English."""
    sample_date = datetime.date(2026, 1, 15)
    assert "Ene" in format_week_label(sample_date, LANG_ES)
    assert "Jan" in format_week_label(sample_date, LANG_EN)


def test_high_contrast_css_contains_required_styles():
    """Verify that CSS contains the required contrast properties and visibility."""
    assert "#F8FAFC" in HIGH_CONTRAST_CSS
    assert "#CBD5E1" in HIGH_CONTRAST_CSS
    assert "#161B22" in HIGH_CONTRAST_CSS
    assert "#30363D" in HIGH_CONTRAST_CSS
    assert ".stApp" in HIGH_CONTRAST_CSS
    assert '[data-testid="stAppViewContainer"]' in HIGH_CONTRAST_CSS
    assert '[data-testid="stMetric"]' in HIGH_CONTRAST_CSS
    assert '[data-testid="stMetricLabel"]' in HIGH_CONTRAST_CSS
    assert '[data-testid="stMetricValue"]' in HIGH_CONTRAST_CSS
    assert '[data-testid="stAlert"]' in HIGH_CONTRAST_CSS
    assert 'button[kind="secondary"]' in HIGH_CONTRAST_CSS
    assert 'button[kind="primary"]' in HIGH_CONTRAST_CSS
    assert "visibility: visible !important" in HIGH_CONTRAST_CSS
    assert "display: none" not in HIGH_CONTRAST_CSS
    assert "visibility: hidden" not in HIGH_CONTRAST_CSS
    assert "opacity: 0" not in HIGH_CONTRAST_CSS
    assert "padding-top: 3.75rem !important" in HIGH_CONTRAST_CSS
    assert 'header[data-testid="stHeader"]' in HIGH_CONTRAST_CSS
    assert "-webkit-text-fill-color: #F8FAFC !important" in HIGH_CONTRAST_CSS
    assert "-webkit-text-fill-color: #CBD5E1 !important" in HIGH_CONTRAST_CSS
    assert ".app-title-text" in HIGH_CONTRAST_CSS
    assert ".app-subtitle-text" in HIGH_CONTRAST_CSS


def test_apply_plotly_theme():
    """Verify that apply_plotly_theme sets plotly_dark and dark backgrounds."""
    fig = go.Figure(go.Scatter(x=[1, 2], y=[3, 4]))
    themed_fig = apply_plotly_theme(fig)
    layout = themed_fig.layout
    assert layout.template is not None
    assert layout.paper_bgcolor == "#161B22"
    assert layout.plot_bgcolor == "#161B22"
    assert layout.font.color == "#F1F5F9"


def test_app_main_import_and_helpers():
    """Verify app.main can be imported and helper functions work."""
    import pandas as pd

    from app.main import _exception_workbook, _format_money
    from src.reconciler import ReconciliationResult

    assert _format_money(12345.6) == "$12,346 CLP"
    dummy_result = ReconciliationResult(
        invoices=pd.DataFrame(
            [
                {
                    "invoice_id": "INV-1",
                    "reconciliation_status": "erp_missing",
                    "total_amount": 100,
                }
            ]
        ),
        unmatched_bank=pd.DataFrame(
            [{"transaction_id": "BNK-1", "credit": 100, "debit": 0}]
        ),
    )
    excel_bytes_es = _exception_workbook(dummy_result, lang=LANG_ES)
    assert len(excel_bytes_es) > 0
    excel_bytes_en = _exception_workbook(dummy_result, lang=LANG_EN)
    assert len(excel_bytes_en) > 0


def test_create_collection_report_multilingual(tmp_path):
    """Verify static collection report generates correctly in ES and EN."""
    import pandas as pd

    from src.static_charts import create_collection_report

    sample_df = pd.DataFrame(
        [
            {
                "invoice_id": "INV-1",
                "invoice_date": "2025-01-01",
                "first_payment_date": "2025-01-20",
                "total_amount": 1000,
                "bank_amount": 1000,
            }
        ]
    )
    p_es = tmp_path / "chart_es.png"
    p_en = tmp_path / "chart_en.png"
    create_collection_report(sample_df, p_es, lang="es")
    create_collection_report(sample_df, p_en, lang="en")
    assert p_es.exists() and p_es.stat().st_size > 0
    assert p_en.exists() and p_en.stat().st_size > 0
