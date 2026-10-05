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
        if desviacion_estandar == 0: desviacion_estandar = 0.1
            
        horas_int = int(media_matematica)
        minutos_int = int((media_matematica - horas_int) * 60)
        texto_hora_pico = f"{horas_int:02d}:{minutos_int:02d} Hrs"
        
        horas_desv = int(desviacion_estandar)
        minutos_desv = int((desviacion_estandar - horas_desv) * 60)
        texto_desviacion = f"± {horas_desv}h {minutos_desv}m"

    df_madrugada = df_filtrado[(df_filtrado['Fecha_Hora'].dt.hour >= 0) & (df_filtrado['Fecha_Hora'].dt.hour < 6)]
    clics_madrugada = len(df_madrugada)
    porcentaje_madrugada = (clics_madrugada / total_movimientos_filtrados * 100) if total_movimientos_filtrados > 0 else 0.0

    st.markdown("""
        <style>
        [data-testid="stMetricValue"] { font-size: 24px !important; font-weight: bold; }
        [data-testid="stMetricLabel"] { font-size: 13px !important; }
        </style>
    """, unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric(label="🎯 Clics / Universo Total", value=f"{total_movimientos_filtrados:,}", delta=f"De {total_registros_globales:,} globales")
    with col2: st.metric(label="🏢 Empresas Activas", value=f"{companias_activas:,}")
    with col3: st.metric(label="👤 Usuarios Operadores", value=f"{usuarios_unicos:,}")
    with col4: st.metric(label="💰 Volumen Financiero", value=f"${suma_dinero_total:,.2f}")

    col5, col6, col7, col8 = st.columns(4)
    with col5: st.metric(label="🕒 Hora Pico Promedio", value=texto_hora_pico)
    with col6: st.metric(label="📊 Desviación Estándar", value=texto_desviacion)
    with col7: st.metric(label="🚨 Clics Nocturnos (00-06)", value=f"{clics_madrugada:,}", delta=f"{porcentaje_madrugada:.1f}% del total", delta_color="inverse")
    with col8:
        variacion_porcentual = (desviacion_estandar / media_matematica * 100) if media_matematica > 0 else 0.0
        st.metric(label="📉 Coeficiente Variación", value=f"{variacion_porcentual:.1f}%")

    st.markdown("---")

    st.subheader("🏢 Distribución de Actividad por Empresa")
    top_companies = df_filtrado['Compañía'].value_counts().reset_index()
    top_companies.columns = ['Compañía', 'Clics']
    top10_comp = top_companies.head(10).sort_values(by='Clics', ascending=True)
    
    top10_comp['Texto_Clics'] = top10_comp['Clics'].map(lambda x: f"{x:,}")
    fig_top_comp = px.bar(top10_comp, x='Clics', y='Compañía', orientation='h', title="Top 10 Empresas más Activas", labels={'Clics': 'Cantidad de Movimientos', 'Compañía': 'Razón Social'}, color_continuous_scale='Blues', color='Clics', text='Texto_Clics')
    fig_top_comp.update_layout(xaxis=dict(fixedrange=True), yaxis=dict(fixedrange=True), hovermode=False, template="plotly_white", height=380, margin=dict(l=20, r=20, t=40, b=20), showlegend=False)
    fig_top_comp.update_traces(textposition='inside', textfont=dict(color='#FF0000', size=12, weight='bold'), cliponaxis=False)
    st.plotly_chart(fig_top_comp, use_container_width=True, config={'displayModeBar': False, 'staticPlot': True})

    st.markdown("---")

    st.subheader("👤 Rendimiento del Personal Contable")
    top_users = df_filtrado['Usuario'].value_counts().reset_index()
    top_users.columns = ['Usuario', 'Clics']
    top10_user = top_users.head(10).sort_values(by='Clics', ascending=True)
    
    top10_user['Texto_Clics'] = top10_user['Clics'].map(lambda x: f"{x:,}")
    fig_top_user = px.bar(top10_user, x='Clics', y='Usuario', orientation='h', title="Top 10 Usuarios Operativos", labels={'Clics': 'Cantidad de Movimientos', 'Usuario': 'Identificador de Operador'}, color_discrete_sequence=['#FF4B4B'], text='Texto_Clics')
    fig_top_user.update_layout(xaxis=dict(fixedrange=True), yaxis=dict(fixedrange=True), hovermode=False, template="plotly_white", height=380, margin=dict(l=20, r=20, t=40, b=20))
    fig_top_user.update_traces(textposition='inside', textfont=dict(color='white', size=12, weight='bold'), cliponaxis=False)
    st.plotly_chart(fig_top_user, use_container_width=True, config={'displayModeBar': False, 'staticPlot': True})

    st.markdown("---")

    if 'Monto' in df_filtrado.columns and df_filtrado['Monto'].sum() > 0:
        st.subheader("💰 Distribución Financiera de Operaciones")
        df_monetario = df_filtrado.groupby('Compañía')['Monto'].sum().reset_index()
        df_monetario = df_monetario.sort_values(by='Monto', ascending=False).head(10)
        
        df_monetario['Texto_Monto'] = df_monetario['Monto'].map(lambda x: f"${x:,.2f}")
        fig_monetario = px.bar(df_monetario, x='Compañía', y='Monto', title="Volumen Monetario Total por Firma ($ MainAmt)", labels={'Monto': 'Suma Monetaria ($)', 'Compañía': 'Empresa'}, text='Texto_Monto')
        fig_monetario.update_layout(xaxis=dict(fixedrange=True, tickangle=-25), yaxis=dict(fixedrange=True), hovermode=False, template="plotly_white", height=380, margin=dict(l=20, r=20, t=40, b=40))
        fig_monetario.update_traces(textposition='outside', textfont=dict(color='white', size=11, weight='bold'), cliponaxis=False, marker_color='#2CA02C')
        st.plotly_chart(fig_monetario, use_container_width=True, config={'displayModeBar': False, 'staticPlot': True})
        st.markdown("---")

    # 4. GRÁFICA DE LÍNEA: CLICS POR MES
    st.subheader("📉 Evolución Cronológica del Esfuerzo Contable")
    try:
        df_linea = df_filtrado.copy()
        df_linea['Mes_Periodo'] = df_linea['Fecha_Hora'].dt.to_period('M')
        df_meses = df_linea.groupby('Mes_Periodo').size().reset_index(name='Cantidad_Clics')
        df_meses['Mes_Texto'] = df_meses['Mes_Periodo'].astype(str)
        df_meses = df_meses.sort_values(by='Mes_Periodo', ascending=True)

        if not df_meses.empty:
            fig_mensual = go.Figure()
            fig_mensual.add_trace(go.Scatter(
                x=df_meses['Mes_Texto'], 
                y=df_meses['Cantidad_Clics'], 
                mode='lines+markers', 
                name='Clics por Mes', 
                line=dict(color='#17A2B8', width=3), 
                marker=dict(size=10, color='#0F6A7A')
            ))
            
            anotaciones_nodos = []
            for k, fila in df_meses.iterrows():
                anotaciones_nodos.append(dict(
                    x=fila['Mes_Texto'],
                    y=fila['Cantidad_Clics'],
                    text=f"{fila['Cantidad_Clics']:,}", 
                    font=dict(color='white', size=11, weight='bold'),
                    showarrow=False,
                    yshift=14 
                ))
            
            fig_mensual.update_layout(
                title="Volumen Mensual Histórico de Clics Procesados en Sage", 
                xaxis_title="Periodo Fiscal (Mes/Año)", 
                yaxis_title="Cantidad Total de Clics", 
                xaxis=dict(type='category', fixedrange=True), 
                yaxis=dict(fixedrange=True, minallowed=0), 
                hovermode=False, 
                template="plotly_white", 
                height=340, 
                margin=dict(l=40, r=40, t=40, b=40),
                annotations=anotaciones_nodos 
            )
            st.plotly_chart(fig_mensual, use_container_width=True, config={'displayModeBar': False, 'staticPlot': True})
        else:
            st.info("ℹ️ Datos temporales insuficientes para trazar la línea de tendencia.")
    except Exception as e:
        st.error(f"⚠️ Error en Análisis Mensual: {e}")

    st.markdown("---")

    # 5. CAMPANA DE GAUSS 
    if len(datos_horas) > 5:
        st.subheader("🕒 Distribución Horaria del Esfuerzo Laboral (Campana de Gauss)")
        try:
            eje_x_horas = np.linspace(0, 23.99, 500)
            pdf_gauss = (1.0 / (desviacion_estandar * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((eje_x_horas - media_matematica) / desviacion_estandar)**2)
            
            fig_gauss = go.Figure()
            fig_gauss.add_trace(go.Scatter(x=eje_x_horas, y=pdf_gauss, mode='lines', name='Densidad Probabilística', line=dict(color='#2678FE', width=2)))
            
            lim_inf = media_matematica - desviacion_estandar
            lim_sup = media_matematica + desviacion_estandar
            x_somb = eje_x_horas[(eje_x_horas >= lim_inf) & (eje_x_horas <= lim_sup)]
            y_somb = pdf_gauss[(eje_x_horas >= lim_inf) & (eje_x_horas <= lim_sup)]
            
            fig_gauss.add_trace(go.Scatter(x=x_somb, y=y_somb, mode='none', fill='tozeroy', fillcolor='rgba(38, 120, 254, 0.25)', name='Zona Primaria (68% de los Clics)'))
            fig_gauss.add_vline(x=media_matematica, line_width=2, line_dash="dash", line_color="#4A4A4A", annotation_text=f" Hora Pico ({texto_hora_pico})", annotation_position="top right")
            
            fig_gauss.update_layout(xaxis_title="Hora del Día (0:00 - 23:59 Hrs)", yaxis_title="Concentración (%)", xaxis=dict(tickmode='array', tickvals=list(range(0, 25, 2)), range=[0, 23.99], fixedrange=True), yaxis=dict(tickformat='.0%', minallowed=0, fixedrange=True), hovermode=False, template="plotly_white", height=340, margin=dict(l=40, r=40, t=40, b=40), legend=dict(orientation="h", y=-0.25))
            st.plotly_chart(fig_gauss, use_container_width=True, config={'displayModeBar': False, 'staticPlot': True})
        except Exception as e:
            st.error(f"⚠️ Error en Gauss: {e}")

    st.markdown("---")

    # =====================================================================
    # 6. TABLA INTERACTIVA DE DATOS DE AUDITORÍA (BLOQUEO DE DESCARGAS)
    # =====================================================================
    # st.subheader("🔍 Auditor de Registros Detallados (Data In-Depth)")
    # st.markdown("Usa la barra superior de la tabla para buscar términos, ordenar columnas o expandir transacciones:")
    
    # # REINCORPORACIÓN SECUENCIAL: Ubicamos 'Referencia' exactamente después de 'Monto'
    # columnas_visibles = ['Fecha_Hora', 'Compañía', 'Usuario', 'Acción', 'Monto', 'Referencia', 'Ventana_Detalle']
    # df_tabla_interactiva = df_filtrado[[c for c in columnas_visibles if c in df_filtrado.columns]].copy()
    
    # if not df_tabla_interactiva.empty:
    #     df_tabla_interactiva['Fecha_Hora'] = df_tabla_interactiva['Fecha_Hora'].dt.strftime('%Y-%m-%d %H:%M:%S')
    #     if 'Monto' in df_tabla_interactiva.columns:
    #         df_tabla_interactiva['Monto'] = df_tabla_interactiva['Monto'].map(lambda x: f"${x:,.2f}")
        
    #     # Dibujamos la tabla sin permitir interacción de selección masiva
    #     st.dataframe(
    #         df_tabla_interactiva, 
    #         use_container_width=True, 
    #         hide_index=True,
    #         on_select="ignore"
    #     )

    #     # 🚨 INYECCIÓN CSS: Oculta los íconos flotantes de descarga integrados de Streamlit (el ojo, la flecha de descarga y expandir)
    #     st.markdown("""
    #         <style>
    #         [data-testid="stElementToolbar"] {
    #             display: none !important;
    #         }
    #         </style>
    #     """, unsafe_allow_html=True)
    # else:
    #     st.info("ℹ️ No hay registros detallados disponibles para mostrar.")

    # =====================================================================
    # 6. TABLA INTERACTIVA DE DATOS DE AUDITORÍA (BLOQUEO ESTÁTICO DE DESCARGAS)
    # =====================================================================
    st.subheader("🔍 Auditor de Registros Detallados (Data In-Depth)")
    st.markdown("Usa la barra superior de la tabla para buscar términos, ordenar columnas o expandir transacciones:")
    
    # 🚨 NOTA REPETIDA DE SEGURIDAD: Si tenías 'st.download_button' en alguna línea, bórralo por completo.
    
    columnas_visibles = ['Fecha_Hora', 'Compañía', 'Usuario', 'Acción', 'Monto', 'Referencia', 'Ventana_Detalle']
    df_tabla_interactiva = df_filtrado[[c for c in columnas_visibles if c in df_filtrado.columns]].copy()
    
    if not df_tabla_interactiva.empty:
        df_tabla_interactiva['Fecha_Hora'] = df_tabla_interactiva['Fecha_Hora'].dt.strftime('%Y-%m-%d %H:%M:%S')
        if 'Monto' in df_tabla_interactiva.columns:
            df_tabla_interactiva['Monto'] = df_tabla_interactiva['Monto'].map(lambda x: f"${x:,.2f}")
        
        # 🚨 SOLUCIÓN ABSOLUTA: Convertimos el DataFrame a un formato HTML estilizado.
        # Esto remueve físicamente el motor interactivo de Streamlit, haciendo imposible que aparezca el botón de 'Download'.
        tabla_estatica_html = df_tabla_interactiva.style.to_html(index=False)
        
        # Inyectamos estilos corporativos para que el HTML se adapte estéticamente a tu tema oscuro de DaDiMAC
        st.markdown(f"""
            <div style="overflow-x:auto; max-height:450px; border:1px solid #2e3136; border-radius:6px;">
                <style>
                    table {{ width: 100%; border-collapse: collapse; font-family: sans-serif; font-size: 13px; color: #f0f2f6; background-color: #131722; }}
                    th {{ background-color: #1e222d; color: #2678fe; padding: 12px; text-align: left; border-bottom: 2px solid #2e3136; font-weight: bold; position: sticky; top: 0; }}
                    td {{ padding: 10px 12px; border-bottom: 1px solid #2e3136; white-space: nowrap; }}
                    tr:hover {{ background-color: #1c2030; }}
                </style>
                {tabla_estatica_html}
            </div>
        """, unsafe_allow_html=True)
        st.caption("🔒 Seguridad Perimetral: La extracción masiva y descarga de este set de datos está restringida por la Gerencia.")
    else:
        st.info("ℹ️ No hay registros detallados disponibles para mostrar.")

