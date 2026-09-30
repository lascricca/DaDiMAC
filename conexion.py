import io
import requests
import streamlit as st
import pandas as pd

# =====================================================================
# CONFIGURACIÓN CLOUD: RUTA ESTÁTICA DIRECTA A TU GOOGLE DRIVE
# =====================================================================
# Construcción fija de tu enlace oficial para evitar errores de formateo
URL_DESCARGA_DIRECTA = "https://google.com"

@st.cache_data(ttl=1800)  # Conserva en memoria RAM por 30 minutos para velocidad máster
def cargar_datos_vivos_consolidados():
    """
    Descarga el archivo masivo usando 'requests' de forma directa y estática
    para evadir cualquier error de resolución de nombres en Streamlit Cloud.
    """
    try:
        # Petición HTTP directa a los servidores de Google Drive
        respuesta = requests.get(URL_DESCARGA_DIRECTA, timeout=45)
        
        if respuesta.status_code == 200:
            # Transmutamos el texto descargado en un flujo de memoria para Pandas
            objeto_memoria = io.StringIO(respuesta.text)
            df = pd.read_csv(objeto_memoria, sep=None, engine='python')
            
            # Mapeo y tipificación obligatoria de columnas contables
            if 'Date_Time' in df.columns:
                df['Fecha_Hora'] = pd.to_datetime(df['Date_Time'], errors='coerce')
            elif 'Fecha_Hora' in df.columns:
                df['Fecha_Hora'] = pd.to_datetime(df['Fecha_Hora'], errors='coerce')
            else:
                df['Fecha_Hora'] = pd.to_datetime(df.iloc[:, 0], errors='coerce')

            # Homologación estructural de nombres para el orquestador y la interfaz
            df['Compañía'] = df['CompanyName'] if 'CompanyName' in df.columns else (df['Compañía'] if 'Compañía' in df.columns else "Sin Compañía")
            df['Usuario'] = df['UserID'] if 'UserID' in df.columns else (df['Usuario'] if 'Usuario' in df.columns else "Desconocido")
            df['Monto'] = df['MainAmt'] if 'MainAmt' in df.columns else (df['Monto'] if 'Monto' in df.columns else 0.0)
            df['Acción'] = df['EventAction'] if 'EventAction' in df.columns else "Clic"
            df['Ventana_Detalle'] = df['WindowText'] if 'WindowText' in df.columns else ""

            # Limpieza y ordenamiento cronológico de auditoría
            df = df.dropna(subset=['Fecha_Hora'])
            df = df.sort_values(by='Fecha_Hora', ascending=False)
            
            return df
        else:
            st.error(f"⚠️ Google Drive rechazó la descarga. Código HTTP: {respuesta.status_code}")
            return None
            
    except Exception as e:
        st.error(f"⚠️ Error crítico de conexión al absorber base de datos en Google Drive: {e}")
        return None
