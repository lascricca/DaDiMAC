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
URL_FIREBASE_STORAGE = f"https://googleapis.com{BUCKET_NAME}/o/{ARCHIVO_CODIFICADO}?alt=media"

@st.cache_data(ttl=1800)  # Mantiene la base de datos en caché por 30 minutos para máxima fluidez
def cargar_datos_vivos_consolidados():
    """
    Descarga el archivo analítico masivo de clics directamente desde Firebase Storage
    y aplica un mapeo inteligente e inmune a variaciones de mayúsculas/minúsculas.
    """
    try:
        # Petición HTTP directa al bucket de almacenamiento liberado
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
                
            # Homologación total de columnas a minúsculas y sin impurezas para evitar descalces
            df.columns = df.columns.str.replace('"', '').str.strip().str.lower()
            
            # 1. ESCÁNER INTELIGENTE DE LA LÍNEA TEMPORAL (FECHA Y HORA)
            columnas_fecha = ['date_time', 'date', 'time', 'fecha_hora', 'fecha']
            col_fecha_encontrada = None
            
            for col in columnas_fecha:
                if col in df.columns:
                    col_fecha_encontrada = col
                    break
                    
            if col_fecha_encontrada:
                df['Fecha_Hora'] = pd.to_datetime(df[col_fecha_encontrada], errors='coerce')
            else:
                # Si las cabeceras fallan, tomamos la primera columna por defecto
                df['Fecha_Hora'] = pd.to_datetime(df.iloc[:, 0], errors='coerce')

            # 2. HOMOLOGACIÓN DE VARIABLES CONTABLES ADAPTATIVA
            df['Compañía'] = df['companyname'] if 'companyname' in df.columns else (df['compañía'] if 'compañía' in df.columns else "Sin Compañía")
            df['Usuario'] = df['userid'] if 'userid' in df.columns else (df['usuario'] if 'usuario' in df.columns else "Desconocido")
            df['Monto'] = pd.to_numeric(df['mainamt'], errors='coerce').fillna(0.0) if 'mainamt' in df.columns else (pd.to_numeric(df['monto'], errors='coerce').fillna(0.0) if 'monto' in df.columns else 0.0)
            df['Acción'] = df['eventaction'] if 'eventaction' in df.columns else (df['acción'] if 'acción' in df.columns else "Clic")
            df['Ventana_Detalle'] = df['windowtext'] if 'windowtext' in df.columns else (df['ventana_detalle'] if 'ventana_detalle' in df.columns else "")

            # Limpieza de nulos únicamente si la conversión falló drásticamente
            if df['Fecha_Hora'].notna().sum() > 0:
                df = df.dropna(subset=['Fecha_Hora'])
            
            # Ordenamiento cronológico de auditoría
            df = df.sort_values(by='Fecha_Hora', ascending=False)
            
            return df
        else:
            st.error(f"⚠️ Firebase Storage rechazó la descarga. Código HTTP: {respuesta.status_code}")
            return None
            
    except Exception as e:
        st.error(f"⚠️ Error crítico de conexión al absorber base de datos en Firebase: {e}")
        return None
