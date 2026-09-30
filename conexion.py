import io
import requests
import streamlit as st
import pandas as pd

# =====================================================================
# EXTRACTOR CLOUD HÍBRIDO CON MULTI-CANAL DE CONTINGENCIA (GOOGLE DRIVE)
# =====================================================================
ID_DOCUMENTO_DRIVE = "1X1vKvJIA4ymt_iPeeXlYDTPE0dzFoZbl"

# Canal A: Exportación estándar para archivos subidos como texto plano (CSV)
URL_CANAL_A = f"https://google.com{ID_DOCUMENTO_DRIVE}/export?format=csv"

# Canal B: Exportación forzada de hoja de cálculo nativa (Google Sheets) a nivel binario
URL_CANAL_B = f"https://google.com{ID_DOCUMENTO_DRIVE}/export?format=csv&id={ID_DOCUMENTO_DRIVE}&gid=0"

@st.cache_data(ttl=900)  # Reduce el tiempo de caché a 15 minutos para acelerar la sincronización en caliente
def cargar_datos_vivos_consolidados():
    """
    Descarga el archivo analítico aplicando un algoritmo de conmutación por error
    para neutralizar cualquier alteración de formato provocada por Google Drive.
    """
    df = None
    
    # --- INTENTO 1: CANAL A (TEXTO PLANO STANDARD) ---
    try:
        respuesta = requests.get(URL_CANAL_A, timeout=45)
        if respuesta.status_code == 200 and len(respuesta.text) > 500:
            objeto_memoria = io.StringIO(respuesta.text)
            df = pd.read_csv(objeto_memoria, sep=None, engine='python', on_bad_lines='skip')
    except:
        pass

    # --- INTENTO 2: CANAL B (CONMUTACIÓN POR ERROR - HOJA NATIVA BINARIA) ---
    if df is None or df.empty or len(df.columns) < 2:
        try:
            respuesta = requests.get(URL_CANAL_B, timeout=45)
            if respuesta.status_code == 200:
                objeto_memoria = io.StringIO(respuesta.text)
                df = pd.read_csv(objeto_memoria, sep=None, engine='python', on_bad_lines='skip')
        except Exception as e:
            st.error(f"⚠️ Falla crítica en los canales de contingencia de red: {e}")
            return None

    # --- VALIDACIÓN FINAL DE LA BASE DE DATOS CONTABLE ---
    if df is None or df.empty or len(df.columns) < 2:
        return None  # Si ambos canales fallan, mantiene la alerta amarilla de control activo

    # --- PROCESAMIENTO Y ESTANDARIZACIÓN DE COLUMNAS SAGE 50 ---
    try:
        # Limpieza de impurezas en los nombres de las cabeceras
        df.columns = df.columns.str.replace('"', '').str.strip()
        
        # Mapeo y tipificación cronológica obligatoria
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

        # Depuración final de registros corruptos o vacíos
        df = df.dropna(subset=['Fecha_Hora'])
        df = df.sort_values(by='Fecha_Hora', ascending=False)
        
        return df
        
    except Exception as e:
        st.error(f"⚠️ Error en el mapeo de columnas del archivo de auditoría: {e}")
        return None
