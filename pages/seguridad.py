"""Tab 7: Seguridad, incidentes y MFA."""
from __future__ import annotations
import dash_bootstrap_components as dbc
# FIX: no_update importado al nivel del módulo
from dash import Input, Output, no_update, dcc, html
from src.components import build_attack_timeline, build_incidents_table, empty_state_card, kpi_card
from src.data_manager import DataManager
from src.utils import format_percent


def layout() -> dbc.Container:
    return dbc.Container(
        [
            html.H5("Seguridad — Incidentes y MFA", className="satena-section-title"),
            dbc.Row(
                [
                    dbc.Col(html.Div(id="seguridad-kpi-mfa"), md=4, className="mb-3"),
                    # FIX: figure={} para evitar prop inválido en carga inicial
                    dbc.Col(dcc.Graph(id="graph-ataques-timeline", figure={}), md=8, className="mb-3"),
                ]
            ),
            html.Div(id="seguridad-tabla-incidentes"),
        ],
        fluid=True,
        className="px-0",
    )


def register_callbacks(app, dm: DataManager) -> None:
    @app.callback(
        Output("seguridad-kpi-mfa", "children"),
        Output("graph-ataques-timeline", "figure"),
        Output("seguridad-tabla-incidentes", "children"),
        Input("auth-store", "data"),
        Input("session-data-store", "data"),
        Input("main-tabs", "active_tab"),
        prevent_initial_call=False,
    )
    def load_seguridad(auth_data, session_data, active_tab):
        if not auth_data or not auth_data.get("authenticated"):
            return dbc.Alert("Acceso restringido", color="warning"), {}, None
        if not session_data:
            es = empty_state_card("Sin datos de seguridad", "Cargue un archivo Excel para ver incidentes y cobertura MFA.", 240)
            return es, {}, es
        if active_tab != "tab-seguridad":
            return no_update, no_update, no_update

        seguridad = dm.get_seguridad(session_data)
        cobertura_mfa = 0.96
        return (
            kpi_card(
                "Cobertura MFA — Oficina de TI",
                format_percent(cobertura_mfa),
                "2FA obligatorio en consolas críticas",
            ),
            build_attack_timeline(seguridad),
            build_incidents_table(seguridad),
        )
