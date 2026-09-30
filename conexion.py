import io
import requests
import streamlit as st
import pandas as pd

# =====================================================================
# CONFIGURACIÓN CLOUD: EXTRACCIÓN ROBUSTA Y SINCRONIZADA DE GOOGLE DRIVE
# =====================================================================
URL_DESCARGA_DIRECTA = "https://google.com"

@st.cache_data(ttl=1800)  # Mantiene los datos en memoria por 30 minutos
def cargar_datos_vivos_consolidados():
    """
    Descarga el archivo masivo desde Google Drive y lo procesa con un motor
    flexible que auto-detecta el delimitador real sin corromper la estructura de columnas.
    """
    try:
        # Petición HTTP directa a los servidores de Google Drive
        respuesta = requests.get(URL_DESCARGA_DIRECTA, timeout=60)
        
        if respuesta.status_code == 200:
            # Convertimos el texto en un flujo de lectura para Pandas
            objeto_memoria = io.StringIO(respuesta.text)
            
            # MOTOR EQUILIBRADO: Eliminamos la restricción rígida de QUOTE_NONE para
            # evitar el desajuste de columnas, pero activamos la tolerancia a líneas corruptas.
            df = pd.read_csv(
                objeto_memoria, 
                sep=None,             # Detecta automáticamente si usa comas (,) o puntos y comas (;)
                engine='python',      # Requerido para usar la detección automática de separador
                on_bad_lines='skip'   # Descarta limpiamente cualquier fila deforme sin tumbar el sistema
            )
            
            # Si el archivo se leyó pero no se estructuraron columnas correctas, salta la advertencia
            if df.empty or len(df.columns) < 2:
                return None
                
            # Limpieza estándar de impurezas en los nombres de las columnas
            df.columns = df.columns.str.replace('"', '').str.strip()
            
            # Mapeo y tipificación obligatoria de la línea temporal
            if 'Date_Time' in df.columns:
                df['Fecha_Hora'] = pd.to_datetime(df['Date_Time'], errors='coerce')
            elif 'Fecha_Hora' in df.columns:
                df['Fecha_Hora'] = pd.to_datetime(df['Fecha_Hora'], errors='coerce')
            else:
                df['Fecha_Hora'] = pd.to_datetime(df.iloc[:, 0], errors='coerce')

            # Homologación estructural de nombres para el orquestador y la interfaz
            df['Compañía'] = df['CompanyName'] if 'CompanyName' in df.columns else (df['Compañía'] if 'Compañía' in df.columns else "Sin Compañía")
            df['Usuario'] = df['UserID'] if 'UserID' in df.columns else (df['Usuario'] if 'Usuario' in df.columns else "Desconocido")
            df['Monto'] = pd.to_numeric(df['MainAmt'], errors='coerce').fillna(0.0) if 'MainAmt' in df.columns else 0.0
            df['Acción'] = df['EventAction'] if 'EventAction' in df.columns else "Clic"
            df['Ventana_Detalle'] = df['WindowText'] if 'WindowText' in df.columns else ""

            # Limpieza y ordenamiento cronológico de auditoría interna
            df = df.dropna(subset=['Fecha_Hora'])
            df = df.sort_values(by='Fecha_Hora', ascending=False)
            
            return df
        else:
            st.error(f"⚠️ Google Drive rechazó la descarga. Código HTTP: {respuesta.status_code}")
            return None
            
    except Exception as e:
        st.error(f"⚠️ Error crítico de conexión al absorber base de datos en Google Drive: {e}")
        return None
