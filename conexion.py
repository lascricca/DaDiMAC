import streamlit as st
import pandas as pd

# =====================================================================
# CONFIGURACIÓN CLOUD: EXTRACCIÓN TRANSACCIONAL DESDE GOOGLE DRIVE
# =====================================================================
# Identificador único extraído de tu enlace corporativo oficial
ID_DOCUMENTO_DRIVE = "1X1vKvJIA4ymt_iPeeXlYDTPE0dzFoZbl"

# URL de exportación directa en formato CSV estructurado para Pandas
URL_DESCARGA_DIRECTA = f"https://google.com{ID_DOCUMENTO_DRIVE}/export?format=csv"

@st.cache_data(ttl=1800)  # Conserva en caché por 30 minutos para optimizar la velocidad cloud
def cargar_datos_vivos_consolidados():
    """
    Descarga y procesa en la memoria RAM del servidor cloud el universo masivo 
    de clics contables proveniente del Google Drive de MAC & Asociados.
    """
    try:
        # Descarga directa del archivo CSV masivo
        df = pd.read_csv(URL_DESCARGA_DIRECTA, sep=None, engine='python')
        
        # Mapeo y tipificación obligatoria de columnas contables
        if 'Date_Time' in df.columns:
            df['Fecha_Hora'] = pd.to_datetime(df['Date_Time'], errors='coerce')
        elif 'Fecha_Hora' in df.columns:
            df['Fecha_Hora'] = pd.to_datetime(df['Fecha_Hora'], errors='coerce')
        else:
            # Fallback en caso de que las cabeceras varíen ligeramente
            df['Fecha_Hora'] = pd.to_datetime(df.iloc[:, 0], errors='coerce')

        # Homologación estructural de nombres para el orquestador y la interfaz
        df['Compañía'] = df['CompanyName'] if 'CompanyName' in df.columns else (df['Compañía'] if 'Compañía' in df.columns else "Sin Compañía")
        df['Usuario'] = df['UserID'] if 'UserID' in df.columns else (df['Usuario'] if 'Usuario' in df.columns else "Desconocido")
        df['Monto'] = df['MainAmt'] if 'MainAmt' in df.columns else (df['Monto'] if 'Monto' in df.columns else 0.0)
        df['Acción'] = df['EventAction'] if 'EventAction' in df.columns else "Clic"
        df['Ventana_Detalle'] = df['WindowText'] if 'WindowText' in df.columns else ""

        # Limpieza de registros nulos en la línea temporal
        df = df.dropna(subset=['Fecha_Hora'])
        
        # Ordenar cronológicamente para consistencia de auditoría
        df = df.sort_values(by='Fecha_Hora', ascending=False)
        
        return df
        
    except Exception as e:
        st.error(f"⚠️ Error crítico de conexión al absorber base de datos en Google Drive: {e}")
        return None
