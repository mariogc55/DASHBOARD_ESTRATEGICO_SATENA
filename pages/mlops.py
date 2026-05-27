"""Tab 1: MLOps — despliegues y CI/CD."""
from __future__ import annotations
import dash_bootstrap_components as dbc
# FIX: no_update importado al nivel del módulo
from dash import Input, Output, no_update, dcc, html
from src.analytics import compute_mlops_metrics
from src.components import build_fases_bar, build_mlops_timeline, kpi_card
from src.data_manager import DataManager
from src.utils import format_percent


def layout() -> dbc.Container:
    return dbc.Container(
        [
            html.H5("MLOps — Ciclo de vida y pipelines", className="satena-section-title"),
            dbc.Row(
                [
                    dbc.Col(html.Div(id="mlops-kpi-pipeline"), md=4, className="mb-3"),
                    # FIX: figure={} para evitar prop inválido en carga inicial
                    dbc.Col(dcc.Graph(id="graph-mlops-timeline", figure={}), md=8, className="mb-3"),
                ]
            ),
            dbc.Row(
                [
                    dbc.Col(dcc.Graph(id="graph-mlops-fases", figure={}), md=12),
                ]
            ),
        ],
        fluid=True,
        className="px-0",
    )


def register_callbacks(app, dm: DataManager) -> None:
    @app.callback(
        Output("mlops-kpi-pipeline", "children"),
        Output("graph-mlops-timeline", "figure"),
        Output("graph-mlops-fases", "figure"),
        Input("auth-store", "data"),
        Input("session-data-store", "data"),
        Input("main-tabs", "active_tab"),
        prevent_initial_call=False,
    )
    def load_mlops(auth_data, session_data, active_tab):
        if not auth_data or not auth_data.get("authenticated"):
            return dbc.Alert("Acceso restringido", color="warning"), {}, {}
        if active_tab != "tab-mlops":
            return no_update, no_update, no_update

        modelos = dm.get_modelos(session_data)
        metrics = compute_mlops_metrics(modelos)
        return (
            kpi_card(
                "Tasa éxito CI/CD",
                format_percent(metrics["pipeline_exito"]),
                "Últimos 30 días",
            ),
            build_mlops_timeline(metrics["timeline"]),
            build_fases_bar(metrics["fases"]),
        )
