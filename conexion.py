import io
import requests
import streamlit as st
import pandas as pd

# =====================================================================
# CONFIGURACIÓN CLOUD DEFINITIVA: DECODIFICACIÓN EPOCH SAGE PEACHTREE
# =====================================================================
URL_FIREBASE_STORAGE = "https://firebasestorage.googleapis.com/v0/b/dadimac-62fd6.firebasestorage.app/o/DaDiMAC_ExtraeCSV.csv?alt=media&token=669de119-c19c-4946-9b11-305714951df4"

def validar_y_convertir_epoch_sage(df_crudo):
    """
    Convierte matemáticamente los segundos enteros de Sage Peachtree a DateTime real
    sumando el offset desde 01/01/1970. Si detecta fallas, genera un reporte de filas.
    """
    # Guardamos la posición original de la fila física (Pandas base 0 + 2 por el encabezado del CSV)
    df_crudo['Fila_Excel'] = df_crudo.index + 2
    
    # Asegurar consistencia en el nombre de la columna independientemente de las mayúsculas
    df_crudo.rename(columns=lambda x: 'timestampraw' if x.lower() == 'timestampraw' else x, inplace=True)

    # Forzamos la conversión a valores numéricos (segundos enteros de Sage)
    segundos_sage = pd.to_numeric(df_crudo['timestampraw'], errors='coerce')
    
    # 1. Detectar filas donde el valor no es un número entero convertible (textos, vacíos, etc.)
    mascara_nan = segundos_sage.isna()
    
    # 2. Convertir temporalmente a DateTime las filas válidas para analizar coherencia temporal
    fechas_convertidas = pd.to_datetime(segundos_sage, unit='s', errors='coerce')
    
    # Detectar fechas fuera del rango lógico operativo de la firma (Años 2000 a 2026)
    anio_actual = pd.Timestamp.now().year
    mascara_anio_invalido = (fechas_convertidas.dt.year < 2000) | (fechas_convertidas.dt.year > anio_actual)
    
    # Consolidamos las filas corruptas
    df_corruptos = df_crudo[mascara_nan | (mascara_anio_invalido & ~mascara_nan)]
    
    if not df_corruptos.empty:
        st.error("### 🛑 Control de Calidad DaDiMAC: Registros Corruptos Detectados")
        st.warning(
            f"Se han localizado **{len(df_corruptos)} filas** en el archivo con datos corruptos "
            f"en la columna 'timestampraw' que impiden calcular la fecha exacta."
        )
        
        # Estructuramos el reporte con la posición de la fila física para el auditor
        reporte = pd.DataFrame({
            'Fila Física (Excel/CSV)': df_corruptos['Fila_Excel'],
            'Valor Encontrado (SAGE Seconds)': df_corruptos['timestampraw'],
            'Compañía': df_corruptos['companyname'] if 'companyname' in df_corruptos.columns else "N/A",
            'Usuario': df_corruptos['userid'] if 'userid' in df_corruptos.columns else "N/A"
        })
        
        st.dataframe(reporte.sort_values(by='Fila Física (Excel/CSV)'), use_container_width=True)
        st.info("💡 **Acción requerida:** Modifique o elimine estas posiciones directamente en su archivo original de Sage antes de continuar.")
        st.stop()  # Congela la carga de la UI de forma limpia para evitar fugas o descalces de memoria
        
    # Si la validación es exitosa, inyectamos la transformación matemática definitiva
    return fechas_convertidas

@st.cache_data(ttl=1800)  # Mantiene la base de datos en caché por 30 minutos
def cargar_datos_vivos_consolidados():
    """
    Descarga el archivo analítico masivo de clics desde Firebase Storage
    y ejecuta obligatoriamente el módulo de conversión y validación Epoch.
    """
    try:
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
                
            # Homologación total de columnas a minúsculas
            df.columns = df.columns.str.replace('"', '').str.strip().str.lower()
            
            # PROCESAMIENTO MATEMÁTICO: Transformación de segundos Unix de Sage Peachtree
            df['Fecha_Hora'] = validar_y_convertir_epoch_sage(df)
            
            # Homologación de variables para la interfaz gráfica
            df['Compañía'] = df['companyname'] if 'companyname' in df.columns else (df['compañía'] if 'compañía' in df.columns else "Sin Compañía")
            df['Usuario'] = df['userid'] if 'userid' in df.columns else (df['usuario'] if 'usuario' in df.columns else "Desconocido")
            df['Monto'] = pd.to_numeric(df['mainamt'], errors='coerce').fillna(0.0) if 'mainamt' in df.columns else 0.0
            df['Acción'] = df['eventaction'] if 'eventaction' in df.columns else "Clic"
            df['Ventana_Detalle'] = df['windowtext'] if 'windowtext' in df.columns else ""

            df = df.sort_values(by='Fecha_Hora', ascending=False)
            return df
        else:
            st.error(f"⚠️ Firebase Storage rechazó la descarga. Código HTTP: {respuesta.status_code}. Es altamente probable que requieras copiar una Download URL fresca desde la consola.")
            return None
            
    except Exception as e:
        st.error(f"⚠️ Error crítico de conexión al absorber base de datos en Firebase: {e}")
        return None
