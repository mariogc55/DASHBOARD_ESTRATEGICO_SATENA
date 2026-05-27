"""
Dashboard Estratégico Integral de Gobernanza de IA — SATENA.
Punto de entrada: login con credenciales demo y orquestación de módulos Dash.
"""

from __future__ import annotations

import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, State, dcc, html, no_update

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
    title="SATENA — Gobernanza de IA",
)
server = app.server

dm = get_data_manager()
PASSWORD_HASH = hash_password(DEFAULT_PASSWORD)

# Salud COBIT inicial (datos por defecto local) para que el panel superior
# muestre estado aunque el usuario no haya subido un Excel.
_cobit_health_initial: dict | None = None
try:
    _out = validate_excel_bytes(dm.workbook_path.read_bytes(), filename=str(dm.workbook_path.name))
    _cobit_health_initial = {
        "status": "success" if _out.ok else "fail",
        "filename": str(dm.workbook_path.name),
        "warnings": _out.warnings,
        "errors": _out.errors,
    }
except Exception as exc:  # noqa: BLE001
    _cobit_health_initial = {
        "status": "unknown",
        "filename": str(dm.workbook_path.name),
        "warnings": [],
        "errors": [str(exc)],
    }


def login_layout() -> dbc.Container:
    return dbc.Container(
        [
            dbc.Card(
                dbc.CardBody(
                    [
                        html.H3("SATENA — Gobernanza de IA", className="text-center mb-1"),
                        html.P(
                            "Ingrese sus credenciales de acceso",
                            className="text-center text-muted mb-4",
                        ),
                        dbc.Label("Usuario"),
                        dbc.Input(
                            id="login-user",
                            type="text",
                            placeholder=DEFAULT_USER,
                            className="mb-3",
                        ),
                        dbc.Label("Contraseña"),
                        dbc.Input(
                            id="login-password",
                            type="password",
                            placeholder="••••••••",
                            className="mb-3",
                        ),
                        dbc.Button(
                            "Iniciar sesión",
                            id="btn-login",
                            color="primary",
                            className="w-100",
                        ),
                        html.Div(id="login-feedback", className="mt-3"),
                        html.Small(
                            f"Credenciales demo — Usuario: {DEFAULT_USER}",
                            className="d-block text-center text-muted mt-3",
                        ),
                    ]
                ),
                className="satena-card login-container",
            )
        ],
        className="login-container",
    )


def dashboard_layout() -> html.Div:
    return html.Div(
        [
            dbc.Navbar(
                dbc.Container(
                    [
                        dbc.Row(
                            [
                                dbc.Col(
                                    dbc.NavbarBrand(
                                        "SATENA — Dashboard Gobernanza de IA",
                                        className="fw-bold me-2",
                                    ),
                                    width="auto",
                                    className="d-flex align-items-center",
                                ),
                                dbc.Col(
                                    dbc.NavLink("SIOP-DS · Alto Riesgo", className="text-warning mb-0"),
                                    width="auto",
                                    className="d-flex align-items-center",
                                ),
                                dbc.Col(width=True),
                                dbc.Col(
                                    dcc.Upload(
                                        id="upload-data-xlsx",
                                        children=dbc.Button(
                                            "Cargar Excel de datos",
                                            color="light",
                                            size="sm",
                                            className="text-nowrap",
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
                                        "Cerrar sesión",
                                        id="btn-logout",
                                        color="light",
                                        size="sm",
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
                    html.H4("Gestión Operativa de la IA", className="satena-section-title"),
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
                                label="Auditoría y Fairness",
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
        return no_update, no_update, dbc.Alert("Complete usuario y contraseña.", color="warning")
    if user.strip() != DEFAULT_USER or not verify_password(password, PASSWORD_HASH):
        return no_update, no_update, dbc.Alert("Credenciales inválidas.", color="danger")
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
                    "Éxito COBIT 2019: el archivo cumple criterios de Exactitud, Integridad y Consistencia."
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
                [html.Strong("Ajustes automáticos aplicados: "), html.Ul([html.Li(w) for w in warnings])],
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
