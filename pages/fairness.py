"""Tab 5: Auditoría y fairness — Fase 7 plan estratégico."""
from __future__ import annotations
import dash_bootstrap_components as dbc
# FIX: no_update importado al nivel del módulo
from dash import Input, Output, no_update, html
from src.analytics import compute_fairness_metrics
from src.components import build_audit_log_table, empty_state_card, semaforo_card
from src.data_manager import DataManager


def layout() -> dbc.Container:
    return dbc.Container(
        [
            html.H5("Auditoría y Fairness — Fase 7", className="satena-section-title"),
            html.P(
                "Métricas Harvard: Paridad Demográfica, Igualdad de Oportunidades (TPR), "
                "Paridad de Error de Predicción (PPV). Rutas Sociales vs. Troncales.",
                className="text-muted",
            ),
            dbc.Row(
                [
                    dbc.Col(html.Div(id="fairness-semaforo-dp"), md=4, className="mb-3"),
                    dbc.Col(html.Div(id="fairness-semaforo-tpr"), md=4, className="mb-3"),
                    dbc.Col(html.Div(id="fairness-semaforo-ppv"), md=4, className="mb-3"),
                ]
            ),
            html.H6("Log de auditoría inmutable (Human-in-the-Loop)", className="mt-3 mb-2"),
            html.Div(id="fairness-audit-table"),
        ],
        fluid=True,
        className="px-0",
    )


def register_callbacks(app, dm: DataManager) -> None:
    @app.callback(
        Output("fairness-semaforo-dp", "children"),
        Output("fairness-semaforo-tpr", "children"),
        Output("fairness-semaforo-ppv", "children"),
        Output("fairness-audit-table", "children"),
        Input("auth-store", "data"),
        Input("session-data-store", "data"),
        Input("main-tabs", "active_tab"),
        prevent_initial_call=False,
    )
    def load_fairness(auth_data, session_data, active_tab):
        if not auth_data or not auth_data.get("authenticated"):
            return tuple([dbc.Alert("Acceso restringido", color="warning")] * 4)
        if not session_data:
            es = empty_state_card("Sin datos de fairness", "Cargue un archivo Excel para ver metricas de equidad y log de auditoria.", 200)
            return es, es, es, es
        if active_tab != "tab-fairness":
            return (no_update,) * 4

        fairness_df = dm.get_fairness(session_data)

        # FIX: manejar DataFrame vacío antes de .iloc[-1] en compute_fairness_metrics
        if fairness_df.empty:
            msg = dbc.Alert("No hay datos de fairness para el modelo seleccionado.", color="warning")
            return msg, msg, msg, msg

        metrics = compute_fairness_metrics(fairness_df)

        # FIX: eliminado bloque sklearn_check — código muerto que no se mostraba en UI
        # (compute_fairness_from_labels con datos random no aportaba información real)

        auditoria = dm.get_auditoria(session_data)
        return (
            semaforo_card(
                "Paridad Demográfica",
                f"{metrics['paridad_demografica']:.3f}",
                metrics["paridad_ok"],
            ),
            semaforo_card(
                "Igualdad de Oportunidades (|ΔTPR|)",
                f"{metrics['tpr_diff'] * 100:.2f}%",
                metrics["tpr_ok"],
            ),
            semaforo_card(
                "Paridad Error Predicción (|ΔPPV|)",
                f"{metrics['ppv_diff'] * 100:.2f}%",
                metrics["ppv_ok"],
            ),
            build_audit_log_table(auditoria),
        )
