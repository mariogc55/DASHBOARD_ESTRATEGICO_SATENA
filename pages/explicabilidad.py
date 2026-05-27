"""Tab 4: Explicabilidad SHAP."""
from __future__ import annotations
import dash_bootstrap_components as dbc
# FIX: no_update importado al nivel del módulo
from dash import Input, Output, no_update, dcc, html
from src.analytics import compute_shap_values
from src.components import build_shap_bar
from src.data_manager import DataManager


def layout() -> dbc.Container:
    return dbc.Container(
        [
            html.H5("Explicabilidad — Interpretabilidad del modelo", className="satena-section-title"),
            html.P(
                "Valores SHAP promedio por variable de entrada del modelo de demanda social (SIOP-DS).",
                className="text-muted",
            ),
            # FIX: figure={} para evitar prop inválido en carga inicial
            dcc.Graph(id="graph-shap-bars", figure={}),
        ],
        fluid=True,
        className="px-0",
    )


def register_callbacks(app, dm: DataManager) -> None:
    @app.callback(
        Output("graph-shap-bars", "figure"),
        Input("auth-store", "data"),
        Input("session-data-store", "data"),
        Input("main-tabs", "active_tab"),
        prevent_initial_call=False,
    )
    def load_shap(auth_data, session_data, active_tab):
        if not auth_data or not auth_data.get("authenticated"):
            return {}
        if active_tab != "tab-explicabilidad":
            return no_update
        _ = dm, session_data
        shap_df = compute_shap_values()
        return build_shap_bar(shap_df)
