"""Tab 2: Versionado del modelo SIOP-DS."""
from __future__ import annotations
import dash_bootstrap_components as dbc
# FIX: no_update importado al nivel del módulo
from dash import Input, Output, no_update, dash_table, dcc, html
from src.components import build_version_line, empty_state_card
from src.data_manager import DataManager
from src.utils import SATENA_AZUL, SATENA_BLANCO


def layout() -> dbc.Container:
    return dbc.Container(
        [
            html.H5("Versionado — SIOP-DS", className="satena-section-title"),
            html.Div(id="tabla-versiones-siop"),
            # FIX: figure={} para evitar prop inválido en carga inicial
            dcc.Graph(id="graph-versiones-metricas", figure={}, className="mt-3"),
        ],
        fluid=True,
        className="px-0",
    )


def register_callbacks(app, dm: DataManager) -> None:
    @app.callback(
        Output("tabla-versiones-siop", "children"),
        Output("graph-versiones-metricas", "figure"),
        Input("auth-store", "data"),
        Input("session-data-store", "data"),
        Input("main-tabs", "active_tab"),
        prevent_initial_call=False,
    )
    def load_versionado(auth_data, session_data, active_tab):
        if not auth_data or not auth_data.get("authenticated"):
            return dbc.Alert("Acceso restringido", color="warning"), {}
        if not session_data:
            es = empty_state_card("Sin historial de versiones", "Cargue un archivo Excel para ver el versionado de SIOP-DS.", 260)
            return es, {}
        if active_tab != "tab-versionado":
            return no_update, no_update

        siop = dm.get_siop_versions(session_data)

        # FIX: manejar caso sin versiones SIOP-DS en datos de sesión
        if siop.empty:
            msg = dbc.Alert("No se encontraron versiones de SIOP-DS en los datos cargados.", color="warning")
            return msg, {}

        display = siop[
            ["Version", "Fecha_Despliegue", "Estado", "Accuracy", "F1_Score", "Nivel_Riesgo"]
        ].copy()
        display["Fecha_Despliegue"] = display["Fecha_Despliegue"].dt.strftime("%Y-%m-%d")
        tabla = dash_table.DataTable(
            columns=[{"name": c, "id": c} for c in display.columns],
            data=display.to_dict("records"),
            style_header={"backgroundColor": SATENA_AZUL, "color": SATENA_BLANCO},
            style_cell={"padding": "8px"},
            page_size=6,
        )
        return tabla, build_version_line(siop)
