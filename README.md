# Dashboard Estratégico de Gobernanza de IA — SATENA

> Proyecto académico — Materia: Gobierno de TI  
> Framework: COBIT 2019 · EU AI Act · ISO/IEC 42001 · CONPES 4058 · UNESCO · NIST AI RMF

---

## Descripción general

Dashboard interactivo desarrollado en Python/Dash que implementa un sistema integral de gobernanza para modelos de inteligencia artificial en **SATENA** (Servicios Aéreos a Territorios Nacionales). El sistema aplica los criterios de calidad de la información de COBIT 2019 (Exactitud, Integridad y Consistencia) para la validación de datos, y expone métricas de MLOps, drift, fairness, explicabilidad, sesgos y seguridad en tiempo real.

El modelo principal monitoreado es **SIOP-DS** (Sistema Integrado de Optimización de Flota y Demanda Social), clasificado como **Alto Riesgo** bajo el EU AI Act por su impacto en rutas de conectividad social.

---

## Estructura del proyecto

```
PROYECTO-DASHBOARD-IA/
├── app.py                  # Punto de entrada — login, routing, callbacks globales
├── requirements.txt        # Dependencias Python
├── pages/                  # Módulos de cada pestaña del dashboard
│   ├── gobierno.py         # Panel superior: KPIs, inventario, radar de cumplimiento
│   ├── mlops.py            # Tab 1: Ciclo de vida y pipelines CI/CD
│   ├── versionado.py       # Tab 2: Historial de versiones SIOP-DS
│   ├── drift.py            # Tab 3: Monitoreo PSI y KS-Test
│   ├── explicabilidad.py   # Tab 4: Valores SHAP
│   ├── fairness.py         # Tab 5: Auditoría y métricas de equidad
│   ├── sesgos.py           # Tab 6: Sesgos y robustez adversarial
│   └── seguridad.py        # Tab 7: Incidentes y cobertura MFA
├── src/                    # Lógica de negocio
│   ├── analytics.py        # Motor analítico: PSI, KS-Test, SHAP, fairness
│   ├── components.py       # Generadores de figuras Plotly y componentes visuales
│   ├── data_manager.py     # Proveedor de datos: disco o sesión validada
│   ├── validator.py        # Validación COBIT 2019 de archivos Excel
│   └── utils.py            # Constantes, colores, cifrado, utilidades
├── data/
│   ├── datos_gobernadia.xlsx   # Datos semilla del dashboard
│   └── generar_datos.py        # Script para regenerar los datos de prueba
└── assets/                 # CSS personalizado
```

---

## Requisitos

- Python 3.11 o superior
- pip

Dependencias principales (ver `requirements.txt`):

```
dash==2.18.2
dash-bootstrap-components==1.6.0
plotly==5.24.1
pandas==2.2.3
openpyxl==3.1.5
numpy==2.1.3
scipy==1.14.1
scikit-learn==1.5.2
cryptography==43.0.3
```

---

## Instalación y ejecución

```bash
# 1. Clonar el repositorio
git clone https://github.com/tu-usuario/proyecto-dashboard-ia.git
cd proyecto-dashboard-ia

# 2. Crear entorno virtual
python -m venv .venv
source .venv/bin/activate        # Linux/Mac
.venv\Scripts\activate           # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. (Opcional) Regenerar datos de prueba
python data/generar_datos.py

# 5. Ejecutar el dashboard
python app.py
```

Abrir en el navegador: [http://localhost:8050](http://localhost:8050)

**Credenciales demo:**
- Usuario: `admin.satena`
- Contraseña: `Satena@2026!`

---

## Carga de datos

El dashboard acepta archivos `.xlsx` con exactamente **5 hojas requeridas** (puede tener hojas adicionales como `gobierno_datos`):

| Hoja | Descripción |
|------|-------------|
| `modelos` | Inventario de modelos de IA con métricas de rendimiento |
| `drift` | Series temporales de PSI y KS-Statistic por modelo |
| `fairness` | Métricas de equidad: Paridad Demográfica, TPR, PPV por grupo |
| `auditoria` | Log inmutable de decisiones Human-in-the-Loop |
| `seguridad` | Registro de incidentes de ciberseguridad |

Para generar un archivo de prueba compatible:

```bash
python data/generar_datos.py
```

El archivo `datos_prueba_carga.xlsx` puede cargarse desde el botón **"Cargar Excel de datos"** en la barra superior del dashboard.

---

## Módulos del dashboard

### Panel superior — Gobierno de la IA
KPIs globales (modelos en producción, % documentación, % auditoría vigente, % cumplimiento), inventario de modelos con clasificación EU AI Act, gráfica de gobierno de datos y radar de cumplimiento normativo multi-marco.

### Tab 1 — MLOps
Tasa de éxito de pipelines CI/CD, línea de tiempo de despliegues mensuales y distribución de modelos por fase del ciclo de vida (Desarrollo → Staging → Producción → Deprecado).

### Tab 2 — Versionado
Historial de versiones de SIOP-DS con evolución de Accuracy y F1-Score entre versiones.

### Tab 3 — Monitoreo y Drift
Evolución temporal del PSI con umbral crítico (0.25), resultado del KS-Test (Kolmogorov-Smirnov) e histograma de comparación de distribuciones entrenamiento vs. producción.

### Tab 4 — Explicabilidad
Valores SHAP promedio por variable de entrada del modelo de demanda social, ordenados por importancia.

### Tab 5 — Auditoría y Fairness
Semáforos COBIT para Paridad Demográfica (umbral 0.80–1.25), Igualdad de Oportunidades |ΔTPR| (< 5%) y Paridad de Error de Predicción |ΔPPV| (< 5%). Log inmutable de auditoría Human-in-the-Loop.

### Tab 6 — Sesgos y Robustez
Heatmap de sesgos por variable operativa y resultados de resiliencia ante ataques adversariales simulados (FGSM, PGD, Envenenamiento, Membership Inference).

### Tab 7 — Seguridad
Cobertura MFA, línea temporal de vectores de ataque mitigados y tabla de incidentes con severidad y tiempo de resolución.

---

## Arquitectura de datos

```
dcc.Upload (xlsx)
     │
     ▼
parse_upload_to_session_payload()
     │
     ▼
validate_excel_bytes()  ←── Criterios COBIT 2019
     │                       Exactitud · Integridad · Consistencia
     ▼
frames_to_session_payload()
     │
     ▼
dcc.Store (session-data-store)
     │
     ▼
DataManager.get_*()  ←── Todos los callbacks leen desde aquí
     │
     ▼
analytics.py  →  components.py  →  dcc.Graph / DataTable
```

---

## Marcos normativos implementados

| Marco | Aplicación en el dashboard |
|-------|---------------------------|
| **COBIT 2019** | Validación de calidad de datos (Exactitud, Integridad, Consistencia) al cargar Excel |
| **EU AI Act** | Clasificación de riesgo de modelos (Alto / Limitado / Mínimo) en inventario |
| **ISO/IEC 42001** | Indicadores de madurez en radar de cumplimiento |
| **CONPES 4058** | Indicadores de gobernanza para IA en entidades públicas colombianas |
| **UNESCO Rec. on AI** | Dimensión ética en radar de cumplimiento |
| **NIST AI RMF** | Gestión de riesgos en radar de cumplimiento |

---

## Variables de entorno (opcional)

```bash
# Sobrescribir la contraseña demo (recomendado en producción)
export SATENA_DEMO_PASSWORD="tu_contraseña_segura"
```

---

## Notas de desarrollo

- El dashboard fue iniciado con **Cursor** y continuado con **VS Code**.
- Los datos son sintéticos y generados con semillas fijas para reproducibilidad.
- El archivo `datos_gobernadia.xlsx` se genera automáticamente al primer arranque si no existe.
- La carpeta `.secrets/` contiene la clave Fernet para cifrado interno y está excluida del repositorio.
