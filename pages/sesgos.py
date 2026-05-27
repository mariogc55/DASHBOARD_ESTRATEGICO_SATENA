"""Tab 6: Sesgos y robustez adversarial."""
from __future__ import annotations
import dash_bootstrap_components as dbc
from dash import Input, Output, no_update, dcc, html
# FIX: renombrar la función analítica para evitar colisión con la función de componentes
from src.analytics import compute_adversarial_resilience, compute_bias_heatmap as compute_bias_df
from src.components import build_adversarial_bar, build_bias_heatmap, empty_state_card
from src.data_manager import DataManager


def layout() -> dbc.Container:
    return dbc.Container(
        [
            html.H5("Sesgos y Robustez", className="satena-section-title"),
            dbc.Row(
                [
                    # FIX: figure={} para evitar prop inválido en carga inicial
                    dbc.Col(dcc.Graph(id="graph-sesgos-heatmap", figure={}), lg=6),
                    dbc.Col(dcc.Graph(id="graph-adversarial-bar", figure={}), lg=6),
                ]
            ),
        ],
        fluid=True,
        className="px-0",
    )


def register_callbacks(app, dm: DataManager) -> None:
    @app.callback(
        Output("graph-sesgos-heatmap", "figure"),
        Output("graph-adversarial-bar", "figure"),
        Input("auth-store", "data"),
        Input("session-data-store", "data"),
        Input("main-tabs", "active_tab"),
        prevent_initial_call=False,
    )
    def load_sesgos(auth_data, session_data, active_tab):
        if not auth_data or not auth_data.get("authenticated"):
            return {}, {}
        if not session_data:
            return {}, {}
        if active_tab != "tab-sesgos":
            return no_update, no_update
        _ = dm, session_data
        # FIX: usar compute_bias_df (renombrada) para el DataFrame, build_bias_heatmap para la figura
        bias = compute_bias_df()
        adv = compute_adversarial_resilience()
        return build_bias_heatmap(bias), build_adversarial_bar(adv)
