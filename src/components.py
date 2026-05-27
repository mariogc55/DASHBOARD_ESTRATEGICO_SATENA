"""Generadores de figuras Plotly y componentes visuales reutilizables."""
from __future__ import annotations
from typing import Any
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import dash_table, html
import dash_bootstrap_components as dbc
from src.utils import (
    SATENA_AZUL,
    SATENA_AZUL_OSCURO,
    SATENA_AMARILLO,
    SATENA_BLANCO,
    SATENA_ROJO,
    SATENA_VERDE,
    PSI_UMBRAL_CRITICO,
)


_KPI_ACCENT: dict[str, str] = {
    "primary": SATENA_AZUL,
    "success": SATENA_VERDE,
    "warning": SATENA_AMARILLO,
    "danger": SATENA_ROJO,
}


_KPI_BG: dict[str, str] = {
    "primary": "rgba(11, 61, 145, 0.04)",
    "success": "rgba(25, 135, 84, 0.05)",
    "warning": "rgba(255, 193, 7, 0.06)",
    "danger":  "rgba(220, 53, 69, 0.05)",
}


def kpi_card(
    title: str,
    value: str,
    subtitle: str = "",
    color: str = "primary",
    icon: str = "",
) -> dbc.Card:
    """Tarjeta de metrica reutilizable con acento de color lateral, icono y gradiente.

    Args:
        title:    Etiqueta superior (en mayusculas pequenas).
        value:    Valor principal grande.
        subtitle: Texto secundario o meta debajo del valor.
        color:    Acento -- "primary" | "success" | "warning" | "danger".
        icon:     Emoji o texto corto que precede al valor.
    """
    accent = _KPI_ACCENT.get(color, SATENA_AZUL)
    bg     = _KPI_BG.get(color, _KPI_BG["primary"])
    return dbc.Card(
        dbc.CardBody(
            [
                # Fila superior: etiqueta + punto de color
                html.Div(
                    [
                        html.Span(title, className="satena-kpi-label"),
                        html.Span(className="kpi-dot", style={"background": accent}),
                    ],
                    className="kpi-header-row",
                ),
                # Valor principal
                html.Div(
                    [
                        html.Span(icon + " ", className="kpi-icon") if icon else None,
                        html.Span(value, className="satena-kpi-value"),
                    ],
                    className="kpi-value-row",
                ),
                # Subtitulo chip
                html.Div(
                    html.Span(subtitle, className="kpi-subtitle-chip"),
                    className="kpi-footer-row",
                ) if subtitle else None,
            ]
        ),
        className="satena-card h-100 kpi-card",
        style={
            "borderLeft": f"4px solid {accent}",
            "background": f"linear-gradient(135deg, #ffffff 60%, {bg} 100%)",
        },
    )




def empty_state_card(
    title: str = "Sin datos cargados",
    message: str = "Use el boton 'Cargar Excel' en la barra superior para visualizar esta seccion.",
    height: int = 300,
) -> html.Div:
    """Componente de estado vacio que se muestra cuando no hay datos de sesion."""
    return html.Div(
        dbc.Card(
            dbc.CardBody(
                html.Div(
                    [
                        html.Div(className="empty-state-icon"),
                        html.H5(title, className="empty-state-title"),
                        html.P(message, className="empty-state-message"),
                    ],
                    className="empty-state-inner",
                )
            ),
            className="satena-card empty-state-card",
        ),
        style={"minHeight": f"{height}px", "display": "flex", "alignItems": "center", "width": "100%"},
    )


def no_data_kpi(title: str) -> dbc.Card:
    """KPI card vacio para cuando no hay datos de sesion."""
    return kpi_card(title, "--", "Sin datos")

def build_psi_timeline(drift_df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=drift_df["Fecha"],
            y=drift_df["PSI"],
            mode="lines+markers",
            name="PSI",
            line=dict(color=SATENA_AZUL, width=2),
        )
    )
    fig.add_hline(
        y=PSI_UMBRAL_CRITICO,
        line_dash="dash",
        line_color=SATENA_ROJO,
        annotation_text=f"Umbral critico ({PSI_UMBRAL_CRITICO})",
    )
    fig.update_layout(
        title="Evolucion temporal del PSI -- SIOP-DS",
        template="plotly_white",
        margin=dict(l=40, r=20, t=50, b=40),
        yaxis_title="PSI",
        xaxis_title="Fecha",
        height=380,
    )
    return fig


def build_histogram_comparison(reference: Any, current: Any) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(
        go.Histogram(
            x=reference,
            name="Entrenamiento",
            opacity=0.55,
            marker_color=SATENA_AZUL,
            nbinsx=40,
        )
    )
    fig.add_trace(
        go.Histogram(
            x=current,
            name="Tiempo real",
            opacity=0.55,
            marker_color=SATENA_AMARILLO,
            nbinsx=40,
        )
    )
    fig.update_layout(
        barmode="overlay",
        title="Distribucion: entrenamiento vs. produccion (SIOP-DS)",
        template="plotly_white",
        margin=dict(l=40, r=20, t=50, b=40),
        height=380,
        xaxis_title="Indice de demanda normalizado",
        yaxis_title="Frecuencia",
    )
    return fig


def build_shap_bar(shap_df: pd.DataFrame) -> go.Figure:
    fig = go.Figure(
        go.Bar(
            x=shap_df["shap_mean"],
            y=shap_df["variable"],
            orientation="h",
            marker_color=SATENA_AZUL,
        )
    )
    fig.update_layout(
        title="Importancia SHAP promedio -- Modelo de demanda",
        template="plotly_white",
        margin=dict(l=160, r=20, t=50, b=40),
        height=420,
        xaxis_title="|SHAP| promedio",
    )
    return fig


def build_gobierno_datos_bar(gobierno_df: pd.DataFrame, modelos_df: pd.DataFrame) -> go.Figure:
    merged = gobierno_df.merge(modelos_df[["ID", "Nombre"]], on="ID", how="left")
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            name="Volumen (miles)",
            x=merged["Nombre"],
            y=merged["Volumen_Procesado"] / 1000,
            marker_color=SATENA_AZUL,
        )
    )
    fig.add_trace(
        go.Bar(
            name="% Anonimizado",
            x=merged["Nombre"],
            y=merged["Pct_Anonimizado"] * 100,
            marker_color=SATENA_AZUL_OSCURO,
        )
    )
    fig.add_trace(
        go.Bar(
            name="% Linaje documentado",
            x=merged["Nombre"],
            y=merged["Pct_Linaje"] * 100,
            marker_color=SATENA_AMARILLO,
        )
    )
    fig.update_layout(
        barmode="group",
        title="Gobierno de Datos por modelo",
        template="plotly_white",
        height=400,
        yaxis_title="Valor",
    )
    return fig


def build_compliance_radar(radar_scores: dict[str, float]) -> go.Figure:
    labels = list(radar_scores.keys())
    values = [v * 100 for v in radar_scores.values()]
    values_closed = values + [values[0]]
    labels_closed = labels + [labels[0]]
    fig = go.Figure(
        go.Scatterpolar(
            r=values_closed,
            theta=labels_closed,
            fill="toself",
            fillcolor="rgba(11, 61, 145, 0.25)",
            line=dict(color=SATENA_AZUL, width=2),
            name="Madurez",
        )
    )
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        title="Cumplimiento normativo -- Madurez por marco",
        template="plotly_white",
        height=420,
        showlegend=False,
    )
    return fig


def build_mlops_timeline(timeline_df: pd.DataFrame) -> go.Figure:
    fig = px.line(
        timeline_df,
        x="mes",
        y="despliegues",
        markers=True,
        title="Linea de tiempo de despliegues mensuales",
    )
    fig.update_traces(line_color=SATENA_AZUL)
    fig.update_layout(template="plotly_white", height=360, xaxis_title="Mes", yaxis_title="Despliegues")
    return fig


def build_fases_bar(fases: pd.Series) -> go.Figure:
    color_map = {
        "Desarrollo": SATENA_AZUL,
        "Staging": SATENA_AMARILLO,
        "Produccion": SATENA_VERDE,
        "Deprecado": SATENA_ROJO,
    }
    colors = [color_map.get(str(fase), SATENA_AZUL) for fase in fases.index]
    fig = go.Figure(
        go.Bar(
            x=fases.index.astype(str),
            y=fases.values,
            marker_color=colors,
        )
    )
    fig.update_layout(
        title="Modelos por fase del ciclo de vida",
        template="plotly_white",
        height=360,
        yaxis_title="Cantidad",
    )
    return fig


def build_version_line(siop_df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=siop_df["Version"],
            y=siop_df["Accuracy"],
            mode="lines+markers",
            name="Accuracy",
            line=dict(color=SATENA_AZUL),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=siop_df["Version"],
            y=siop_df["F1_Score"],
            mode="lines+markers",
            name="F1-Score",
            line=dict(color=SATENA_AMARILLO),
        )
    )
    fig.update_layout(
        title="SIOP-DS -- Evolucion Accuracy y F1-Score",
        template="plotly_white",
        height=400,
        xaxis_title="Version",
        yaxis_title="Metrica",
    )
    return fig


def build_bias_heatmap(bias_df: pd.DataFrame) -> go.Figure:
    fig = go.Figure(
        data=go.Heatmap(
            z=bias_df.values,
            x=bias_df.columns.tolist(),
            y=bias_df.index.tolist(),
            colorscale="RdBu",
            zmid=0,
        )
    )
    fig.update_layout(
        title="Mapa de sesgos por variable operativa",
        template="plotly_white",
        height=400,
    )
    return fig


def build_adversarial_bar(adv_df: pd.DataFrame) -> go.Figure:
    fig = go.Figure(
        go.Bar(
            x=adv_df["ataque"],
            y=adv_df["resiliencia_pct"],
            marker_color=SATENA_AZUL,
            text=adv_df["resiliencia_pct"].round(1),
            textposition="outside",
        )
    )
    fig.update_layout(
        title="Resiliencia ante ataques adversariales simulados (%)",
        template="plotly_white",
        height=380,
        yaxis=dict(range=[0, 100]),
    )
    return fig


def build_attack_timeline(seguridad_df: pd.DataFrame) -> go.Figure:
    df = seguridad_df.copy()
    df["mitigados"] = (df["Estado"] == "Mitigado").astype(int)
    agg = df.groupby("Fecha", as_index=False)["mitigados"].sum()
    fig = px.area(
        agg,
        x="Fecha",
        y="mitigados",
        title="Vectores de ataque mitigados en el tiempo",
    )
    fig.update_traces(fillcolor="rgba(11, 61, 145, 0.35)", line_color=SATENA_AZUL)
    fig.update_layout(template="plotly_white", height=360, yaxis_title="Incidentes mitigados")
    return fig


def build_model_inventory_table(modelos_df: pd.DataFrame) -> dash_table.DataTable:
    display = modelos_df[
        ["ID", "Nombre", "Version", "Propietario", "Estado", "EU_AI_Act"]
    ].copy()
    style_data_conditional = [
        {
            "if": {
                "filter_query": '{Nombre} = "SIOP-DS" && {EU_AI_Act} = "Alto Riesgo"',
            },
            "className": "datatable-siop-alto-riesgo",
        }
    ]
    return dash_table.DataTable(
        columns=[{"name": c.replace("_", " "), "id": c} for c in display.columns],
        data=display.to_dict("records"),
        page_size=8,
        style_table={"overflowX": "auto"},
        style_header={
            "backgroundColor": SATENA_AZUL,
            "color": SATENA_BLANCO,
            "fontWeight": "bold",
        },
        style_cell={"textAlign": "left", "padding": "8px"},
        style_data_conditional=style_data_conditional,
    )


def build_audit_log_table(auditoria_df: pd.DataFrame) -> dash_table.DataTable:
    return dash_table.DataTable(
        columns=[{"name": c, "id": c} for c in auditoria_df.columns],
        data=auditoria_df.to_dict("records"),
        page_size=6,
        style_table={"overflowX": "auto"},
        style_header={"backgroundColor": SATENA_AZUL_OSCURO, "color": SATENA_BLANCO},
        style_cell={"textAlign": "left", "padding": "8px", "whiteSpace": "normal", "height": "auto"},
    )


def build_incidents_table(seguridad_df: pd.DataFrame) -> dash_table.DataTable:
    display = seguridad_df.copy()
    display["Fecha"] = display["Fecha"].dt.strftime("%Y-%m-%d")
    return dash_table.DataTable(
        columns=[{"name": c.replace("_", " "), "id": c} for c in display.columns],
        data=display.to_dict("records"),
        page_size=6,
        style_table={"overflowX": "auto"},
        style_header={"backgroundColor": SATENA_AZUL, "color": SATENA_BLANCO},
        style_cell={"textAlign": "left", "padding": "8px"},
    )


def alert_card(severidad: str, mensaje: str) -> dbc.Card:
    css = {
        "Crítica": "alert-card-critica",
        "Media": "alert-card-media",
        "Baja": "alert-card-baja",
    }.get(severidad, "alert-card-media")
    color = {
        "Crítica": SATENA_ROJO,
        "Media": SATENA_AMARILLO,
        "Baja": SATENA_VERDE,
    }.get(severidad, SATENA_AMARILLO)
    return dbc.Card(
        dbc.CardBody(
            [
                html.H6(f"Alerta de degradación -- {severidad}", style={"color": color}),
                html.P(mensaje, className="mb-0"),
            ]
        ),
        className=f"satena-card mb-2 {css}",
    )


def semaforo_card(titulo: str, valor: str, ok: bool) -> dbc.Card:
    return dbc.Card(
        dbc.CardBody(
            [
                html.H6(titulo, className="mb-2"),
                html.H4(valor, className="mb-0"),
                html.Small("En cumplimiento" if ok else "Fuera de umbral", className="mt-2 d-block"),
            ]
        ),
        className="satena-card h-100 " + ("semaforo-verde" if ok else "semaforo-rojo"),
    )
