import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Configuración de la aleatoriedad para reproducibilidad
np.random.seed(42)

# 1. GENERACIÓN DE LA HOJA: modelos
datos_modelos = {
    'ID': ['MOD-SIOP-01', 'MOD-PRED-02', 'MOD-RUT-03'],
    'Nombre': [
        'SIOP-DS (Optimización de Flota y Demanda Social)', 
        'SinergIA Reworked (Predicción de Tarifas)', 
        'MushrooMania Logistics (Mantenimiento Predictivo)'
    ],
    'Version': ['v2.1.0', 'v1.0.4', 'v3.2.1'],
    'Fecha_Despliegue': ['2026-01-15', '2026-02-20', '2025-11-05'],
    'Propietario': ['Dirección de Operaciones Aéreas', 'Oficina de TI / Comercial', 'Mantenimiento / TI'],
    'Estado': ['Producción', 'Staging', 'Producción'],
    'Nivel_Riesgo': ['Riesgo Alto', 'Riesgo Limitado', 'Riesgo Mínimo'],
    'Accuracy': [0.89, 0.74, 0.92],
    'F1_Score': [0.87, 0.71, 0.90]
}
df_modelos = pd.DataFrame(datos_modelos)

# Configuración de fechas para series temporales (16 semanas del 2026)
fechas = [datetime(2026, 1, 5) + timedelta(weeks=i) for i in range(16)]
fechas_str = [f.strftime('%Y-%m-%d') for f in fechas]

# 2. GENERACIÓN DE LA HOJA: drift (Enfoque en el SIOP-DS)
drift_data = []
for i, fecha in enumerate(fechas_str):
    # Simulación de comportamiento: Enero y Febrero estable, Marzo y Abril con degradación (Drift)
    if i < 8:  # Primeras 8 semanas (Estable)
        psi = round(np.random.uniform(0.04, 0.12), 3)
        ks_stat = round(np.random.uniform(0.05, 0.15), 3)
        ks_p = round(np.random.uniform(0.20, 0.80), 3)
        alerta = 'Normal'
    elif i >= 8 and i < 12:  # Semanas 8 a 11 (Crisis climática/territorial - Alerta Crítica)
        psi = round(np.random.uniform(0.26, 0.34), 3)
        ks_stat = round(np.random.uniform(0.40, 0.55), 3)
        ks_p = round(np.random.uniform(0.001, 0.04), 3)
        alerta = 'Crítico'
    else:  # Últimas semanas (Estabilización post-ajuste)
        psi = round(np.random.uniform(0.14, 0.19), 3)
        ks_stat = round(np.random.uniform(0.18, 0.24), 3)
        ks_p = round(np.random.uniform(0.06, 0.15), 3)
        alerta = 'Advertencia'
        
    drift_data.append(['MOD-SIOP-01', fecha, psi, ks_stat, ks_p, alerta])

df_drift = pd.DataFrame(drift_data, columns=['ID_Modelo', 'Fecha', 'PSI', 'KS_Statistic', 'KS_Pvalue', 'Alerta'])

# 3. GENERACIÓN DE LA HOJA: fairness
fairness_data = []
for i, fecha in enumerate(fechas_str):
    grupo_a = 'Rutas Troncales'
    grupo_b = 'Rutas Sociales'
    
    if i < 8: # Estable
        paridad = round(np.random.uniform(0.88, 1.12), 2)
        tpr_a, tpr_b = round(np.random.uniform(0.88, 0.92), 2), round(np.random.uniform(0.85, 0.89), 2)
        ppv_a, ppv_b = round(np.random.uniform(0.86, 0.90), 2), round(np.random.uniform(0.84, 0.88), 2)
    elif i >= 8 and i < 12: # El algoritmo discrimina sesgando las rutas sociales
        paridad = round(np.random.uniform(0.68, 0.75), 2) # Provoca semáforo Rojo (< 0.80)
        tpr_a, tpr_b = round(np.random.uniform(0.91, 0.94), 2), round(np.random.uniform(0.70, 0.75), 2) # Diferencia > 5%
        ppv_a, ppv_b = round(np.random.uniform(0.88, 0.91), 2), round(np.random.uniform(0.72, 0.76), 2)
    else: # Recuperación con mitigación por post-procesamiento
        paridad = round(np.random.uniform(0.82, 0.87), 2)
        tpr_a, tpr_b = round(np.random.uniform(0.87, 0.90), 2), round(np.random.uniform(0.83, 0.86), 2)
        ppv_a, ppv_b = round(np.random.uniform(0.85, 0.88), 2), round(np.random.uniform(0.81, 0.84), 2)
        
    fairness_data.append(['MOD-SIOP-01', fecha, grupo_a, grupo_b, paridad, tpr_a, tpr_b, ppv_a, ppv_b])

df_fairness = pd.DataFrame(fairness_data, columns=['ID_Modelo', 'Fecha', 'Grupo_A', 'Grupo_B', 'Paridad_Demografica', 'TPR_A', 'TPR_B', 'PPV_A', 'PPV_B'])

# 4. GENERACIÓN DE LA HOJA: auditoria (Human-in-the-Loop)
rutas_satena = [
    {"v": "Flota: ATR-42, Ruta: Medellín-Caucasia, Factor_Ocupacion: 88%", "p": "Incrementar Frecuencia"},
    {"v": "Flota: Twin Otter, Ruta: Bogotá-Nuquí, Factor_Ocupacion: 92%, Clima: Nublado", "p": "Mantener Capacidad"},
    {"v": "Flota: ATR-72, Ruta: Bogotá-Medellín, Factor_Ocupacion: 45%", "p": "Reducir Capacidad"},
    {"v": "Flota: Twin Otter, Ruta: Florencia-Puerto Leguízamo, Factor_Ocupacion: 60%", "p": "Reducir Capacidad"},
    {"v": "Flota: ATR-42, Ruta: Cali-Guapi, Factor_Ocupacion: 95%, Conflicto: Sí", "p": "Incrementar Frecuencia"},
    {"v": "Flota: Twin Otter, Ruta: Villavicencio-Mitú, Factor_Ocupacion: 51%", "p": "Reducir Capacidad"}
]

auditoria_data = []
operadores = ['Despachador_Cali_02', 'Analista_Bogota_05', 'Control_Medellin_01']
timestamp_base = datetime(2026, 4, 1, 8, 0, 0)

for i in range(60): # 60 registros de logs operativos
    ruta_sel = np.random.choice(rutas_satena)
    id_log = f"LOG-2026-{10000 + i}"
    timestamp = (timestamp_base + timedelta(hours=i*4, minutes=np.random.randint(0, 59))).strftime('%Y-%m-%d %H:%M:%S')
    variables = ruta_sel["v"]
    prediccion = ruta_sel["p"]
    operador = np.random.choice(operadores)
    
    # Simulación de criterio humano: el operador rechaza si el algoritmo intenta desproteger una ruta social
    if "Ruta: Florencia" in variables or "Ruta: Villavicencio" in variables and prediccion == "Reducir Capacidad":
        accion = "Rechazado" # Primacía de conectividad social
    else:
        accion = "Aprobado" if np.random.rand() > 0.15 else "Rechazado"
        
    auditoria_data.append([id_log, 'MOD-SIOP-01', timestamp, variables, prediccion, operador, accion])

df_auditoria = pd.DataFrame(auditoria_data, columns=['ID_Log', 'ID_Modelo', 'Timestamp', 'Variables_Entrada', 'Prediccion', 'Operador', 'Accion_Final'])

# 5. GENERACIÓN DE LA HOJA: seguridad (Eventos de Ciberseguridad del Sector Defensa)
seguridad_data = [
    ['INC-001', '2026-01-20', 'Falla de Sincronización MFA', 'Baja', 'Mitigado', 15],
    ['INC-002', '2026-02-14', 'Acceso No Autorizado (API Externa)', 'Alta', 'Mitigado', 120],
    ['INC-003', '2026-03-10', 'Intento de Inyección Adversaria', 'Crítica', 'Mitigado', 45],
    ['INC-004', '2026-03-28', 'Anomalía de Carga (Data Poisoning)', 'Alta', 'Mitigado', 180],
    ['INC-005', '2026-04-15', 'Falla de Sincronización MFA', 'Baja', 'Mitigado', 10],
    ['INC-006', '2026-05-02', 'Intento de Inyección Adversaria', 'Crítica', 'Mitigado', 30]
]
df_seguridad = pd.DataFrame(seguridad_data, columns=['ID_Incidente', 'Fecha', 'Tipo', 'Severidad', 'Estado', 'Tiempo_Resolucion'])

# 6. EXPORTACIÓN A UN ÚNICO ARCHIVO EXCEL MULTIPESTAÑA
nombre_archivo = 'datos_gobernadia.xlsx'

with pd.ExcelWriter(nombre_archivo, engine='openpyxl') as writer:
    df_modelos.to_excel(writer, sheet_name='modelos', index=False)
    df_drift.to_excel(writer, sheet_name='drift', index=False)
    df_fairness.to_excel(writer, sheet_name='fairness', index=False)
    df_auditoria.to_excel(writer, sheet_name='auditoria', index=False)
    df_seguridad.to_excel(writer, sheet_name='seguridad', index=False)

print(f"¡Éxito! El archivo '{nombre_archivo}' ha sido generado correctamente con las 5 pestañas parametrizadas.")   