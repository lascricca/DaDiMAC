import io
import urllib.parse
import requests
import streamlit as st
import pandas as pd

# =====================================================================
# CONFIGURACIÓN CLOUD DEFINITIVA: EMBARQUE DESDE FIREBASE STORAGE
# =====================================================================
BUCKET_NAME = "dadimac-62fd6.firebasestorage.app" 
NOMBRE_ARCHIVO = "DaDiMAC_ExtraeCSV.csv" 

# Codificación segura del nombre del archivo para la API de Google Cloud
ARCHIVO_CODIFICADO = urllib.parse.quote(NOMBRE_ARCHIVO, safe="")

# Construcción de la URL base oficial de descarga
URL_FIREBASE_STORAGE = f"https://firebasestorage.googleapis.com/v0/b/{BUCKET_NAME}/o/{ARCHIVO_CODIFICADO}?alt=media"

@st.cache_data(ttl=1800)  # Conserva en memoria RAM por 30 minutos para velocidad máxima
def cargar_datos_vivos_consolidados():
    """
    Descarga el archivo analítico masivo de clics directamente desde la red 
    interna de Firebase Storage a máxima velocidad.
    """
    try:
        # Petición HTTP directa al bucket de almacenamiento de tu proyecto
        respuesta = requests.get(URL_FIREBASE_STORAGE, timeout=60)
        
        if respuesta.status_code == 200:
            objeto_memoria = io.StringIO(respuesta.text)
            
            # Motor tolerante a fallos de líneas o comillas en Sage 50
            df = pd.read_csv(
                objeto_memoria, 
                sep=None, 
                engine='python', 
                on_bad_lines='skip'
            )
            
            if df.empty or len(df.columns) < 2:
                return None
                
            # Limpieza estándar de impurezas en las cabeceras
            df.columns = df.columns.str.replace('"', '').str.strip()
            
            # Mapeo y tipificación cronológica obligatoria de la línea temporal
            if 'Date_Time' in df.columns:
                df['Fecha_Hora'] = pd.to_datetime(df['Date_Time'], errors='coerce')
            elif 'Fecha_Hora' in df.columns:
                df['Fecha_Hora'] = pd.to_datetime(df['Fecha_Hora'], errors='coerce')
            else:
                df['Fecha_Hora'] = pd.to_datetime(df.iloc[:, 0], errors='coerce')

            # Homologación estructural de variables para la interfaz interactiva
            df['Compañía'] = df['CompanyName'] if 'CompanyName' in df.columns else (df['Compañía'] if 'Compañía' in df.columns else "Sin Compañía")
            df['Usuario'] = df['UserID'] if 'UserID' in df.columns else (df['Usuario'] if 'Usuario' in df.columns else "Desconocido")
            df['Monto'] = pd.to_numeric(df['MainAmt'], errors='coerce').fillna(0.0) if 'MainAmt' in df.columns else 0.0
            df['Acción'] = df['EventAction'] if 'EventAction' in df.columns else "Clic"
            df['Ventana_Detalle'] = df['WindowText'] if 'WindowText' in df.columns else ""

            # Depuración final de registros vacíos
            df = df.dropna(subset=['Fecha_Hora'])
            df = df.sort_values(by='Fecha_Hora', ascending=False)
            
            return df
        else:
            st.error(f"⚠️ Firebase Storage rechazó la descarga. Código HTTP: {respuesta.status_code}. Es muy probable que necesites ajustar las reglas de almacenamiento a modo lectura pública.")
            return None
            
    except Exception as e:
        st.error(f"⚠️ Error crítico de conexión al absorber base de datos en Firebase: {e}")
        return None
