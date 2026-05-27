"""Motor analítico: drift, equidad, explicabilidad y cumplimiento."""
from __future__ import annotations
from typing import Any
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import confusion_matrix
from src.utils import (
    FAIRNESS_DP_MAX,
    FAIRNESS_DP_MIN,
    FAIRNESS_PPV_MAX_DIFF,
    FAIRNESS_TPR_MAX_DIFF,
    PSI_UMBRAL_CRITICO,
)


def calculate_psi(expected: np.ndarray, actual: np.ndarray, bins: int = 10) -> float:
    """Population Stability Index entre dos distribuciones."""
    expected = np.asarray(expected, dtype=float)
    actual = np.asarray(actual, dtype=float)
    breakpoints = np.linspace(
        min(expected.min(), actual.min()),
        max(expected.max(), actual.max()),
        bins + 1,
    )
    breakpoints[0] = -np.inf
    breakpoints[-1] = np.inf
    exp_perc, _ = np.histogram(expected, bins=breakpoints)
    act_perc, _ = np.histogram(actual, bins=breakpoints)
    exp_perc = np.where(exp_perc == 0, 0.0001, exp_perc / exp_perc.sum())
    act_perc = np.where(act_perc == 0, 0.0001, act_perc / act_perc.sum())
    psi = np.sum((act_perc - exp_perc) * np.log(act_perc / exp_perc))
    return float(psi)


def run_ks_test(reference: np.ndarray, current: np.ndarray) -> dict[str, Any]:
    statistic, p_value = stats.ks_2samp(reference, current)
    pasa = p_value >= 0.05
    return {
        "statistic": float(statistic),
        "p_value": float(p_value),
        "estado": "Pasa" if pasa else "Falla",
        "en_cumplimiento": pasa,
    }


def synthesize_drift_distributions(seed: int = 42) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    reference = rng.normal(loc=0.55, scale=0.12, size=5000)
    current = rng.normal(loc=0.62, scale=0.15, size=5000)
    return reference, current


def compute_drift_summary(drift_df: pd.DataFrame) -> dict[str, Any]:
    # FIX: manejar DataFrame vacío para evitar IndexError en .iloc[-1]
    if drift_df.empty:
        return {
            "psi_series": drift_df,
            "psi_latest": 0.0,
            "psi_calculated": 0.0,
            "ks_statistic": 0.0,
            "ks_pvalue": 1.0,
            "ks_estado": "Sin datos",
            "ks_computed": {"statistic": 0.0, "p_value": 1.0, "estado": "Sin datos", "en_cumplimiento": True},
            "severidad": "Baja",
            "reference": np.array([]),
            "current": np.array([]),
            "umbral_psi": PSI_UMBRAL_CRITICO,
        }

    latest = drift_df.iloc[-1]
    ref, cur = synthesize_drift_distributions()
    psi_calc = calculate_psi(ref, cur)
    ks = run_ks_test(ref, cur)
    severidad = str(latest.get("Alerta", "Baja"))
    return {
        "psi_series": drift_df,
        "psi_latest": float(latest["PSI"]),
        "psi_calculated": psi_calc,
        "ks_statistic": float(latest["KS_Statistic"]),
        "ks_pvalue": float(latest["KS_Pvalue"]),
        "ks_estado": "Pasa" if float(latest["KS_Pvalue"]) >= 0.05 else "Falla",
        "ks_computed": ks,
        "severidad": severidad,
        "reference": ref,
        "current": cur,
        "umbral_psi": PSI_UMBRAL_CRITICO,
    }


def compute_fairness_metrics(fairness_df: pd.DataFrame) -> dict[str, Any]:
    row = fairness_df.iloc[-1]
    paridad = float(row["Paridad_Demografica"])
    tpr_diff = abs(float(row["TPR_A"]) - float(row["TPR_B"]))
    ppv_diff = abs(float(row["PPV_A"]) - float(row["PPV_B"]))
    return {
        "grupo_a": row["Grupo_A"],
        "grupo_b": row["Grupo_B"],
        "paridad_demografica": paridad,
        "paridad_ok": FAIRNESS_DP_MIN <= paridad <= FAIRNESS_DP_MAX,
        "tpr_diff": tpr_diff,
        "tpr_ok": tpr_diff < FAIRNESS_TPR_MAX_DIFF,
        "ppv_diff": ppv_diff,
        "ppv_ok": ppv_diff < FAIRNESS_PPV_MAX_DIFF,
        "tpr_a": float(row["TPR_A"]),
        "tpr_b": float(row["TPR_B"]),
        "ppv_a": float(row["PPV_A"]),
        "ppv_b": float(row["PPV_B"]),
    }


def compute_fairness_from_labels(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    group: np.ndarray,
) -> dict[str, float]:
    """Métricas de equidad con scikit-learn (grupos binarios)."""
    groups = np.unique(group)
    if len(groups) != 2:
        raise ValueError("Se requieren exactamente dos grupos para el análisis de equidad.")
    rates: dict[str, float] = {}
    tpr_map: dict[str, float] = {}
    ppv_map: dict[str, float] = {}
    for g in groups:
        mask = group == g
        y_t = y_true[mask]
        y_p = y_pred[mask]
        rates[str(g)] = float(y_p.mean())
        tn, fp, fn, tp = confusion_matrix(y_t, y_p, labels=[0, 1]).ravel()
        tpr_map[str(g)] = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        ppv_map[str(g)] = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    g0, g1 = map(str, groups)
    paridad = rates[g0] / rates[g1] if rates[g1] > 0 else 0.0
    return {
        "paridad_demografica": paridad,
        "tpr_diff": abs(tpr_map[g0] - tpr_map[g1]),
        "ppv_diff": abs(ppv_map[g0] - ppv_map[g1]),
    }


def compute_shap_values(seed: int = 7) -> pd.DataFrame:
    """Valores SHAP promedio simulados para el modelo de demanda SIOP-DS."""
    rng = np.random.default_rng(seed)
    variables = [
        "temporada_operativa",
        "capacidad_asientos",
        "conectividad_regional",
        "historico_ocupacion",
        "precio_tarifa_social",
        "indice_vulnerabilidad",
        "distancia_km",
        "frecuencia_semanal",
    ]
    valores = rng.uniform(0.05, 0.35, len(variables))
    valores = valores / valores.sum()
    return pd.DataFrame({"variable": variables, "shap_mean": valores}).sort_values(
        "shap_mean", ascending=True
    )


def compute_bias_heatmap(seed: int = 11) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    variables = ["ruta", "temporada", "asientos", "tarifa", "region", "clima"]
    metricas = ["Sesgo medido", "Desviación", "Impacto"]
    data = rng.uniform(-0.4, 0.4, size=(len(variables), len(metricas)))
    return pd.DataFrame(data, index=variables, columns=metricas)


def compute_adversarial_resilience() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "ataque": [
                "FGSM",
                "PGD",
                "Evación de umbral",
                "Envenenamiento",
                "Membership Inference",
            ],
            "resiliencia_pct": [92.5, 88.0, 94.2, 86.5, 90.1],
        }
    )


def compute_compliance_radar() -> dict[str, float]:
    return {
        "ISO/IEC 42001": 0.82,
        "EU AI Act": 0.78,
        "CONPES 4058": 0.85,
        "UNESCO": 0.80,
        "NIST AI RMF": 0.83,
    }


def compute_governance_kpis(modelos_df: pd.DataFrame) -> dict[str, Any]:
    prod = modelos_df[modelos_df["Estado"] == "Producción"]
    total_prod = len(prod)
    doc_pct = modelos_df["Documentacion_Completa"].mean() if "Documentacion_Completa" in modelos_df else 0.75
    audit_pct = modelos_df["Auditoria_Vigente"].mean() if "Auditoria_Vigente" in modelos_df else 0.70
    radar = compute_compliance_radar()
    cumplimiento_global = float(np.mean(list(radar.values())))
    return {
        "total_produccion": total_prod,
        "pct_documentacion": float(doc_pct),
        "pct_auditoria": float(audit_pct),
        "pct_cumplimiento": cumplimiento_global,
    }


def compute_mlops_metrics(modelos_df: pd.DataFrame) -> dict[str, Any]:
    df = modelos_df.copy()
    df["mes"] = df["Fecha_Despliegue"].dt.to_period("M").astype(str)
    timeline = df.groupby("mes").size().reset_index(name="despliegues")
    fases = df["Fase"].value_counts().reindex(
        ["Desarrollo", "Staging", "Producción", "Deprecado"], fill_value=0
    )
    pipeline_exito = 0.94 if len(df) > 0 else 0.0
    return {"timeline": timeline, "fases": fases, "pipeline_exito": pipeline_exito}
