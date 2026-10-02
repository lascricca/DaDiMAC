# DaDiMAC.py
import streamlit as st
import pandas as pd
from datetime import datetime

# IMPORTACIÓN DE LOS MÓDULOS DEL PROYECTO
import conexion
import interfaz
import usuarios  # Módulo de Autenticación con Firebase

# =====================================================================
# BLINDAJE INTERACTIVO GLOBAL: CONGELAMIENTO AL TACTO Y MOUSE
# =====================================================================
st.markdown(
    """
    <style>
    /* Bloquea la interacción del mouse y gestos táctiles en los contenedores de gráficos */
    .grafico-estatico {
        pointer-events: none;
        user-select: none;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Configuración inicial de la interfaz
st.set_page_config(page_title="Dashboard DaDiMAC", layout="wide", initial_sidebar_state="expanded")


# Bloqueo Máster de Seguridad con Firebase Auth
if usuarios.login_sidebar():
    # =====================================================================
    # ENCABEZADO DEL DASHBOARD: LOGO SUPERIOR IZQUIERDO Y TÍTULO ABAJO
    # =====================================================================
    # 1. Renderiza primero el logo alineado a la izquierda (Ancho de 156 píxeles)
    st.image("LOGO MAC.jpeg", width=156, use_container_width=False)
    
    # 2. Renderiza el título de la firma justo debajo del logo con tamaño de 42px
    st.markdown('<h2 style="font-size: 42px; margin-top: 15px; margin-bottom: 5px;">Dashboard de Auditoría DaDiMAC - Cloud</h2>', unsafe_allow_html=True)    
    
    st.info(f"☁️ **Modo Servidor Cloud Activo** | Consultor: {st.session_state.usuario_email}")

    # PASO 1: Carga instantánea de la base unificada en memoria caché
    df_completo = conexion.cargar_datos_vivos_consolidados()

        
    if df_completo is not None and not df_completo.empty:

        # =====================================================================
        # ENCABEZADO DE LA BARRA LATERAL: LOGO DE LA MARCA
        # =====================================================================
        st.sidebar.image("LOGO LASA.gif", width=104, use_container_width=False)
        st.sidebar.markdown("### L.A. Scricca Asesores, S.A.")
        
        # --- FILTRO 1: MULTISELECTOR MÁSTER POR EMPRESA (INTERFAZ OPTIMIZADA)
        st.sidebar.header("🏢 1. Filtro por Empresa")
        lista_companias_disponibles = sorted(df_completo['Compañía'].unique())
        
        # Por defecto cargamos la primera compañía para mantener la UI activa de forma elegante
        valores_defecto_emp = [lista_companias_disponibles[0]] if lista_companias_disponibles else []

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
            
            # PASO 2: Envío al renderizador de interfaz.py protegido por el escudo de congelamiento
            if not df_final_filtrado.empty:
                # Abrimos el contenedor invisible que bloquea la interacción del mouse y pantallas táctiles
                st.markdown('<div class="grafico-estatico">', unsafe_allow_html=True)
            
                # Tu llamada original a interfaz.py permanece completamente intacta y operativa
                interfaz.renderizar_dashboard(df_final_filtrado, fecha_inicio, fecha_fin, df_csv_origen=df_completo)
            
                # Cerramos el escudo de protección
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.warning("⚠️ No se localizaron movimientos contables para los criterios seleccionadas.")

    else:
        st.warning("⚠️ El archivo 'DaDiMAC_ExtraeCSV.csv' está vacío o desincronizado.")
else:
    # Mensaje elegante cuando la aplicación está totalmente bloqueada en la nube
    st.title("🔒 Plataforma de Auditoría Contable DaDiMAC")
    st.info("Introduce tus credenciales autorizadas en el panel izquierdo para acceder. Si es tu primera vez o perdiste tu acceso, puedes registrarte o usar el botón de restablecimiento automático.")
    
    # =====================================================================
    # INYECCIÓN DE FONDO DE PANTALLA EXCLUSIVO DESDE TU REPOSITORIO GITHUB
    # =====================================================================
    # URL Cruda corregida con el subdominio 'raw' para lectura directa de Streamlit
    URL_FONDO_GITHUB = "https://github.com/lascricca/DaDiMAC/blob/main/Ejecutivos.jpg?raw=true" 
    
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: linear-gradient(rgba(0, 0, 0, 0.55), rgba(0, 0, 0, 0.55)), url("{URL_FONDO_GITHUB}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        /* Estilización de los inputs de la barra de login para alto contraste */
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p, 
        [data-testid="stSidebar"] label {{
            color: #FFFFFF !important;
            font-weight: bold !important;
            text-shadow: 1px 1px 3px rgba(0,0,0,0.8);
        }}
        </style>
        """,
        unsafe_allow_html=True
    )
