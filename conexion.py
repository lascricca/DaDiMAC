import io
import requests
import streamlit as st
import pandas as pd

# =====================================================================
# CONFIGURACIÓN CLOUD DEFINITIVA: EMBARQUE AUTORIZADO DESDE FIREBASE
# =====================================================================
# Enlace maestro verificado con token criptográfico de L.A. Scricca Asesores, S.A.
URL_FIREBASE_STORAGE = "https://firebasestorage.googleapis.com/v0/b/dadimac-62fd6.firebasestorage.app/o/DaDiMAC_ExtraeCSV.csv?alt=media&token=669de119-c19c-4946-9b11-305714951df4"

@st.cache_data(ttl=1800)  # Conserva en memoria RAM por 30 minutos para velocidad máxima
def cargar_datos_vivos_consolidados():
    """
    Descarga el archivo analítico masivo de clics directamente desde la red 
    interna de Firebase Storage utilizando el token oficial de acceso público.
    """
    try:
        # Petición HTTP directa al bucket de almacenamiento utilizando el canal verificado
        respuesta = requests.get(URL_FIREBASE_STORAGE, timeout=60)
        
        if respuesta.status_code == 200:
            objeto_memoria = io.StringIO(respuesta.text)
            
            # Motor robusto de lectura automática de separadores (detecta comas o puntos y comas)
            df = pd.read_csv(
                objeto_memoria, 
                sep=None, 
                engine='python', 
                on_bad_lines='skip'
            )
            
            if df.empty or len(df.columns) < 1:
                return None
                
            # Homologación total de columnas a minúsculas para evitar descalces por mayúsculas
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
                # Si las cabeceras fallan o vienen alteradas, tomamos la primera columna por defecto
                df['Fecha_Hora'] = pd.to_datetime(df.iloc[:, 0], errors='coerce')

            # 2. HOMOLOGACIÓN DE VARIABLES CONTABLES INTERACTIVAS DE SAGE 50
            df['Compañía'] = df['companyname'] if 'companyname' in df.columns else (df['compañía'] if 'compañía' in df.columns else "Sin Compañía")
            df['Usuario'] = df['userid'] if 'userid' in df.columns else (df['usuario'] if 'usuario' in df.columns else "Desconocido")
            df['Monto'] = pd.to_numeric(df['mainamt'], errors='coerce').fillna(0.0) if 'mainamt' in df.columns else 0.0
            df['Acción'] = df['eventaction'] if 'eventaction' in df.columns else "Clic"
            df['Ventana_Detalle'] = df['windowtext'] if 'windowtext' in df.columns else ""

            # Depuración de registros donde la fecha falló críticamente
            if df['Fecha_Hora'].notna().sum() > 0:
                df = df.dropna(subset=['Fecha_Hora'])
            
            # Ordenamiento cronológico de auditoría (más reciente primero)
            df = df.sort_values(by='Fecha_Hora', ascending=False)
            return df
        else:
            st.error(f"⚠️ Firebase Storage rechazó la descarga. Código HTTP: {respuesta.status_code}")
            return None
            
    except Exception as e:
        st.error(f"⚠️ Error crítico de conexión al absorber base de datos en Firebase: {e}")
        return None
