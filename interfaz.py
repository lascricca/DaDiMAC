import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

def renderizar_dashboard(df_filtrado, fecha_inicio, fecha_fin, df_csv_origen=None):
    total_movimientos_filtrados = len(df_filtrado)
    usuarios_unicos = df_filtrado['Usuario'].nunique()
    companias_activas = df_filtrado['Compañía'].nunique()
    suma_dinero_total = df_filtrado['Monto'].sum() if 'Monto' in df_filtrado.columns else 0.0
    
    if df_csv_origen is not None:
        total_registros_globales = len(df_csv_origen)
    else:
        total_registros_globales = total_movimientos_filtrados

    df_filtrado['Hora_Decimal'] = df_filtrado['Fecha_Hora'].dt.hour + df_filtrado['Fecha_Hora'].dt.minute / 60.0
    datos_horas = df_filtrado['Hora_Decimal'].dropna().values

    media_matematica = 12.0
    desviacion_estandar = 2.5
    texto_hora_pico = "Sin datos"
    texto_desviacion = "0.00 Hrs"
    
    if len(datos_horas) > 0:
        media_matematica = float(np.mean(datos_horas))
        desviacion_estandar = float(np.std(datos_horas))
        if desviacion_estandar == 0: 
            desviacion_estandar = 0.1
            
        horas_int = int(media_matematica)
        minutos_int = int((media_matematica - horas_int) * 60)
        texto_hora_pico = f"{horas_int:02d}:{minutos_int:02d} Hrs"
        
        horas_desv = int(desviacion_estandar)
        minutos_desv = int((desviacion_estandar - horas_desv) * 60)
        texto_desviacion = f"± {horas_desv}h {minutos_desv}m"

    df_madrugada = df_filtrado[(df_filtrado['Fecha_Hora'].dt.hour >= 0) & (df_filtrado['Fecha_Hora'].dt.hour < 6)]
    clics_madrugada = len(df_madrugada)
    
    if total_movimientos_filtrados > 0:
        porcentaje_madrugada = (clics_madrugada / total_movimientos_filtrados * 100)
    else:
        porcentaje_madrugada = 0.0

    # Estilos CSS compactos para las métricas superiores
    st.markdown("""
        <style>
        [data-testid="stMetricValue"] { font-size: 24px !important; font-weight: bold; }
        [data-testid="stMetricLabel"] { font-size: 13px !important; }
        </style>
    """, unsafe_allow_html=True)

    # PORTADA DE KPIS UNIFICADA Y COMPACTA (Fila 1: Operación y Volumen)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label="🎯 Clics / Universo Total", value=f"{total_movimientos_filtrados:,}", delta=f"De {total_registros_globales:,} globales")
    with col2:
        st.metric(label="🏢 Empresas Activas", value=f"{companias_activas:,}")
    with col3:
        st.metric(label="👤 Usuarios Operadores", value=f"{usuarios_unicos:,}")
    with col4:
        st.metric(label="💰 Volumen Financiero", value=f"${suma_dinero_total:,.2f}")

    # PORTADA DE KPIS UNIFICADA Y COMPACTA (Fila 2: Estadística y Seguridad)
    col5, col6, col7, col8 = st.columns(4)
    with col5:
        st.metric(label="🕒 Hora Pico Promedio", value=texto_hora_pico)
    with col6:
        st.metric(label="📊 Desviación Estándar", value=texto_desviacion)
    with col7:
        st.metric(label="🚨 Clics Nocturnos (00-06)", value=f"{clics_madrugada:,}", delta=f"{porcentaje_madrugada:.1f}% del total", delta_color="inverse")
    with col8:
        variacion_porcentual = (desviacion_estandar / media_matematica * 100) if media_matematica > 0 else 0.0
        st.metric(label="📉 Coeficiente Variación", value=f"{variacion_porcentual:.1f}%")

    st.markdown("---")

    # PORTADA UNIFICADA: FLUJO VERTICAL SECUENCIAL
    st.markdown("### 📈 Portada Analítica Avanzada (Horarios, Ránkings y Dinero)")
    
    # 1. Gráfico de Campana de Gauss (Ancho completo con Línea de la Media)
    if len(datos_horas) > 5:
        try:
            eje_x_horas = np.linspace(0, 23.99, 500)
            pdf_gauss = (1.0 / (desviacion_estandar * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((eje_x_horas - media_matematica) / desviacion_estandar)**2)
            
            fig_gauss = go.Figure()
            fig_gauss.add_trace(go.Scatter(x=eje_x_horas, y=pdf_gauss, mode='lines', name='Densidad Probabilística', line=dict(color='#2678FE', width=2)))
            
            lim_inf = media_matematica - desviacion_estandar
            lim_sup = media_matematica + desviacion_estandar
            x_somb = eje_x_horas[(eje_x_horas >= lim_inf) & (eje_x_horas <= lim_sup)]
            y_somb = pdf_gauss[(eje_x_horas >= lim_inf) & (eje_x_horas <= lim_sup)]
            
            fig_gauss.add_trace(go.Scatter(
                x=x_somb, y=y_somb, mode='none', fill='tozeroy', 
                fillcolor='rgba(38, 120, 254, 0.25)', 
                name='Zona Primaria (68% de los Clics)'
            ))
            
            # INYECCIÓN MÁSTER: Línea discontinua vertical en el punto más alto (Media)
            fig_gauss.add_vline(
                x=media_matematica, 
                line_width=2, 
                line_dash="dash", 
                line_color="#4A4A4A",
                annotation_text=f" Hora Pico ({texto_hora_pico})",
                annotation_position="top right"
            )
            
            fig_gauss.update_layout(
                title="Distribución Horaria del Esfuerzo Laboral (Campana de Gauss)",
                xaxis_title="Hora del Día (0:00 - 23:59 Hrs)",
                yaxis_title="Concentración (%)",
                xaxis=dict(tickmode='array', tickvals=list(range(0, 25, 2)), range=[0, 23.99], fixedrange=True),
                yaxis=dict(tickformat='.0%', minallowed=0, fixedrange=True),
                hovermode=False,
                template="plotly_white", height=340,
                margin=dict(l=40, r=40, t=40, b=40),
                legend=dict(orientation="h", y=-0.25)
            )
            st.plotly_chart(fig_gauss, use_container_width=True, config={'displayModeBar': False, 'staticPlot': True})
        except Exception as e:
            st.error(f"⚠️ Error en Gauss: {e}")

    st.markdown("---")

    # 2. Ránking de Compañías
    st.subheader("🏢 Distribución de Actividad por Firma")
    top_companies = df_filtrado['Compañía'].value_counts().reset_index()
    top_companies.columns = ['Compañía', 'Clics']
    top10_comp = top_companies.head(10).sort_values(by='Clics', ascending=True)
    
    fig_top_comp = px.bar(
        top10_comp, x='Clics', y='Compañía', orientation='h',
        title="Top 10 Empresas más Activas",
        labels={'Clics': 'Cantidad de Movimientos', 'Compañía': 'Razón Social'},
        color_continuous_scale='Blues', color='Clics'
    )
    fig_top_comp.update_layout(
        xaxis=dict(fixedrange=True),
        yaxis=dict(fixedrange=True),
        hovermode=False,
        template="plotly_white", height=380, margin=dict(l=20, r=20, t=40, b=20), showlegend=False
    )
    st.plotly_chart(fig_top_comp, use_container_width=True, config={'displayModeBar': False, 'staticPlot': True})

    st.markdown("---")

    # 3. Ránking de Usuarios
    st.subheader("👤 Rendimiento del Personal Contable")
    top_users = df_filtrado['Usuario'].value_counts().reset_index()
    top_users.columns = ['Usuario', 'Clics']
    top10_user = top_users.head(10).sort_values(by='Clics', ascending=True)
    
    fig_top_user = px.bar(
        top10_user, x='Clics', y='Usuario', orientation='h',
        title="Top 10 Usuarios Operativos",
        labels={'Clics': 'Cantidad de Movimientos', 'Usuario': 'Identificador de Operador'},
        color_discrete_sequence=['#FF4B4B']
    )
    fig_top_user.update_layout(
        xaxis=dict(fixedrange=True),
        yaxis=dict(fixedrange=True),
        hovermode=False,
        template="plotly_white", height=380, margin=dict(l=20, r=20, t=40, b=20)
    )
    st.plotly_chart(fig_top_user, use_container_width=True, config={'displayModeBar': False, 'staticPlot': True})

    st.markdown("---")

    # 4. Gráfico de volumen financiero MainAmt
    if 'Monto' in df_filtrado.columns and df_filtrado['Monto'].sum() > 0:
        st.subheader("💰 Distribución Financiera de Operaciones")
        df_monetario = df_filtrado.groupby('Compañía')['Monto'].sum().reset_index()
        df_monetario = df_monetario.sort_values(by='Monto', ascending=False).head(10)
        
        fig_monetario = px.bar(
            df_monetario, x='Compañía', y='Monto',
            title="Volumen Monetario Total por Firma ($ MainAmt)",
            labels={'Monto': 'Suma Monetaria ($)', 'Compañía': 'Empresa'},
            text_auto='.2s', color_discrete_sequence=['#2CA02C']
        )
        fig_monetario.update_layout(
            xaxis=dict(fixedrange=True, tickangle=-25),
            yaxis=dict(fixedrange=True),
            hovermode=False,
            template="plotly_white", height=380, margin=dict(l=20, r=20, t=40, b=40)
        )
        st.plotly_chart(fig_monetario, use_container_width=True, config={'displayModeBar': False, 'staticPlot': True})
        st.markdown("---")

    # 5. TABLA INTERACTIVA DE DATOS AL FINAL DE LA CASCADA
    st.subheader("🔍 Auditor de Registros Detallados (Data In-Depth)")
    st.markdown("Usa la barra superior de la tabla para buscar términos, ordenar columnas o expandir transacciones específicas:")
    
    # Preparamos un DataFrame limpio y ordenado para no saturar visualmente
    columnas_visibles = ['Fecha_Hora', 'Compañía', 'Usuario', 'Acción', 'Monto', 'Ventana_Detalle']
    df_tabla_interactiva = df_filtrado[[c for c in columnas_visibles if c in df_filtrado.columns]].copy()
    
    if not df_tabla_interactiva.empty:
        # Formateamos la columna Fecha_Hora para visualización ejecutiva limpia
        df_tabla_interactiva['Fecha_Hora'] = df_tabla_interactiva['Fecha_Hora'].dt.strftime('%Y-%m-%d %H:%M:%S')
        if 'Monto' in df_tabla_interactiva.columns:
            df_tabla_interactiva['Monto'] = df_tabla_interactiva['Monto'].map(lambda x: f"${x:,.2f}")
            
        st.dataframe(df_tabla_interactiva, use_container_width=True, hide_index=True)
    else:
        st.info("ℹ️ No hay registros detallados disponibles para mostrar.")
