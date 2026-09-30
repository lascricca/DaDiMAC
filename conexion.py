import io
import requests
import streamlit as st
import pandas as pd
import csv

# =====================================================================
# CONFIGURACIÓN CLOUD: RUTA ESTÁTICA DIRECTA A TU GOOGLE DRIVE
# =====================================================================
URL_DESCARGA_DIRECTA = "https://google.com"

@st.cache_data(ttl=1800)  # Conserva en memoria RAM por 30 minutos para velocidad máxima
def cargar_datos_vivos_consolidados():
    """
    Descarga el archivo masivo usando 'requests' y lo procesa con un motor 
    tolerante a fallos de comillas dobles y caracteres especiales en los textos de Sage 50.
    """
    try:
        # Petición HTTP directa a los servidores de Google Drive
        respuesta = requests.get(URL_DESCARGA_DIRECTA, timeout=45)
        
        if respuesta.status_code == 200:
            # Transmutamos el texto descargado en un flujo de memoria para Pandas
            objeto_memoria = io.StringIO(respuesta.text)
            
            # MOTOR REPARADO: Se configura quoting=csv.QUOTE_NONE para que las comillas
            # dentro de las descripciones de las ventanas no rompan las columnas.
            df = pd.read_csv(
                objeto_memoria, 
                sep=None, 
                engine='python',
                quoting=csv.QUOTE_NONE,
                on_bad_lines='skip'  # Si hay alguna línea corrupta insalvable, la salta en lugar de colapsar
            )
            
            # Limpieza rápida de comillas residuales en los nombres de las columnas si existieran
            df.columns = df.columns.str.replace('"', '').str.strip()
            
            # Mapeo y tipificación obligatoria de columnas contables
            if 'Date_Time' in df.columns:
                df['Fecha_Hora'] = pd.to_datetime(df['Date_Time'].astype(str).str.replace('"', ''), errors='coerce')
            elif 'Fecha_Hora' in df.columns:
                df['Fecha_Hora'] = pd.to_datetime(df['Fecha_Hora'].astype(str).str.replace('"', ''), errors='coerce')
            else:
                df['Fecha_Hora'] = pd.to_datetime(df.iloc[:, 0].astype(str).str.replace('"', ''), errors='coerce')

            # Homologación estructural de nombres para el orquestador y la interfaz
            df['Compañía'] = df['CompanyName'].astype(str).str.replace('"', '') if 'CompanyName' in df.columns else (df['Compañía'] if 'Compañía' in df.columns else "Sin Compañía")
            df['Usuario'] = df['UserID'].astype(str).str.replace('"', '') if 'UserID' in df.columns else (df['Usuario'] if 'Usuario' in df.columns else "Desconocido")
            df['Monto'] = pd.to_numeric(df['MainAmt'].astype(str).str.replace('"', ''), errors='coerce').fillna(0.0) if 'MainAmt' in df.columns else 0.0
            df['Acción'] = df['EventAction'].astype(str).str.replace('"', '') if 'EventAction' in df.columns else "Clic"
            df['Ventana_Detalle'] = df['WindowText'].astype(str).str.replace('"', '') if 'WindowText' in df.columns else ""

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
