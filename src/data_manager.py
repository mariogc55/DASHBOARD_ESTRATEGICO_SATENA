"""Gestión de datos: archivo local por defecto o conjuntos validados desde sesión."""
from __future__ import annotations
import shutil
from datetime import datetime, timedelta
from functools import lru_cache
from pathlib import Path
from typing import Any
import numpy as np
import pandas as pd
from src.utils import DATA_DIR, ensure_directories
from src.validator import (
    DATETIME_BY_SHEET,
    NUMERIC_BY_SHEET,
    REQUIRED_SHEETS,
    frames_to_session_payload,
    validate_excel_bytes,
)

DEFAULT_WORKBOOK_PATH = DATA_DIR / "datos_gobernadia.xlsx"
LEGACY_WORKBOOK_PATH = DATA_DIR / "satena_ia_governance.xlsx"


def rehydrate_frames_from_store(sheets: dict[str, list[dict[str, Any]]]) -> dict[str, pd.DataFrame]:
    """Reconstruye DataFrames desde el payload JSON del Store."""
    out: dict[str, pd.DataFrame] = {}
    for name in sorted(REQUIRED_SHEETS):
        records = sheets.get(name)
        if not records:
            out[name] = pd.DataFrame()
            continue
        df = pd.DataFrame(records)
        for col in DATETIME_BY_SHEET.get(name, ()):
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")
        for col in NUMERIC_BY_SHEET.get(name, ()):
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        out[name] = df
    return out


def parse_upload_to_session_payload(
    contents: str | None, filename: str | None
) -> tuple[dict[str, Any] | None, list[str], list[str]]:
    """
    Decodifica dcc.Upload, valida y devuelve (payload_store | None, warnings, errors).
    """
    if contents is None:
        return None, [], []
    import base64
    import io as _io
    try:
        header, b64data = contents.split(",", 1)
        raw = base64.b64decode(b64data)
    except Exception as exc:  # noqa: BLE001
        return None, [], [f"No se pudo decodificar el archivo: {exc}"]
    if not filename or not str(filename).lower().endswith(".xlsx"):
        return None, [], ["Solo se admiten archivos con extensión .xlsx."]

    outcome = validate_excel_bytes(raw, filename=str(filename))
    if not outcome.ok:
        return None, outcome.warnings, outcome.errors

    payload = frames_to_session_payload(outcome.frames, str(filename), outcome.warnings)

    # FIX: capturar hojas extra (como gobierno_datos) que el validador ignora
    # pero que el dashboard sí puede usar si están presentes.
    try:
        xl_extra = pd.ExcelFile(_io.BytesIO(raw), engine="openpyxl")
        extra_sheets = {"gobierno_datos"}
        for sheet_name in xl_extra.sheet_names:
            key = str(sheet_name).strip().lower()
            if key in extra_sheets:
                df_extra = pd.read_excel(xl_extra, sheet_name=sheet_name, engine="openpyxl")
                for col in df_extra.columns:
                    if pd.api.types.is_datetime64_any_dtype(df_extra[col]):
                        df_extra[col] = df_extra[col].dt.strftime("%Y-%m-%dT%H:%M:%S")
                payload["sheets"][key] = df_extra.to_dict(orient="records")
    except Exception:  # noqa: BLE001 — hoja extra es opcional, no bloquear
        pass

    return payload, outcome.warnings, []


def _first_model_id(df: pd.DataFrame) -> str | None:
    """Retorna el primer ID_Modelo disponible en un DataFrame, o None si está vacío."""
    if df.empty or "ID_Modelo" not in df.columns:
        return None
    return str(df["ID_Modelo"].iloc[0])


class DataManager:
    """Proveedor centralizado: disco (lazy) o datos de sesión validados."""

    def __init__(self, workbook_path: Path | None = None) -> None:
        self.workbook_path = workbook_path or DEFAULT_WORKBOOK_PATH
        ensure_directories()
        self._ensure_default_workbook()

    def _ensure_default_workbook(self) -> None:
        if self.workbook_path.exists():
            return
        if LEGACY_WORKBOOK_PATH.exists():
            shutil.copy2(LEGACY_WORKBOOK_PATH, self.workbook_path)
            return
        self._generate_seed_workbook()

    def _session_frames(self, session_data: dict[str, Any] | None) -> dict[str, pd.DataFrame] | None:
        if not session_data or not session_data.get("valid"):
            return None
        sheets = session_data.get("sheets")
        if not isinstance(sheets, dict):
            return None
        return rehydrate_frames_from_store(sheets)

    def _generate_seed_workbook(self) -> None:
        rng = np.random.default_rng(42)
        modelos = pd.DataFrame(
            [
                {
                    "ID": "MDL-001",
                    "Nombre": "SIOP-DS",
                    "Version": "3.2.1",
                    "Fecha_Despliegue": "2025-11-15",
                    "Propietario": "Oficina IA Operaciones",
                    "Estado": "Producción",
                    "Nivel_Riesgo": "Alto",
                    "Accuracy": 0.912,
                    "F1_Score": 0.887,
                    "EU_AI_Act": "Alto Riesgo",
                    "Documentacion_Completa": True,
                    "Auditoria_Vigente": True,
                    "Fase": "Producción",
                },
                {
                    "ID": "MDL-002",
                    "Nombre": "SAT-Fuel-Opt",
                    "Version": "1.4.0",
                    "Fecha_Despliegue": "2025-08-02",
                    "Propietario": "Mantenimiento",
                    "Estado": "Producción",
                    "Nivel_Riesgo": "Limitado",
                    "Accuracy": 0.864,
                    "F1_Score": 0.831,
                    "EU_AI_Act": "Riesgo Limitado",
                    "Documentacion_Completa": True,
                    "Auditoria_Vigente": True,
                    "Fase": "Producción",
                },
                {
                    "ID": "MDL-003",
                    "Nombre": "Crew-Roster-AI",
                    "Version": "2.0.3",
                    "Fecha_Despliegue": "2025-09-20",
                    "Propietario": "RRHH Operaciones",
                    "Estado": "Staging",
                    "Nivel_Riesgo": "Limitado",
                    "Accuracy": 0.801,
                    "F1_Score": 0.776,
                    "EU_AI_Act": "Riesgo Limitado",
                    "Documentacion_Completa": False,
                    "Auditoria_Vigente": True,
                    "Fase": "Staging",
                },
                {
                    "ID": "MDL-004",
                    "Nombre": "Baggage-Forecast",
                    "Version": "0.9.8",
                    "Fecha_Despliegue": "2025-06-10",
                    "Propietario": "Aeropuertos",
                    "Estado": "Desarrollo",
                    "Nivel_Riesgo": "Mínimo",
                    "Accuracy": 0.742,
                    "F1_Score": 0.701,
                    "EU_AI_Act": "Riesgo Mínimo",
                    "Documentacion_Completa": False,
                    "Auditoria_Vigente": False,
                    "Fase": "Desarrollo",
                },
                {
                    "ID": "MDL-005",
                    "Nombre": "Route-Demand-Legacy",
                    "Version": "1.1.0",
                    "Fecha_Despliegue": "2024-03-01",
                    "Propietario": "Planificación",
                    "Estado": "Deprecado",
                    "Nivel_Riesgo": "Limitado",
                    "Accuracy": 0.689,
                    "F1_Score": 0.655,
                    "EU_AI_Act": "Riesgo Limitado",
                    "Documentacion_Completa": True,
                    "Auditoria_Vigente": False,
                    "Fase": "Deprecado",
                },
                {
                    "ID": "MDL-006",
                    "Nombre": "SIOP-DS",
                    "Version": "3.1.0",
                    "Fecha_Despliegue": "2025-07-01",
                    "Propietario": "Oficina IA Operaciones",
                    "Estado": "Deprecado",
                    "Nivel_Riesgo": "Alto",
                    "Accuracy": 0.898,
                    "F1_Score": 0.871,
                    "EU_AI_Act": "Alto Riesgo",
                    "Documentacion_Completa": True,
                    "Auditoria_Vigente": False,
                    "Fase": "Deprecado",
                },
                {
                    "ID": "MDL-007",
                    "Nombre": "SIOP-DS",
                    "Version": "3.0.5",
                    "Fecha_Despliegue": "2025-03-15",
                    "Propietario": "Oficina IA Operaciones",
                    "Estado": "Deprecado",
                    "Nivel_Riesgo": "Alto",
                    "Accuracy": 0.881,
                    "F1_Score": 0.859,
                    "EU_AI_Act": "Alto Riesgo",
                    "Documentacion_Completa": True,
                    "Auditoria_Vigente": False,
                    "Fase": "Deprecado",
                },
            ]
        )
        fechas = pd.date_range(end=datetime.today(), periods=90, freq="D")
        drift_rows: list[dict[str, Any]] = []
        psi_base = 0.08
        for i, fecha in enumerate(fechas):
            psi = psi_base + (i / len(fechas)) * 0.22 + rng.normal(0, 0.015)
            ks_stat = 0.05 + (i / len(fechas)) * 0.12 + rng.normal(0, 0.01)
            ks_p = max(0.001, 0.25 - (i / len(fechas)) * 0.2 + rng.normal(0, 0.02))
            alerta = "Crítica" if psi >= 0.25 else ("Media" if psi >= 0.15 else "Baja")
            drift_rows.append(
                {
                    "ID_Modelo": "MDL-001",
                    "Fecha": fecha.strftime("%Y-%m-%d"),
                    "PSI": round(float(psi), 4),
                    "KS_Statistic": round(float(ks_stat), 4),
                    "KS_Pvalue": round(float(ks_p), 4),
                    "Alerta": alerta,
                }
            )
        drift = pd.DataFrame(drift_rows)
        fairness = pd.DataFrame(
            [
                {
                    "ID_Modelo": "MDL-001",
                    "Fecha": datetime.today().strftime("%Y-%m-%d"),
                    "Grupo_A": "Rutas Sociales",
                    "Grupo_B": "Rutas Troncales",
                    "Paridad_Demografica": 0.94,
                    "TPR_A": 0.86,
                    "TPR_B": 0.89,
                    "PPV_A": 0.84,
                    "PPV_B": 0.87,
                }
            ]
        )
        auditoria = pd.DataFrame(
            [
                {
                    "ID_Log": "LOG-1001",
                    "ID_Modelo": "MDL-001",
                    "Timestamp": (datetime.now() - timedelta(hours=5)).isoformat(),
                    "Variables_Entrada": "ruta=Bogotá-Quibdó; temporada=alta; asientos=34",
                    "Prediccion": "demanda=0.78",
                    "Operador": "coord.operaciones@satena.gov.co",
                    "Accion_Final": "Aprobada",
                },
                {
                    "ID_Log": "LOG-1002",
                    "ID_Modelo": "MDL-001",
                    "Timestamp": (datetime.now() - timedelta(hours=3)).isoformat(),
                    "Variables_Entrada": "ruta=Medellín-Apartadó; temporada=media; asientos=28",
                    "Prediccion": "demanda=0.62",
                    "Operador": "analista.demanda@satena.gov.co",
                    "Accion_Final": "Revisión Humana",
                },
                {
                    "ID_Log": "LOG-1003",
                    "ID_Modelo": "MDL-001",
                    "Timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
                    "Variables_Entrada": "ruta=Bogotá-Leticia; temporada=baja; asientos=52",
                    "Prediccion": "demanda=0.41",
                    "Operador": "supervisor.ia@satena.gov.co",
                    "Accion_Final": "Rechazada",
                },
            ]
        )
        seguridad = pd.DataFrame(
            [
                {
                    "ID_Incidente": "INC-501",
                    "Fecha": (datetime.today() - timedelta(days=12)).strftime("%Y-%m-%d"),
                    "Tipo": "Intento de inyección en API MLOps",
                    "Severidad": "Alta",
                    "Estado": "Mitigado",
                    "Tiempo_Resolucion": 4.5,
                },
                {
                    "ID_Incidente": "INC-502",
                    "Fecha": (datetime.today() - timedelta(days=7)).strftime("%Y-%m-%d"),
                    "Tipo": "Escaneo de puertos en endpoint drift",
                    "Severidad": "Media",
                    "Estado": "Mitigado",
                    "Tiempo_Resolucion": 2.0,
                },
                {
                    "ID_Incidente": "INC-503",
                    "Fecha": (datetime.today() - timedelta(days=2)).strftime("%Y-%m-%d"),
                    "Tipo": "Credencial débil detectada en staging",
                    "Severidad": "Baja",
                    "Estado": "En investigación",
                    "Tiempo_Resolucion": 0.0,
                },
            ]
        )
        with pd.ExcelWriter(self.workbook_path, engine="openpyxl") as writer:
            modelos.drop(
                columns=["EU_AI_Act", "Documentacion_Completa", "Auditoria_Vigente", "Fase"]
            ).to_excel(writer, sheet_name="modelos", index=False)
            drift.to_excel(writer, sheet_name="drift", index=False)
            fairness.to_excel(writer, sheet_name="fairness", index=False)
            auditoria.to_excel(writer, sheet_name="auditoria", index=False)
            seguridad.to_excel(writer, sheet_name="seguridad", index=False)

        meta_path = DATA_DIR / "modelos_meta.csv"
        modelos.to_csv(meta_path, index=False)

    @lru_cache(maxsize=16)
    def _read_sheet(self, sheet_name: str) -> pd.DataFrame:
        return pd.read_excel(self.workbook_path, sheet_name=sheet_name, engine="openpyxl")

    def _synthesize_gobierno_datos(self, modelos: pd.DataFrame) -> pd.DataFrame:
        rng = np.random.default_rng(123)
        # FIX: usar la columna ID correcta — puede ser "ID" (datos seed) o ya normalizada
        id_values = modelos["ID"].values if "ID" in modelos.columns else modelos.index.astype(str).values
        return pd.DataFrame(
            {
                "ID": id_values,
                "Volumen_Procesado": rng.integers(50_000, 900_000, len(modelos)),
                "Pct_Anonimizado": np.clip(rng.uniform(0.75, 0.99, len(modelos)), 0, 1),
                "Pct_Linaje": np.clip(rng.uniform(0.6, 0.95, len(modelos)), 0, 1),
            }
        )

    def get_modelos(self, session_data: dict[str, Any] | None = None) -> pd.DataFrame:
        sess = self._session_frames(session_data)
        if sess is not None:
            df = sess["modelos"].copy()
        else:
            df = self._read_sheet("modelos").copy()
        meta_cols = ("EU_AI_Act", "Documentacion_Completa", "Auditoria_Vigente", "Fase")
        if all(c in df.columns for c in meta_cols):
            pass
        else:
            meta_path = DATA_DIR / "modelos_meta.csv"
            if meta_path.exists() and sess is None:
                meta = pd.read_csv(meta_path)
                extra_cols = [c for c in meta_cols if c in meta.columns]
                merge_cols = ["ID", "Nombre", "Version"]
                if extra_cols and all(c in meta.columns for c in merge_cols):
                    df = df.merge(
                        meta[merge_cols + extra_cols].drop_duplicates(subset=merge_cols),
                        on=merge_cols,
                        how="left",
                    )
            if not all(c in df.columns for c in meta_cols):
                df = df.assign(
                    EU_AI_Act=np.where(
                        df["Nivel_Riesgo"].astype(str).str.contains("Alto", case=False),
                        "Alto Riesgo",
                        "Riesgo Limitado",
                    ),
                    Documentacion_Completa=pd.to_numeric(df["Accuracy"], errors="coerce") > 0.8,
                    Auditoria_Vigente=df["Estado"] == "Producción",
                    Fase=df["Estado"],
                )
        df["Fecha_Despliegue"] = pd.to_datetime(df["Fecha_Despliegue"])
        return df

    def get_drift(self, session_data: dict[str, Any] | None = None, model_id: str = "MDL-001") -> pd.DataFrame:
        sess = self._session_frames(session_data)
        if sess is not None:
            df = sess["drift"].copy()
        else:
            df = self._read_sheet("drift").copy()

        # FIX: fallback tolerante — si el model_id exacto no existe, usar el primer ID disponible.
        # Evita DataFrame vacío cuando el Excel cargado usa IDs distintos (ej. MOD-SIOP-01).
        if model_id and "ID_Modelo" in df.columns:
            if model_id in df["ID_Modelo"].values:
                df = df[df["ID_Modelo"] == model_id].copy()
            elif not df.empty:
                fallback_id = str(df["ID_Modelo"].iloc[0])
                df = df[df["ID_Modelo"] == fallback_id].copy()

        df["Fecha"] = pd.to_datetime(df["Fecha"])
        return df.sort_values("Fecha")

    def get_fairness(self, session_data: dict[str, Any] | None = None, model_id: str = "MDL-001") -> pd.DataFrame:
        sess = self._session_frames(session_data)
        if sess is not None:
            df = sess["fairness"].copy()
        else:
            df = self._read_sheet("fairness").copy()

        # FIX: fallback tolerante — igual que get_drift
        if model_id and "ID_Modelo" in df.columns:
            if model_id in df["ID_Modelo"].values:
                return df[df["ID_Modelo"] == model_id].copy()
            elif not df.empty:
                fallback_id = str(df["ID_Modelo"].iloc[0])
                return df[df["ID_Modelo"] == fallback_id].copy()
        return df.copy()

    def get_auditoria(
        self, session_data: dict[str, Any] | None = None, model_id: str | None = "MDL-001"
    ) -> pd.DataFrame:
        sess = self._session_frames(session_data)
        if sess is not None:
            df = sess["auditoria"].copy()
        else:
            df = self._read_sheet("auditoria").copy()

        # FIX: fallback tolerante — igual que get_drift
        if model_id and "ID_Modelo" in df.columns:
            if model_id in df["ID_Modelo"].values:
                df = df[df["ID_Modelo"] == model_id]
            elif not df.empty:
                fallback_id = str(df["ID_Modelo"].iloc[0])
                df = df[df["ID_Modelo"] == fallback_id]

        return df.sort_values("Timestamp", ascending=False)

    def get_seguridad(self, session_data: dict[str, Any] | None = None) -> pd.DataFrame:
        sess = self._session_frames(session_data)
        if sess is not None:
            df = sess["seguridad"].copy()
        else:
            df = self._read_sheet("seguridad").copy()
        df["Fecha"] = pd.to_datetime(df["Fecha"])
        return df.sort_values("Fecha")

    def get_gobierno_datos(self, session_data: dict[str, Any] | None = None) -> pd.DataFrame:
        # FIX: si hay datos de sesión, intentar leer la hoja gobierno_datos directamente
        # del payload (el archivo cargado puede traerla). Si no existe en sesión, sintetizar.
        if session_data and session_data.get("valid"):
            sheets = session_data.get("sheets", {})
            if "gobierno_datos" in sheets and sheets["gobierno_datos"]:
                df = pd.DataFrame(sheets["gobierno_datos"])
                # Normalizar nombre de columna ID_Modelo → ID para consistencia interna
                if "ID_Modelo" in df.columns and "ID" not in df.columns:
                    df = df.rename(columns={"ID_Modelo": "ID"})
                for col in ("Pct_Anonimizado", "Pct_Linaje", "Volumen_Procesado"):
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors="coerce")
                return df
            return self._synthesize_gobierno_datos(self.get_modelos(session_data))
        try:
            return self._read_sheet("gobierno_datos")
        except ValueError:
            return self._synthesize_gobierno_datos(self.get_modelos(session_data))

    def get_siop_versions(self, session_data: dict[str, Any] | None = None) -> pd.DataFrame:
        df = self.get_modelos(session_data)
        # FIX: intentar buscar SIOP-DS; si no hay, retornar todos los modelos ordenados por fecha
        siop = df[df["Nombre"] == "SIOP-DS"].sort_values("Fecha_Despliegue")
        if siop.empty:
            siop = df.sort_values("Fecha_Despliegue")
        return siop

    def invalidate_cache(self) -> None:
        self._read_sheet.cache_clear()


_data_manager: DataManager | None = None


def get_data_manager() -> DataManager:
    global _data_manager
    if _data_manager is None:
        _data_manager = DataManager()
    return _data_manager