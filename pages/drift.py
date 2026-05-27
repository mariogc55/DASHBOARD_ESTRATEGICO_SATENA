"""Tab 3: Monitoreo y drift técnico."""
from __future__ import annotations
import dash_bootstrap_components as dbc
# FIX: no_update importado al nivel del módulo, no dentro del callback
from dash import Input, Output, no_update, dcc, html
from src.analytics import compute_drift_summary
from src.components import alert_card, build_histogram_comparison, build_psi_timeline
from src.data_manager import DataManager


def layout() -> dbc.Container:
    return dbc.Container(
        [
            html.H5("Monitoreo y Drift — SIOP-DS", className="satena-section-title"),
            dbc.Row(
                [
                    # FIX: figure={} para evitar prop inválido en tabs inactivos
                    dbc.Col(dcc.Graph(id="graph-psi-timeline", figure={}), lg=8),
                    dbc.Col(html.Div(id="drift-ks-cards"), lg=4),
                ],
                className="mb-3",
            ),
            html.Div(id="drift-alert-cards", className="mb-3"),
            dcc.Graph(id="graph-drift-histogram", figure={}),
        ],
        fluid=True,
        className="px-0",
    )


def register_callbacks(app, dm: DataManager) -> None:
    @app.callback(
        Output("graph-psi-timeline", "figure"),
        Output("drift-ks-cards", "children"),
        Output("drift-alert-cards", "children"),
        Output("graph-drift-histogram", "figure"),
        Input("auth-store", "data"),
        Input("session-data-store", "data"),
        Input("main-tabs", "active_tab"),
        prevent_initial_call=False,
    )
    def load_drift(auth_data, session_data, active_tab):
        if not auth_data or not auth_data.get("authenticated"):
            return {}, dbc.Alert("Acceso restringido", color="warning"), None, {}
        if active_tab != "tab-drift":
            return no_update, no_update, no_update, no_update

        drift_df = dm.get_drift(session_data)
        summary = compute_drift_summary(drift_df)

        # FIX: manejar caso de datos vacíos (p.ej. ID_Modelo no encontrado)
        if drift_df.empty:
            empty_alert = dbc.Alert(
                "No se encontraron registros de drift para el modelo seleccionado.",
                color="warning",
            )
            return {}, empty_alert, [], {}

        ks_card = dbc.Card(
            dbc.CardBody(
                [
                    html.H6("KS-Test (Kolmogorov-Smirnov)", className="mb-3"),
                    html.P(f"Estadístico: {summary['ks_statistic']:.4f}"),
                    html.P(f"p-value: {summary['ks_pvalue']:.4f}"),
                    html.H5(
                        summary["ks_estado"],
                        className="semaforo-verde" if summary["ks_estado"] == "Pasa" else "semaforo-rojo",
                    ),
                    html.Hr(),
                    html.Small(
                        f"PSI calculado (numpy): {summary['psi_calculated']:.4f} | "
                        f"Último PSI registrado: {summary['psi_latest']:.4f}"
                    ),
                ]
            ),
            className="satena-card",
        )
        alertas = [
            alert_card(
                summary["severidad"],
                f"Degradación detectada en SIOP-DS. PSI={summary['psi_latest']:.3f} "
                f"(umbral {summary['umbral_psi']}). Revise reentrenamiento.",
            )
        ]
        return (
            build_psi_timeline(drift_df),
            ks_card,
            alertas,
            build_histogram_comparison(summary["reference"], summary["current"]),
        )
