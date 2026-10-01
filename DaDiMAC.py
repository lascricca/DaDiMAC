# DaDiMAC.py
import streamlit as st
import pandas as pd
from datetime import datetime

# IMPORTACIÓN DE LOS MÓDULOS DEL PROYECTO
import conexion
import interfaz
import usuarios  # Módulo de Autenticación con Firebase

# Configuración inicial de la interfaz
st.set_page_config(page_title="Dashboard DaDiMAC", layout="wide", initial_sidebar_state="expanded")

# Bloqueo Máster de Seguridad con Firebase Auth
if usuarios.login_sidebar():
    st.title("🚀 Bars Dashboard DaDiMAC — Infraestructura Cloud")
    st.info(f"☁️ **Modo Servidor Cloud Activo** | Consultor: {st.session_state.usuario_email}")

    # PASO 1: Carga instantánea de la base unificada en memoria caché
    df_completo = conexion.cargar_datos_vivos_consolidados()

        
    if df_completo is not None and not df_completo.empty:

        # =====================================================================
        # ENCABEZADO DE LA BARRA LATERAL: LOGO DE LA MARCA
        # =====================================================================
        # Si tienes el archivo guardado en tu repositorio de GitHub, usa el nombre del archivo:
        st.sidebar.image("LOGO LASA.gif", width=52, use_container_width=False)
        
        # NOTA: Si prefieres cargarlo desde una dirección web (URL pública), 
        # puedes reemplazar el texto anterior por el enlace directo entre comillas.

        
        # --- FILTRO 1: MULTISELECTOR MÁSTER POR EMPRESA ---
        st.sidebar.header("🏢 1. Filtro por Empresa")
        lista_companias_disponibles = sorted(df_completo['Compañía'].unique())
        
        if "todas_empresas" not in st.session_state:
            st.session_state.todas_empresas = False

        if st.sidebar.button("📦 Seleccionar Todas las Compañías"):
            st.session_state.todas_empresas = True
            st.rerun()
        if st.sidebar.button("🧹 Limpiar Selección"):
            st.session_state.todas_empresas = False
            st.rerun()

        valores_defecto_emp = lista_companias_disponibles if st.session_state.todas_empresas else [lista_companias_disponibles[0]]

        companias_seleccionadas = st.sidebar.multiselect(
            "Selecciona empresas a evaluar:",
            options=lista_companias_disponibles,
            default=valores_defecto_emp
        )
        
        if not companias_seleccionadas:
            st.warning("⚠️ Selecciona al menos una empresa contable en la barra lateral.")
        else:
            df_compania = df_completo[df_completo['Compañía'].isin(companias_seleccionadas)].copy()
            
            # --- FILTRO 2: TEMPORAL ADAPTATIVO ---
            fecha_min_real = df_compania['Fecha_Hora'].min().date()
            fecha_max_real = df_compania['Fecha_Hora'].max().date()
            
            st.sidebar.header("📅 2. Filtro Temporal Adaptativo")
            
            date_range = st.sidebar.date_input(
                "Ajustar Ventana de Consulta", 
                [fecha_min_real, fecha_max_real],
                min_value=fecha_min_real,
                max_value=fecha_max_real
            )
            
            if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
                fecha_inicio, fecha_fin = date_range
            else:
                fecha_inicio, fecha_fin = fecha_min_real, fecha_max_real
                
            # --- FILTRO 3: OPERADORES CONTABLES DETECTADOS ---
            st.sidebar.header("👤 3. Filtro por Personal")
            lista_usuarios_disponibles = sorted(df_compania['Usuario'].unique())
            
            usuarios_seleccionados = st.sidebar.multiselect(
                "Selecciona operadores:",
                options=lista_usuarios_disponibles,
                default=lista_usuarios_disponibles
            )
            
            df_filtrado_fechas = df_compania[
                (df_compania['Fecha_Hora'].dt.date >= fecha_inicio) & 
                (df_compania['Fecha_Hora'].dt.date <= fecha_fin)
            ]
            
            if not usuarios_seleccionados:
                df_final_filtrado = df_filtrado_fechas.copy()
            else:
                df_final_filtrado = df_filtrado_fechas[df_filtrado_fechas['Usuario'].isin(usuarios_seleccionados)].copy()
            
            # PASO 2: Envío al renderizador de interfaz.py (mantiene la campana de Gauss, línea de media, ránkings y tabla)
            if not df_final_filtrado.empty:
                interfaz.renderizar_dashboard(df_final_filtrado, fecha_inicio, fecha_fin, df_csv_origen=df_completo)
            else:
                st.warning("⚠️ No se localizaron movimientos contables para los criterios seleccionadas.")
    else:
        st.warning("⚠️ El archivo 'DaDiMAC_ExtraeCSV.csv' está vacío o desincronizado.")
else:
    # Mensaje elegante cuando la aplicación está totalmente bloqueada en la nube
    st.title("🔒 Plataforma de Auditoría Contable DaDiMAC")
    st.info("Introduce tus credenciales autorizadas en el panel izquierdo para acceder. Si es tu primera vez o perdiste tu acceso, puedes registrarte o usar el botón de restablecimiento automático.")
