"""
Validación y saneamiento de libros Excel para el dashboard de gobernanza IA.
"""
from __future__ import annotations
import io
from dataclasses import dataclass, field
from typing import Any
import pandas as pd

# FIX 1: gobierno_datos es una hoja válida y opcional — el validador ya no la rechaza como "sobrante"
REQUIRED_SHEETS: frozenset[str] = frozenset(
    {"modelos", "drift", "fairness", "auditoria", "seguridad"}
)

SHEET_COLUMNS: dict[str, tuple[str, ...]] = {
    "modelos": (
        "ID",
        "Nombre",
        "Version",
        "Fecha_Despliegue",
        "Propietario",
        "Estado",
        "Nivel_Riesgo",
        "Accuracy",
        "F1_Score",
    ),
    "drift": ("ID_Modelo", "Fecha", "PSI", "KS_Statistic", "KS_Pvalue", "Alerta"),
    "fairness": (
        "ID_Modelo",
        "Fecha",
        "Grupo_A",
        "Grupo_B",
        "Paridad_Demografica",
        "TPR_A",
        "TPR_B",
        "PPV_A",
        "PPV_B",
    ),
    "auditoria": (
        "ID_Log",
        "ID_Modelo",
        "Timestamp",
        "Variables_Entrada",
        "Prediccion",
        "Operador",
        "Accion_Final",
    ),
    "seguridad": (
        "ID_Incidente",
        "Fecha",
        "Tipo",
        "Severidad",
        "Estado",
        "Tiempo_Resolucion",
    ),
}

NUMERIC_BY_SHEET: dict[str, tuple[str, ...]] = {
    "modelos": ("Accuracy", "F1_Score"),
    "drift": ("PSI", "KS_Statistic", "KS_Pvalue"),
    "fairness": ("Paridad_Demografica", "TPR_A", "TPR_B", "PPV_A", "PPV_B"),
    "auditoria": (),
    "seguridad": ("Tiempo_Resolucion",),
}

DATETIME_BY_SHEET: dict[str, tuple[str, ...]] = {
    "modelos": ("Fecha_Despliegue",),
    "drift": ("Fecha",),
    "fairness": ("Fecha",),
    "auditoria": ("Timestamp",),
    "seguridad": ("Fecha",),
}

COLUMN_ALIASES: dict[str, dict[str, str]] = {
    "modelos": {
        # FIX 2: mapear ID_Modelo → ID para la hoja modelos.
        # El script generar_datos.py genera la columna como "ID_Modelo" en lugar de "ID".
        "id_modelo": "ID",
        "id modelo": "ID",
        "idmodelo": "ID",
        "id": "ID",
        "fecha despliegue": "Fecha_Despliegue",
        "fecha_despliegue": "Fecha_Despliegue",
    },
    "drift": {
        "idmodelo": "ID_Modelo",
        "id_modelo": "ID_Modelo",
        "id modelo": "ID_Modelo",
        "psi": "PSI",
        "ks_statistic": "KS_Statistic",
        "ks pvalue": "KS_Pvalue",
    },
    "fairness": {
        "idmodelo": "ID_Modelo",
        "id_modelo": "ID_Modelo",
        "id modelo": "ID_Modelo",
        "paridaddemografica": "Paridad_Demografica",
        "paridad_demografica": "Paridad_Demografica",
        "tpr a": "TPR_A",
        "tpr b": "TPR_B",
        "ppv a": "PPV_A",
        "ppv b": "PPV_B",
    },
    "auditoria": {
        "idlog": "ID_Log",
        "id_log": "ID_Log",
        "id modelo": "ID_Modelo",
        "idmodelo": "ID_Modelo",
        "id_modelo": "ID_Modelo",
    },
    "seguridad": {
        "idincidente": "ID_Incidente",
        "id_incidente": "ID_Incidente",
    },
}

CRITICAL_ID_COLUMNS: dict[str, tuple[str, ...]] = {
    "drift": ("ID_Modelo",),
    "fairness": ("ID_Modelo",),
    "auditoria": ("ID_Log", "ID_Modelo"),
    "seguridad": ("ID_Incidente",),
}


@dataclass
class ValidationOutcome:
    ok: bool
    frames: dict[str, pd.DataFrame] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def _strip_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    return df


def normalizar_consistencia_columnas(sheet: str, df: pd.DataFrame, warnings: list[str]) -> pd.DataFrame:
    df = _strip_columns(df)
    alias_map = COLUMN_ALIASES.get(sheet, {})
    new_cols: list[str] = []
    changed = False
    for col in df.columns:
        key = str(col).strip().lower().replace(" ", "_")
        canonical = alias_map.get(key)
        if canonical and canonical != col:
            new_cols.append(canonical)
            changed = True
        else:
            new_cols.append(str(col))
    if changed:
        warnings.append(
            f"Hoja '{sheet}': se normalizaron nombres de columnas para cumplir Consistencia COBIT."
        )
        df.columns = new_cols
    return df


def validar_integridad_cobit(sheet: str, df: pd.DataFrame) -> list[str]:
    errores: list[str] = []
    crit_cols = CRITICAL_ID_COLUMNS.get(sheet, ())
    for col in crit_cols:
        if col not in df.columns:
            continue
        serie = df[col]
        if serie.dtype == object:
            serie_eval = serie.astype(str).str.strip()
            mask_null = serie_eval.eq("") | serie_eval.isna()
        else:
            mask_null = serie.isna()
        if mask_null.any():
            errores.append(
                f"Error de Integridad COBIT: columna obligatoria {col} en hoja '{sheet}' contiene "
                f"{int(mask_null.sum())} valor(es) nulo(s) o vacío(s)."
            )
    return errores


def _map_sheet_names(sheet_names: list[str]) -> dict[str, str]:
    """Mapea nombre canónico (minúsculas) -> nombre real en el libro."""
    mapping: dict[str, str] = {}
    for raw in sheet_names:
        key = str(raw).strip().lower()
        if key in REQUIRED_SHEETS:
            mapping[key] = raw
    return mapping


def validate_excel_bytes(data: bytes, filename: str = "") -> ValidationOutcome:
    """
    Valida un .xlsx en memoria.
    - Debe tener las 5 hojas requeridas (puede tener hojas adicionales como gobierno_datos).
    - Columnas obligatorias por hoja; se corrigen espacios en nombres y tipos cuando es posible.
    """
    warnings: list[str] = []
    errors: list[str] = []

    if not data:
        return ValidationOutcome(ok=False, errors=["El archivo está vacío o no se pudo leer."])

    try:
        xl = pd.ExcelFile(io.BytesIO(data), engine="openpyxl")
    except Exception as exc:  # noqa: BLE001
        return ValidationOutcome(
            ok=False,
            errors=[f"No se pudo abrir el Excel (archivo corrupto o no es .xlsx): {exc}"],
        )

    raw_names = list(xl.sheet_names)
    lowered = {str(n).strip().lower() for n in raw_names}

    if len(raw_names) != len(lowered):
        return ValidationOutcome(
            ok=False,
            errors=["El libro contiene nombres de hoja duplicados (ignorando mayúsculas)."],
        )

    # FIX 1: validar que las 5 hojas REQUERIDAS estén presentes.
    # Hojas adicionales (como gobierno_datos) se ignoran sin error.
    missing = sorted(REQUIRED_SHEETS - lowered)
    if missing:
        return ValidationOutcome(
            ok=False,
            errors=[
                "El libro debe contener las 5 hojas requeridas: "
                + ", ".join(sorted(REQUIRED_SHEETS))
                + " (nombres en minúsculas o equivalentes sin distinguir mayúsculas)."
                + f" Hojas faltantes: {', '.join(missing)}."
            ],
        )

    # Hojas extra permitidas (gobierno_datos y cualquier otra) — solo avisar, no bloquear
    extra = sorted(lowered - REQUIRED_SHEETS)
    if extra:
        warnings.append(
            f"Hojas adicionales ignoradas por el validador COBIT (no son un error): {', '.join(extra)}."
        )

    name_map = _map_sheet_names(raw_names)
    if set(name_map.keys()) != REQUIRED_SHEETS:
        return ValidationOutcome(ok=False, errors=["No se pudo mapear correctamente las hojas requeridas."])

    frames: dict[str, pd.DataFrame] = {}
    for canonical, real_name in name_map.items():
        try:
            df = pd.read_excel(xl, sheet_name=real_name, engine="openpyxl")
        except Exception as exc:  # noqa: BLE001
            return ValidationOutcome(
                ok=False,
                errors=[f"Error de Consistencia COBIT: no se pudo leer la hoja '{real_name}': {exc}"],
            )

        df = normalizar_consistencia_columnas(canonical, df, warnings)

        required = SHEET_COLUMNS[canonical]
        missing_cols = [c for c in required if c not in df.columns]
        if missing_cols:
            return ValidationOutcome(
                ok=False,
                errors=[
                    "Error de Integridad COBIT: faltan columnas obligatorias en hoja "
                    f"'{canonical}': {', '.join(missing_cols)}."
                ],
            )

        df = df.loc[:, list(required)].copy()

        # Exactitud: tipos numéricos correctos
        for col in NUMERIC_BY_SHEET.get(canonical, ()):
            original = df[col].copy()
            df[col] = pd.to_numeric(df[col], errors="coerce")
            if df[col].isna().any() and not original.isna().all():
                bad = int(df[col].isna().sum())
                return ValidationOutcome(
                    ok=False,
                    errors=[
                        "Error de Exactitud COBIT: hoja "
                        f"'{canonical}', columna '{col}' contiene {bad} valores que no se "
                        "pueden interpretar estrictamente como numéricos."
                    ],
                )
            if df[col].isna().all() and len(df) > 0:
                return ValidationOutcome(
                    ok=False,
                    errors=[
                        "Error de Exactitud COBIT: hoja "
                        f"'{canonical}', columna '{col}' tiene todos los valores inválidos."
                    ],
                )

        for col in DATETIME_BY_SHEET.get(canonical, ()):
            parsed = pd.to_datetime(df[col], errors="coerce")
            if parsed.isna().any() and len(df) > 0:
                warnings.append(
                    f"Hoja '{canonical}', columna '{col}': algunas fechas no parsearon; se conservarán como NaT."
                )
            df[col] = parsed

        if canonical == "drift":
            if df["Alerta"].dtype == object:
                df["Alerta"] = df["Alerta"].astype(str).str.strip()

        if len(df) == 0:
            return ValidationOutcome(
                ok=False,
                errors=[
                    f"Error de Integridad COBIT: la hoja '{canonical}' debe contener al menos una fila de datos."
                ],
            )

        integrity_errors = validar_integridad_cobit(canonical, df)
        if integrity_errors:
            return ValidationOutcome(ok=False, errors=integrity_errors)

        frames[canonical] = df

    return ValidationOutcome(ok=True, frames=frames, warnings=warnings)


def frames_to_session_payload(frames: dict[str, pd.DataFrame], filename: str, warnings: list[str]) -> dict[str, Any]:
    """Serializa DataFrames validados a un dict almacenable en dcc.Store (JSON-serializable)."""
    sheets: dict[str, list[dict[str, Any]]] = {}
    for name, df in frames.items():
        clean = df.copy()
        for col in clean.columns:
            if pd.api.types.is_datetime64_any_dtype(clean[col]):
                clean[col] = clean[col].dt.strftime("%Y-%m-%dT%H:%M:%S")
        records = clean.to_dict(orient="records")
        sheets[name] = records
    return {
        "valid": True,
        "filename": filename or "carga.xlsx",
        "warnings": warnings,
        "sheets": sheets,
    }