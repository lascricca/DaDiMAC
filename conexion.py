import io
import requests
import streamlit as st
import pandas as pd

# =====================================================================
# CONFIGURACIÓN CLOUD DEFINITIVA: EMBARQUE AUTORIZADO DESDE FIREBASE
# =====================================================================
# Enlace maestro verificado con token criptográfico de L.A. Scricca Asesores, S.A.
URL_FIREBASE_STORAGE = "https://googleapis.com"

@st.cache_data(ttl=1800)  # Mantiene la base de datos en caché por 30 minutos para máxima fluidez
def cargar_datos_vivos_consolidados():
    """
    Descarga el archivo analítico masivo de clics directamente desde Firebase Storage.
    Ignora de forma estricta la columna 'timestamp' y procesa 'timestampraw' en formato Sage.
    """
    try:
        # Petición HTTP directa al bucket de almacenamiento utilizando el canal verificado
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
                
            # Homologación total de columnas a minúsculas y sin impurezas de texto
            df.columns = df.columns.str.replace('"', '').str.strip().str.lower()
            
            # 1. PROCESAMIENTO EXCLUSIVO DE LA COLUMNA TIMESTAMPRAW DE SAGE
            if 'timestampraw' in df.columns:
                # Se fuerza la conversión de la cronología nativa de Sage 50 ignorando 'timestamp'
                df['Fecha_Hora'] = pd.to_datetime(df['timestampraw'], errors='coerce')
            else:
                # Mapeo de contingencia si viene en otra variante de texto
                columnas_alternas = ['date_time', 'fecha_hora']
                col_encontrada = None
                for col in columnas_alternas:
                    if col in df.columns:
                        col_encontrada = col
                        break
                if col_encontrada:
                    df['Fecha_Hora'] = pd.to_datetime(df[col_encontrada], errors='coerce')
                else:
                    df['Fecha_Hora'] = pd.to_datetime(df.iloc[:, 0], errors='coerce')

            # 2. HOMOLOGACIÓN DE VARIABLES CONTABLES INTERACTIVAS DE SAGE 50
            df['Compañía'] = df['companyname'] if 'companyname' in df.columns else (df['compañía'] if 'compañía' in df.columns else "Sin Compañía")
            df['Usuario'] = df['userid'] if 'userid' in df.columns else (df['usuario'] if 'usuario' in df.columns else "Desconocido")
            df['Monto'] = pd.to_numeric(df['mainamt'], errors='coerce').fillna(0.0) if 'mainamt' in df.columns else 0.0
            df['Acción'] = df['eventaction'] if 'eventaction' in df.columns else "Clic"
            df['Ventana_Detalle'] = df['windowtext'] if 'windowtext' in df.columns else ""

            # Depuración estricta de registros donde la fecha de Sage falló críticamente
            df = df.dropna(subset=['Fecha_Hora'])
            
            # FILTRO DE SEGURIDAD CRÍTICO: Acotamos las fechas para sanear registros corruptos 
            # del log de Sage (ej: años erróneos como 1970 o 2099) que rompen el date_input de Streamlit.
            anio_actual = pd.Timestamp.now().year
            df = df[(df['Fecha_Hora'].dt.year >= 2000) & (df['Fecha_Hora'].dt.year <= anio_actual)]
            
            if df.empty:
                return None

            # Ordenamiento cronológico de auditoría (más reciente primero)
            df = df.sort_values(by='Fecha_Hora', ascending=False)
            return df
        else:
            st.error(f"⚠️ Firebase Storage rechazó la descarga. Código HTTP: {respuesta.status_code}")
            return None
            
    except Exception as e:
        st.error(f"⚠️ Error crítico de conexión al absorber base de datos en Firebase: {e}")
        return None
