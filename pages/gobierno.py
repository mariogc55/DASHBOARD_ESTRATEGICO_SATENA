"""Panel superior: Gobierno estratégico de la IA."""
from __future__ import annotations
import dash_bootstrap_components as dbc
from dash import Input, Output, no_update, dcc, html
from src.analytics import compute_compliance_radar, compute_governance_kpis
from src.components import (
    build_compliance_radar,
    build_gobierno_datos_bar,
    build_model_inventory_table,
    empty_state_card,
    no_data_kpi,
    kpi_card,
)
from src.data_manager import DataManager
from src.utils import format_percent


def layout() -> dbc.Container:
    return dbc.Container(
        [
            html.H4("Gobierno de la IA — SATENA", className="satena-section-title"),
            html.P(
                "Framework: Adaptive Governance · Metadata Layer · Integrations",
                className="text-muted mb-3",
            ),
            dbc.Row(
                [
                    dbc.Col(html.Div(id="kpi-total-prod"), md=3, sm=6, className="mb-3"),
                    dbc.Col(html.Div(id="kpi-doc"), md=3, sm=6, className="mb-3"),
                    dbc.Col(html.Div(id="kpi-audit"), md=3, sm=6, className="mb-3"),
                    dbc.Col(html.Div(id="kpi-cumplimiento"), md=3, sm=6, className="mb-3"),
                ],
                className="mb-2",
            ),
            html.Div(id="cobit-health-summary", className="mb-3"),
            html.H5("Inventario de Modelos", className="satena-section-title"),
            html.Div(id="inventario-modelos-container"),
            dbc.Row(
                [
                    # FIX: figure={} como valor inicial para evitar prop inválido
                    dbc.Col(dcc.Graph(id="graph-gobierno-datos", figure={}), lg=6, className="mb-3"),
                    dbc.Col(dcc.Graph(id="graph-cumplimiento-radar", figure={}), lg=6, className="mb-3"),
                ]
            ),
        ],
        fluid=True,
        className="px-0",
    )


def register_callbacks(app, dm: DataManager) -> None:
    @app.callback(
        Output("kpi-total-prod", "children"),
        Output("kpi-doc", "children"),
        Output("kpi-audit", "children"),
        Output("kpi-cumplimiento", "children"),
        Output("inventario-modelos-container", "children"),
        Output("graph-gobierno-datos", "figure"),
        Output("graph-cumplimiento-radar", "figure"),
        Output("cobit-health-summary", "children"),
        Input("auth-store", "data"),
        Input("session-data-store", "data"),
        Input("cobit-validation-store", "data"),
        prevent_initial_call=False,
    )
    def load_gobierno(auth_data, session_data, cobit_validation):
        # FIX: retorno correcto por tipo — figuras reciben {} no un componente Alert
        if not auth_data or not auth_data.get("authenticated"):
            alert = dbc.Alert("Acceso restringido", color="warning")
            return alert, alert, alert, alert, alert, {}, {}, alert

        if not session_data:
            nd = no_data_kpi
            es = empty_state_card
            sin_datos_cobit = dbc.Alert(
                "Cargue un archivo Excel para visualizar el estado de cumplimiento COBIT 2019.",
                color="secondary", className="mb-0 py-2",
            )
            return (
                nd("Modelos en produccion"),
                nd("Documentacion tecnica"),
                nd("Auditoria vigente"),
                nd("Cumplimiento global"),
                es("Sin inventario", "Cargue datos para ver los modelos registrados.", 220),
                {}, {},
                sin_datos_cobit,
            )

        modelos = dm.get_modelos(session_data)
        kpis = compute_governance_kpis(modelos)
        gobierno_df = dm.get_gobierno_datos(session_data)
        fig_datos = build_gobierno_datos_bar(gobierno_df, modelos)
        fig_radar = build_compliance_radar(compute_compliance_radar())

        cobit_health = cobit_validation or {}
        status = cobit_health.get("status")
        filename = cobit_health.get("filename", "archivo")

        if status == "success":
            cobit_alert = dbc.Alert(
                [
                    html.Strong(
                        "Éxito: El archivo cumple con los Criterios de Calidad de la Información de COBIT 2019 "
                        "(Exactitud, Integridad y Consistencia)."
                    ),
                    html.Br(),
                    html.Span("Fuente: "),
                    html.Code(str(filename)),
                ],
                color="success",
                className="mb-0 py-2",
            )
            warnings = cobit_health.get("warnings") or []
            if warnings:
                cobit_alert = html.Div(
                    [
                        cobit_alert,
                        dbc.Alert(
                            [html.Strong("Ajustes automáticos: "), html.Ul([html.Li(w) for w in warnings])],
                            color="warning",
                            className="mb-0 py-2 mt-2",
                        ),
                    ]
                )
        elif status == "fail":
            errors = cobit_health.get("errors") or []
            cobit_alert = dbc.Alert(
                [
                    html.Strong("Error de COBIT 2019: "),
                    html.Ul([html.Li(e) for e in errors]) if errors else html.Li("Detalles no disponibles."),
                    html.Br(),
                    html.Span("Fuente: "),
                    html.Code(str(filename)),
                ],
                color="danger",
                className="mb-0 py-2",
            )
        else:
            cobit_alert = dbc.Alert(
                [html.Strong("Salud COBIT 2019: "), "Estado no disponible para el último archivo."],
                color="secondary",
                className="mb-0 py-2",
            )

        return (
            kpi_card("Modelos en producción", str(kpis["total_produccion"]), "SIOP-DS auditado"),
            kpi_card("% Documentación técnica", format_percent(kpis["pct_documentacion"]), "Meta ≥ 90%"),
            kpi_card("% Auditoría vigente", format_percent(kpis["pct_auditoria"]), "Human-in-the-loop"),
            kpi_card("% Cumplimiento global", format_percent(kpis["pct_cumplimiento"]), "Marcos regulatorios"),
            build_model_inventory_table(modelos),
            fig_datos,
            fig_radar,
            cobit_alert,
        )
