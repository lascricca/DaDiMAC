# conexion.py
import os
import pandas as pd
import streamlit as st

# RUTA DEFINITIVA DEL ARCHIVO LOCAL REESTRUCTURADO
RUTA_LOCAL_CSV = r"C:\Users\Luciano\Google Drive\LASA Panama\MAC - Proyectos\MAC - 1 Principal\DADISAGE\DaDiMAC - carpeta en servidor SRV-MAC\DaDiMAC_ExtraeCSV.csv"

def cargar_datos_vivos_consolidados():
    """
    ABSORBEDOR ASILADO LOCAL: Lee el archivo consolidado usando punto y coma (;) como delimitador.
    Mapea de forma directa las cabeceras validadas en la inspección estructural.
    """
    if not os.path.exists(RUTA_LOCAL_CSV):
        st.error(f"❌ Archivo maestro ausente: No se localizó 'DaDiMAC_ExtraeCSV.csv' en la ruta local:\n   {RUTA_LOCAL_CSV}")
        return pd.DataFrame()

    try:
        # Cargamos el CSV forzando el separador por punto y coma (;) verificado
        df_csv = pd.read_csv(RUTA_LOCAL_CSV, sep=';', encoding='utf-8', quotechar='"')
        
        # Sanitización estricta de nombres de columnas (remueve espacios y caracteres ocultos como BOM)
        df_csv.columns = df_csv.columns.str.replace('"', '').str.strip()
        # Reparación específica por si la cadena trae el carácter BOM de bytes de Windows
        df_csv.rename(columns={df_csv.columns[0]: 'Ruta'}, inplace=True)

        # Construcción de la matriz unificada limpia para la interfaz gráfica
        df_final = pd.DataFrame()
        
        # 1. PARSEO CRONOLÓGICO DIRECTO: Consumimos la columna 'TimeStamp' ya procesada
        df_final['Fecha_Hora'] = pd.to_datetime(df_csv['TimeStamp'], errors='coerce')
        
        # 2. CAPTURA DE EMPRESA COMERCIAL: Almacenamos el nombre real para los filtros de Streamlit
        df_final['Compañía'] = df_csv['CompanyName'].fillna('Sin Nombre Comercial').astype(str).str.strip()
        df_final['CompanyDBN'] = df_csv['CompanyDBN'].fillna('SIN_ID').astype(str).str.strip()
        
        # 3. PERSONAL CONTABLE: Homologamos los nombres de usuario a minúsculas limpias
        df_final['Usuario'] = df_csv['UserID'].fillna('sistema / odbc').astype(str).str.strip().str.lower()
        df_final.loc[df_final['Usuario'] == 'not available', 'Usuario'] = 'sistema / odbc'
        
        # 4. TRADUCCIÓN DE CÓDIGOS DE ACCIÓN (Sage 50 nativo): Consumimos la columna 'Action'
        df_csv['Action_Num'] = pd.to_numeric(df_csv['Action'], errors='coerce').fillna(0).astype(int)
        mapeo_codigos = {1: "Guardó Transacción", 2: "Modificó Transacción", 3: "Eliminó Transacción", 4: "Inició Sesión", 5: "Cerró Sesión"}
        df_final['Acción'] = df_csv['Action_Num'].map(mapeo_codigos).fillna("Operación Contable")
        
        # 5. UNIFICACIÓN DE DETALLE EN VENTANA: Combinamos la acción con la descripción y referencias
        ventana_limpia = df_csv['Description'].fillna('').astype(str).str.strip()
        ref_limpia = df_csv['Reference'].fillna('').astype(str).str.strip()
        trans_limpia = df_csv['TransID'].fillna('').astype(str).str.strip()
        
        df_final['Ventana_Detalle'] = (ventana_limpia + " / " + ref_limpia + " / " + trans_limpia).str.strip(" / ")
        df_final.loc[df_final['Ventana_Detalle'] == '', 'Ventana_Detalle'] = 'Auditoría de Sistema / Registro Pasivo'

        # 6. EXTRACCIÓN MONETARIA: Limpieza y parseo de montos financieros de transacciones
        if 'MainAmt' in df_csv.columns:
            df_final['Monto'] = pd.to_numeric(df_csv['MainAmt'], errors='coerce').fillna(0.0)
        else:
            df_final['Monto'] = 0.0

        
        # Devolvemos el set limpio ordenado cronológicamente desde la transacción más reciente
        return df_final.dropna(subset=['Fecha_Hora']).sort_values(by='Fecha_Hora', ascending=False)
        
    except Exception as e:
        st.error(f"❌ Error al procesar la estructura del archivo CSV estructurado: {e}")
        return pd.DataFrame()
