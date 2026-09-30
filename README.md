# 🚀 DaDiMAC — Dashboard Avanzado de Auditoría Interna

**DaDiMAC - Dashboard** es un aplicativo de uso de licencia configurado exclusivamente para **MAC & ASOCIADOS** sobre el ecosistema **SAGE 50 (Peachtree)**. Su función principal es extraer, consolidar y proyectar estadísticas avanzadas de los clics de auditoría gestionados por los usuarios contables en cada una de las compañías registradas en el servidor.

---

## 📜 Propiedad Intelectual y Licencia

⚠️ **AVISO DE CONFIDENCIALIDAD Y DERECHOS:**  
**DaDiMAC** es propiedad intelectual exclusiva de **L.A. Scricca Asesores, S.A.** Todos los derechos reservados. El uso de este Dashboard está sujeto a un contrato de licenciamiento privado y restrictivo. Queda estrictamente prohibida su reproducción, alteración, distribución o ingeniería inversa por parte de personal no autorizado.

---

## 📖 Descripción General del Uso del Aplicativo

El flujo operativo de DaDiMAC está diseñado bajo un estándar de control de tres pasos secuenciales para los auditores y directores de la firma:

1.  **Autenticación de Identidad:** Al ingresar al enlace web, el sistema permanece bloqueado de forma perimetral. Cada usuario debe colocar sus credenciales corporativas autorizadas. Si un consultor olvida su clave, el aplicativo cuenta con un botón de autoservicio que despacha un enlace criptográfico directamente a su bandeja de correo electrónico para restablecerla de forma autónoma.
2.  **Filtrado Multicompañía y Temporal:** Una vez superada la barrera de acceso, la barra lateral izquierda permite seleccionar de forma masiva o individual las empresas mediante sus nombres comerciales reales (`CompanyName`). El sistema adapta de forma dinámica el calendario para acotar la auditoría únicamente al rango real de fechas en el que esa sucursal registra movimientos.
3.  **Evaluación de Comportamiento e Inspección:** El lienzo principal entrega de inmediato los indicadores estadísticos clave (Hora Pico Promedio, Desviación Estándar y Volumen Financiero en dólares a través de la columna `MainAmt`). El auditor evalúa visualmente la regularidad de las jornadas mediante la Campana de Gauss, identifica anomalías operativas mediante el contador de *Alertas Nocturnas* (clics entre 00:00 y 06:00) y rastrea registros transaccionales específicos usando la tabla dinámica del final.

---

## 📊 Componentes Clave e Indicadores Analíticos

*   **Modelado Horario (Campana de Gauss):** Visualización de la densidad probabilística del esfuerzo laboral diario, aislando el comportamiento regular dentro del **68% del volumen central** de transacciones.
*   **Centro de Gravedad (μ):** Marcador matemático discontinuo que identifica la Hora Pico Promedio de transacciones en la firma.
*   **Desviación Estándar (σ):** Medición precisa de la dispersión de la carga de trabajo expresada de manera legible en horas y minutos.
*   **Ránkings de Esfuerzo (Top 10):** Gráficos horizontales interactivos del volumen transaccional segmentado por Empresas y por Usuarios Contables.
*   **Mapeo Financiero:** Sumatoria acumulada en tiempo real de los flujos monetarios operados a través de la columna **`MainAmt`**.
*   **Alertas de Seguridad Nocturna (00:00 - 06:00):** Aislamiento y segmentación estricta de las operaciones ejecutadas en la madrugada. Lejos de tipificar de forma automática cada registro como un indicador de fraude o acceso malicioso, este marcador funciona como un lente analítico multifactorial que permite al auditor diagnosticar tres escenarios operativos críticos:
    1.  **Diagnóstico de Sobrecarga y Salud Organizacional (Factor Humano):** Detección de jornadas laborales extendidas de forma extraordinaria. Si un usuario o sucursal concentra clics recurrentes en la madrugada, el indicador revela cuellos de botella operativos, jornadas críticas de cierres fiscales mal distribuidas o una alarmante falta de personal contable para procesar la carga en horario de oficina.
    2.  **Procesos Autónomos y Rutinas de Sistema (Logs Pasivos):** Identificación de clics automáticos generados por el propio motor de base de datos ODBC de Sage 50, rutinas programadas de mantenimiento en el servidor, indexaciones nocturnas o respaldos automatizados. Aislar estos eventos evita que el "ruido" pasivo del servidor distorsione el cálculo del rendimiento humano diurno en la Campana de Gauss.
    3.  **Control Perimetral y Mitigación de Riesgos (Seguridad de la Información):** Monitoreo preventivo ante anomalías reales de seguridad, tales como el uso no autorizado de credenciales activas fuera del horario comercial del despacho o intentos de alteración masiva de datos históricos en momentos de nula supervisión interna.

---

## 🔐 Seguridad y Autenticación Cloud

La plataforma implementa un bloqueo de seguridad perimetral administrado de forma serverless por **Google Firebase Authentication** conectada de forma directa con el proyecto corporativo de la firma.

---

## 🛠️ Stack Tecnológico

*   **Lenguaje:** Python 3
*   **Core UI:** Streamlit (Entorno web interactivo de alto rendimiento)
*   **Procesamiento:** Pandas & NumPy
*   **Gráficos:** Plotly Open Source (Lienzos vectoriales nativos)
*   **Identity Provider:** Firebase Auth REST API
