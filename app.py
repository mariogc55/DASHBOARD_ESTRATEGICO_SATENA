"""
Dashboard Estrategico Integral de Gobernanza de IA - SATENA.
Punto de entrada: login con credenciales demo y orquestacion de modulos Dash.
"""

from __future__ import annotations

import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, State, ctx, dcc, html, no_update

from pages import (
    drift,
    explicabilidad,
    fairness,
    gobierno,
    mlops,
    seguridad,
    sesgos,
    versionado,
)
from src.data_manager import get_data_manager, parse_upload_to_session_payload
from src.validator import validate_excel_bytes
from src.utils import DEFAULT_PASSWORD, DEFAULT_USER, hash_password, verify_password

EXTERNAL_STYLESHEETS = [dbc.themes.BOOTSTRAP]

app = dash.Dash(
    __name__,
    external_stylesheets=EXTERNAL_STYLESHEETS,
    suppress_callback_exceptions=True,
    title="SATENA - Gobernanza de IA",
)
server = app.server

app.index_string = """<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        <link rel="icon" type="image/svg+xml" href="/assets/satena_favicon.svg">
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
        {%css%}
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>"""

dm = get_data_manager()
PASSWORD_HASH = hash_password(DEFAULT_PASSWORD)

_cobit_health_initial: dict | None = None


def login_layout() -> html.Div:
    return html.Div(
        [
            # ---- Panel izquierdo: marca SATENA ----
            html.Div(
                [
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Span("S", className="login-brand-letter letter-s"),
                                    html.Span("A", className="login-brand-letter letter-a"),
                                    html.Span("T", className="login-brand-letter letter-t"),
                                    html.Span("E", className="login-brand-letter letter-e"),
                                    html.Span("N", className="login-brand-letter letter-n"),
                                    html.Span("A", className="login-brand-letter letter-a2"),
                                ],
                                className="login-panel-brand-word",
                            ),
                            html.Div(className="login-panel-divider"),
                            html.P(
                                "Dashboard Estrategico Integral",
                                className="login-panel-tagline",
                            ),
                            html.P(
                                "Gobernanza de Inteligencia Artificial",
                                className="login-panel-sub",
                            ),
                        ],
                        className="login-panel-content",
                    ),
                ],
                className="login-brand-panel",
            ),
            # ---- Panel derecho: formulario ----
            html.Div(
                [
                    html.Div(
                        [
                            html.Div(className="login-form-accent-bar"),
                            html.H2("Iniciar sesion", className="login-form-title"),
                            html.P(
                                "Ingrese sus credenciales de acceso al sistema",
                                className="login-form-subtitle",
                            ),
                            html.Div(
                                [
                                    dbc.Label("Usuario", className="login-label"),
                                    dbc.Input(
                                        id="login-user",
                                        type="text",
                                        placeholder=DEFAULT_USER,
                                        className="login-input",
                                        autocomplete="username",
                                    ),
                                ],
                                className="mb-3",
                            ),
                            html.Div(
                                [
                                    dbc.Label("Contrasena", className="login-label"),
                                    dbc.Input(
                                        id="login-password",
                                        type="password",
                                        placeholder=chr(8226) * 8,
                                        className="login-input",
                                        autocomplete="current-password",
                                    ),
                                ],
                                className="mb-4",
                            ),
                            dbc.Button(
                                "Acceder al sistema",
                                id="btn-login",
                                color="primary",
                                className="w-100 btn-login-submit",
                                size="lg",
                                n_clicks=0,
                            ),
                            html.Div(id="login-feedback", className="mt-3"),
                            html.Hr(className="login-divider"),
                            html.Small(
                                [
                                    html.Span("Acceso demo: ", className="fw-semibold text-muted"),
                                    html.Code(DEFAULT_USER, className="login-demo-code"),
                                ],
                                className="d-block text-center",
                            ),
                        ],
                        className="login-form-inner",
                    ),
                ],
                className="login-form-panel",
            ),
        ],
        className="login-split-container",
    )


def _modal_limpiar_datos() -> dbc.Modal:
    return dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("Confirmar limpieza de datos"), close_button=True),
            dbc.ModalBody(
                [
                    html.P(
                        "Esta accion eliminara el archivo Excel cargado y restaurara "
                        "el dashboard a los datos de demostracion por defecto.",
                        className="mb-2",
                    ),
                    dbc.Alert(
                        "Los graficos y metricas volveran a su estado inicial. "
                        "Esta accion no puede deshacerse.",
                        color="warning",
                        className="mb-0 py-2",
                    ),
                ]
            ),
            dbc.ModalFooter(
                [
                    dbc.Button(
                        "Cancelar",
                        id="btn-limpiar-cancelar",
                        color="secondary",
                        outline=True,
                        size="sm",
                        className="me-2",
                    ),
                    dbc.Button(
                        "Si, limpiar datos",
                        id="btn-limpiar-confirmar",
                        color="danger",
                        size="sm",
                    ),
                ]
            ),
        ],
        id="modal-limpiar-datos",
        is_open=False,
        centered=True,
    )


def dashboard_layout() -> html.Div:
    return html.Div(
        [
            _modal_limpiar_datos(),
            dbc.Navbar(
                dbc.Container(
                    [
                        dbc.Row(
                            [
                                dbc.Col(
                                    dbc.NavbarBrand(
                                        "SATENA - Dashboard Gobernanza de IA",
                                        className="fw-bold me-2",
                                    ),
                                    width="auto",
                                    className="d-flex align-items-center",
                                ),
                                dbc.Col(
                                    dbc.NavLink("SIOP-DS Alto Riesgo", className="text-warning mb-0"),
                                    width="auto",
                                    className="d-flex align-items-center",
                                ),
                                dbc.Col(width=True),
                                dbc.Col(
                                    dcc.Upload(
                                        id="upload-data-xlsx",
                                        children=dbc.Button(
                                            "Cargar Excel",
                                            color="light",
                                            size="sm",
                                            className="text-nowrap navbar-action-btn",
                                        ),
                                        accept=".xlsx",
                                        multiple=False,
                                        style={"display": "inline-block"},
                                        className="me-2",
                                    ),
                                    width="auto",
                                    className="d-flex align-items-center",
                                ),
                                dbc.Col(
                                    dbc.Button(
                                        "Limpiar Datos",
                                        id="btn-limpiar-datos",
                                        color="danger",
                                        size="sm",
                                        className="text-nowrap me-2 navbar-action-btn",
                                    ),
                                    width="auto",
                                    className="d-flex align-items-center",
                                ),
                                dbc.Col(
                                    dbc.Button(
                                        "Cerrar sesion",
                                        id="btn-logout",
                                        color="light",
                                        size="sm",
                                        outline=True,
                                    ),
                                    width="auto",
                                    className="d-flex align-items-center",
                                ),
                            ],
                            className="w-100 align-items-center gy-2",
                        ),
                        dbc.Row(
                            [
                                dbc.Col(
                                    html.Div(id="upload-data-status", className="small mt-2"),
                                    width=12,
                                ),
                            ],
                            className="w-100",
                        ),
                    ],
                    fluid=True,
                ),
                color="primary",
                dark=True,
                className="satena-navbar mb-4",
            ),
            dbc.Container(
                [
                    gobierno.layout(),
                    html.Hr(),
                    html.H4("Gestion Operativa de la IA", className="satena-section-title"),
                    dbc.Tabs(
                        id="main-tabs",
                        active_tab="tab-mlops",
                        children=[
                            dbc.Tab(label="MLOps", tab_id="tab-mlops", children=mlops.layout()),
                            dbc.Tab(label="Versionado", tab_id="tab-versionado", children=versionado.layout()),
                            dbc.Tab(label="Monitoreo y Drift", tab_id="tab-drift", children=drift.layout()),
                            dbc.Tab(
                                label="Explicabilidad",
                                tab_id="tab-explicabilidad",
                                children=explicabilidad.layout(),
                            ),
                            dbc.Tab(
                                label="Auditoria y Fairness",
                                tab_id="tab-fairness",
                                children=fairness.layout(),
                            ),
                            dbc.Tab(label="Sesgos y Robustez", tab_id="tab-sesgos", children=sesgos.layout()),
                            dbc.Tab(label="Seguridad", tab_id="tab-seguridad", children=seguridad.layout()),
                        ],
                        className="mb-4",
                    ),
                ],
                fluid=True,
            ),
        ]
    )


app.layout = html.Div(
    [
        dcc.Store(id="auth-store", data={"authenticated": False, "user": None}),
        dcc.Store(id="session-data-store", data=None),
        dcc.Store(id="cobit-validation-store", data=_cobit_health_initial),
        html.Div(id="page-router", children=login_layout()),
    ]
)


@app.callback(
    Output("auth-store", "data"),
    Output("page-router", "children"),
    Output("login-feedback", "children"),
    Input("btn-login", "n_clicks"),
    State("login-user", "value"),
    State("login-password", "value"),
    prevent_initial_call=True,
)
def login(n_clicks, user, password):
    if not user or not password:
        return no_update, no_update, dbc.Alert("Complete usuario y contrasena.", color="warning")
    if user.strip() != DEFAULT_USER or not verify_password(password, PASSWORD_HASH):
        return no_update, no_update, dbc.Alert("Credenciales invalidas.", color="danger")
    auth = {"authenticated": True, "user": user.strip()}
    return auth, dashboard_layout(), None


@app.callback(
    Output("auth-store", "data", allow_duplicate=True),
    Output("page-router", "children", allow_duplicate=True),
    Output("session-data-store", "data", allow_duplicate=True),
    Output("cobit-validation-store", "data", allow_duplicate=True),
    Input("btn-logout", "n_clicks"),
    prevent_initial_call=True,
)
def logout(n_clicks):
    if not n_clicks:
        return no_update, no_update, no_update, no_update
    return {"authenticated": False, "user": None}, login_layout(), None, _cobit_health_initial


@app.callback(
    Output("session-data-store", "data", allow_duplicate=True),
    Output("upload-data-status", "children"),
    Output("cobit-validation-store", "data", allow_duplicate=True),
    Input("upload-data-xlsx", "contents"),
    State("upload-data-xlsx", "filename"),
    prevent_initial_call=True,
)
def on_upload_workbook(contents, filename):
    payload, warnings, errors = parse_upload_to_session_payload(contents, filename)
    if errors:
        return (
            no_update,
            dbc.Alert(
                [
                    html.Strong("Error en criterios COBIT 2019: "),
                    html.Ul([html.Li(e) for e in errors]),
                ],
                color="danger",
                dismissable=True,
                className="mb-0 py-2",
            ),
            {
                "status": "fail",
                "filename": filename or "archivo.xlsx",
                "warnings": warnings,
                "errors": errors,
            },
        )
    if payload is None:
        return no_update, "", no_update
    parts: list = [
        dbc.Alert(
            [
                html.Strong(
                    "Exito COBIT 2019: el archivo cumple criterios de Exactitud, Integridad y Consistencia."
                ),
                html.Br(),
                html.Span("Origen de datos: "),
                html.Code(str(payload.get("filename", "archivo"))),
            ],
            color="success",
            dismissable=True,
            className="mb-1 py-2",
        )
    ]
    if warnings:
        parts.append(
            dbc.Alert(
                [
                    html.Strong("Ajustes automaticos aplicados: "),
                    html.Ul([html.Li(w) for w in warnings]),
                ],
                color="warning",
                dismissable=True,
                className="mb-0 py-2",
            )
        )
    return (
        payload,
        parts,
        {
            "status": "success",
            "filename": str(payload.get("filename", "archivo")),
            "warnings": warnings,
            "errors": [],
        },
    )


@app.callback(
    Output("modal-limpiar-datos", "is_open"),
    Input("btn-limpiar-datos", "n_clicks"),
    Input("btn-limpiar-cancelar", "n_clicks"),
    Input("btn-limpiar-confirmar", "n_clicks"),
    State("modal-limpiar-datos", "is_open"),
    prevent_initial_call=True,
)
def toggle_modal_limpiar(n_abrir, n_cancelar, n_confirmar, is_open):
    trigger = ctx.triggered_id
    if trigger == "btn-limpiar-datos":
        return True
    if trigger in ("btn-limpiar-cancelar", "btn-limpiar-confirmar"):
        return False
    return is_open


@app.callback(
    Output("session-data-store", "data", allow_duplicate=True),
    Output("cobit-validation-store", "data", allow_duplicate=True),
    Output("upload-data-status", "children", allow_duplicate=True),
    Input("btn-limpiar-confirmar", "n_clicks"),
    prevent_initial_call=True,
)
def limpiar_datos(n_clicks):
    if not n_clicks:
        return no_update, no_update, no_update
    status_msg = dbc.Alert(
        [
            html.Strong("Datos limpiados. "),
            "El dashboard muestra ahora los datos de demostracion por defecto.",
        ],
        color="info",
        dismissable=True,
        className="mb-0 py-2",
    )
    return None, _cobit_health_initial, status_msg


gobierno.register_callbacks(app, dm)
mlops.register_callbacks(app, dm)
versionado.register_callbacks(app, dm)
drift.register_callbacks(app, dm)
explicabilidad.register_callbacks(app, dm)
fairness.register_callbacks(app, dm)
sesgos.register_callbacks(app, dm)
seguridad.register_callbacks(app, dm)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8050)
