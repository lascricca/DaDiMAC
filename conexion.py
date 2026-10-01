import io
import requests
import streamlit as st
import pandas as pd

# =====================================================================
# CONFIGURACIÓN CLOUD DEFINITIVA: AUDITORÍA DE CALIDAD DESDE FIREBASE
# =====================================================================

# ⚠️ REEMPLAZA ESTA URL CON EL ENLACE FRESCO QUE COPIES DE FIREBASE CONSOLE
# El token actual puede haber expirado y causar el error 404.
URL_FIREBASE_STORAGE = "https://firebasestorage.googleapis.com/v0/b/dadimac-62fd6.firebasestorage.app/o/DaDiMAC_ExtraeCSV.csv?alt=media&token=669de119-c19c-4946-9b11-305714951df4"

def validar_integridad_cronologica(df_crudo):
    """
    Analiza la columna 'timestampraw' antes de entregar los datos a la interfaz.
    Si encuentra anomalías que rompen el calendario, genera un reporte y frena la ejecución.
    """
    # Guardamos la posición original de la fila física (Pandas base 0 + 2 por el encabezado del CSV)
    df_crudo['Fila_Excel'] = df_crudo.index + 2
    
    # 1. Detectar registros donde la conversión a fecha falla por completo (NaT)
    fechas_convertidas = pd.to_datetime(df_crudo['timestampraw'], errors='coerce')
    mascara_nan = fechas_convertidas.isna()
    
    # 2. Detectar registros con años incoherentes (fuera del rango lógico 2000 - Año Actual)
    anio_actual = pd.Timestamp.now().year
    mascara_anio_invalido = (fechas_convertidas.dt.year < 2000) | (fechas_convertidas.dt.year > anio_actual)
    
    # Consolidamos todas las filas corruptas
    df_corruptos = df_crudo[mascara_nan | (mascara_anio_invalido & ~mascara_nan)]
    
    if not df_corruptos.empty:
        st.error("### 🛑 Control de Calidad DaDiMAC: Registros Corruptos Detectados")
        st.warning(
            f"Se han localizado **{len(df_corruptos)} filas** en el archivo 'DaDiMAC_ExtraeCSV.csv' con formatos "
            f"de fecha inválidos o años fuera de rango en la columna 'timestampraw' que impiden abrir el calendario."
        )
        
        # Estructuramos el reporte exacto con la posición de la fila para el auditor
        reporte = pd.DataFrame({
            'Fila Física (Excel/CSV)': df_corruptos['Fila_Excel'],
            'Valor Encontrado (TimeStampRaw)': df_corruptos['timestampraw'],
            'Compañía': df_corruptos['companyname'] if 'companyname' in df_corruptos.columns else "N/A",
            'Usuario': df_corruptos['userid'] if 'userid' in df_corruptos.columns else "N/A"
        })
        
        st.dataframe(reporte.sort_values(by='Fila Física (Excel/CSV)'), use_container_width=True)
        st.info("💡 **Acción requerida:** Corrija los valores listados arriba directamente en su base de datos o archivo de extracción antes de continuar.")
        st.stop()  # Detiene por completo la ejecución de DaDiMAC.py de forma limpia

@st.cache_data(ttl=1800)  # Mantiene la base de datos en caché por 30 minutos
def cargar_datos_vivos_consolidados():
    """
    Descarga el archivo analítico masivo de clics desde Firebase Storage
    y ejecuta obligatoriamente el módulo de validación de integridad.
    """
    try:
        respuesta = requests.get(URL_FIREBASE_STORAGE, timeout=60)
        
        if respuesta.status_code == 200:
            objeto_memoria = io.StringIO(respuesta.text)
            
            # Motor robusto de lectura automática de separadores
            df = pd.read_csv(
                objeto_memoria, 
                sep=None, 
                engine='python', 
                on_bad_lines='skip'
            )
            
            if df.empty or len(df.columns) < 1:
                return None
                
            # Homologación total de columnas a minúsculas para el motor de validación
            df.columns = df.columns.str.replace('"', '').str.strip().str.lower()
            
            # MÓDULO DE VALIDACIÓN ACTIVO: Si hay errores, detendrá la app y mostrará las filas
            validar_integridad_cronologica(df)
            
            # Si pasa la validación con éxito, procesamos las variables normalmente
            df['Fecha_Hora'] = pd.to_datetime(df['timestampraw'])
            
            df['Compañía'] = df['companyname'] if 'companyname' in df.columns else (df['compañía'] if 'compañía' in df.columns else "Sin Compañía")
            df['Usuario'] = df['userid'] if 'userid' in df.columns else (df['usuario'] if 'usuario' in df.columns else "Desconocido")
            df['Monto'] = pd.to_numeric(df['mainamt'], errors='coerce').fillna(0.0) if 'mainamt' in df.columns else 0.0
            df['Acción'] = df['eventaction'] if 'eventaction' in df.columns else "Clic"
            df['Ventana_Detalle'] = df['windowtext'] if 'windowtext' in df.columns else ""

            df = df.sort_values(by='Fecha_Hora', ascending=False)
            return df
        else:
            st.error(f"⚠️ Firebase Storage rechazó la descarga. Código HTTP: {respuesta.status_code}. Copie el enlace de descarga fresco desde la consola de Firebase para renovar el token.")
            return None
            
    except Exception as e:
        st.error(f"⚠️ Error crítico de conexión al absorber base de datos en Firebase: {e}")
        return None
