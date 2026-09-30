import io
import requests
import streamlit as st
import pandas as pd

# =====================================================================
# CONFIGURACIÓN CLOUD: EXTRACCIÓN TRANSACCIONAL DESDE GOOGLE DRIVE
# =====================================================================
ID_DOCUMENTO_DRIVE = "1X1vKvJIA4ymt_iPeeXlYDTPE0dzFoZbl"
URL_DESCARGA_DIRECTA = f"https://google.com{ID_DOCUMENTO_DRIVE}/export?format=csv"

@st.cache_data(ttl=1800)  # Mantiene la base en memoria RAM por 30 minutos
def cargar_datos_vivos_consolidados():
    """
    Descarga el archivo masivo usando 'requests' para evadir restricciones de 
    red del servidor cloud y procesa los clics contables de MAC & Asociados.
    """
    try:
        # Forzamos la descarga mediante peticiones HTTP seguras de requests
        respuesta = requests.get(URL_DESCARGA_DIRECTA, timeout=30)
        
        if respuesta.status_code == 200:
            # Convertimos el texto descargado en un flujo de memoria para Pandas
            objeto_memoria = io.StringIO(respuesta.text)
            df = pd.read_csv(objeto_memoria, sep=None, engine='python')
            
            # Mapeo y tipificación obligatoria de columnas contables
            if 'Date_Time' in df.columns:
                df['Fecha_Hora'] = pd.to_datetime(df['Date_Time'], errors='coerce')
            elif 'Fecha_Hora' in df.columns:
                df['Fecha_Hora'] = pd.to_datetime(df['Fecha_Hora'], errors='coerce')
            else:
                df['Fecha_Hora'] = pd.to_datetime(df.iloc[:, 0], errors='coerce')

            # Homologación estructural de nombres para la interfaz
            df['Compañía'] = df['CompanyName'] if 'CompanyName' in df.columns else (df['Compañía'] if 'Compañía' in df.columns else "Sin Compañía")
            df['Usuario'] = df['UserID'] if 'UserID' in df.columns else (df['Usuario'] if 'Usuario' in df.columns else "Desconocido")
            df['Monto'] = df['MainAmt'] if 'MainAmt' in df.columns else (df['Monto'] if 'Monto' in df.columns else 0.0)
            df['Acción'] = df['EventAction'] if 'EventAction' in df.columns else "Clic"
            df['Ventana_Detalle'] = df['WindowText'] if 'WindowText' in df.columns else ""

            # Limpieza y ordenamiento cronológico
            df = df.dropna(subset=['Fecha_Hora'])
            df = df.sort_values(by='Fecha_Hora', ascending=False)
            
            return df
        else:
            st.error(f"⚠️ Google Drive rechazó la descarga. Código HTTP: {respuesta.status_code}")
            return None
            
    except Exception as e:
        st.error(f"⚠️ Error crítico de conexión al absorber base de datos en Google Drive: {e}")
        return None
