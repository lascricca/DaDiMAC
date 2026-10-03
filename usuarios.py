import requests
import streamlit as st
import random
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# =====================================================================
# CONFIGURACIÓN ESTÁTICA INTEGRAL DE GOOGLE FIREBASE IDENTITY API
# =====================================================================

# 1. Coloca aquí tu Web API Key (la encuentras en Firebase Console -> Configuración del proyecto)
API_KEY = "AIzaSyD8DMID7FFGdBEor0Wmiw7yOqVBZbWSe20" 

# 2. URLs oficiales y completas para la API REST de Firebase Auth
URL_SIGN_UP = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={API_KEY}"
URL_SIGN_IN = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={API_KEY}"
URL_PASSWORD_RESET = f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={API_KEY}"

# ENCABEZADO OBLIGATORIO DE RED PARA EL FIREWALL DE GOOGLE CLOUD
HEADERS_JSON = {"Content-Type": "application/json"}

# =====================================================================
# CONFIGURACIÓN MAESTRA DE MENSAJERÍA PARA CONTROL GERENCIAL
# =====================================================================
CORREO_EMISOR = "dadimacalarma@gmail.com"
PASSWORD_EMISOR = "mcgf ftyv lorg azun"  # Tu contraseña de aplicación de Google de 16 caracteres

# CORREO_MASTER: Tu bandeja personal donde recibirás los accesos pendientes.
CORREO_MASTER = "dadimacalarma@gmail.com"


def enviar_correo_smtp(destinatario, asunto, cuerpo_html):
    """Establece conexión directa con el servidor SMTP de Google para despachar alertas"""
    try:
        msg = MIMEMultipart()
        msg['From'] = CORREO_EMISOR
        msg['To'] = destinatario
        msg['Subject'] = asunto
        msg.attach(MIMEText(cuerpo_html, 'html'))
        
        server = smtplib.SMTP('://gmail.com', 587)
        server.starttls()
        server.login(CORREO_EMISOR, PASSWORD_EMISOR)
        server.sendmail(CORREO_EMISOR, destinatario, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"Falla en la pasarela de mensajería SMTP: {str(e)}")
        return False
#2
def inicializar_sesion():
    """Mantiene la persistencia del estado de autenticación en la nube"""
    if "autenticado" not in st.session_state:
        st.session_state.autenticado = False
        st.session_state.usuario_email = None
        st.session_state.pantalla_actual = "login"
    if "token_registro" not in st.session_state:
        st.session_state.token_registro = None
        st.session_state.datos_pendientes = None

def enviar_correo_restablecimiento(email):
    """Dispara un correo electrónico de recuperación de clave"""
    payload = {"requestType": "PASSWORD_RESET", "email": email}
    try:
        respuesta = requests.post(URL_PASSWORD_RESET, json=payload, headers=HEADERS_JSON)
        if respuesta.status_code == 200:
            return True, f"📩 Enlace enviado a **{email}**. Revisa tu bandeja de entrada o spam para restablecer tu contraseña."
        else:
            datos = respuesta.json()
            error_msg = datos.get("error", {}).get("message", "Error desconocido")
            return False, f"⚠️ Error de Firebase: {error_msg}"
    except Exception as e:
        return False, f"❌ Error de red: {str(e)}"

def registrar_usuario_firebase(email, password):
    """Inscribe un nuevo operador contable en tu base de datos de Firebase"""
    payload = {"email": email, "password": password, "returnSecureToken": True}
    try:
        respuesta = requests.post(URL_SIGN_UP, json=payload, headers=HEADERS_JSON)
        if respuesta.status_code == 200:
            return True, "🎉 Solicitud procesada con éxito."
        else:
            datos = respuesta.json()
            error_msg = datos.get("error", {}).get("message", "Error al registrar")
            if error_msg == "EMAIL_EXISTS":
                error_msg = "Este correo electrónico ya está registrado."
            return False, f"⚠️ {error_msg}"
    except Exception as e:
        return False, f"❌ Error de red: {str(e)}"

def validar_usuario_firebase(email, password):
    """Valida el inicio de sesión e interpreta los bloqueos nativos directamente desde Firebase Cloud"""
    payload = {
        "email": email,
        "password": password,
        "returnSecureToken": True
    }
    try:
        respuesta = requests.post(URL_SIGN_IN, json=payload, headers=HEADERS_JSON)
        if respuesta.status_code == 200:
            datos = respuesta.json()
            email_autenticado = datos.get("email").strip().lower()
            return True, email_autenticado
        else:
            datos = respuesta.json()
            error_code = datos.get("error", {}).get("message", "Error de acceso")
            
            # INTERCEPCIÓN EN LA NUBE: Si la cuenta está deshabilitada en tu consola Firebase Auth
            if error_code in ["USER_DISABLED", "ADMIN_DISABLED"]:
                return False, "🔒 Acceso Retenido: Tu cuenta está registrada en Firebase, pero requiere la activación manual de la Gerencia. Se te notificará por tu correo electrónico una vez otorgada la autorización."
            
            if error_code in ["EMAIL_NOT_FOUND", "INVALID_PASSWORD", "INVALID_LOGIN_CREDENTIALS"]:
                error_code = "Credenciales incorrectas o inválidas."
            return False, f"⚠️ {error_code}"
    except Exception as e:
        return False, f"❌ Error de red: {str(e)}"
#3
def login_sidebar():
    """Despliega la pasarela de control de identidad en la barra lateral con verificación OTP"""
    inicializar_sesion()
    
    if not st.session_state.autenticado:
        if st.session_state.pantalla_actual == "login":
            st.sidebar.header("🔐 Acceso DaDiMAC (Firebase Cloud)")
            email = st.sidebar.text_input("Correo electrónico:", key="auth_email").strip().lower()
            password = st.sidebar.text_input("Contraseña:", type="password", key="auth_pass")
            
            col_btn1, col_btn2 = st.sidebar.columns(2)
            with col_btn1:
                if st.sidebar.button("🔓 Entrar"):
                    if email and password:
                        exito, email_retornado = validar_usuario_firebase(email, password)
                        if exito:
                            st.session_state.autenticado = True
                            st.session_state.usuario_email = email_retornado
                            st.rerun()
                        else:
                            st.sidebar.error(email_retornado)
                    else:
                        st.sidebar.error("⚠️ Completa los campos.")
            
            with col_btn2:
                if st.sidebar.button("📝 Registrarse"):
                    st.session_state.pantalla_actual = "registro"
                    st.rerun()
            
            st.sidebar.markdown("---")
            if st.sidebar.button("❓ Olvidé mi Contraseña"):
                st.session_state.pantalla_actual = "recuperar"
                st.rerun()
                
        elif st.session_state.pantalla_actual == "registro":
            st.sidebar.header("📝 Registro de Auditor")
            nuevo_email = st.sidebar.text_input("Correo corporativo:", key="reg_email").strip().lower()
            nueva_pass = st.sidebar.text_input("Asigna una Contraseña (mín. 6 caracteres):", type="password", key="reg_pass")
            
            if st.session_state.token_registro is not None:
                st.sidebar.warning("🔑 Introduce el token enviado a tu casilla para confirmar la operación:")
                token_ingresado = st.sidebar.text_input("Token de 6 dígitos:", key="reg_token_input").strip()
                
                col_token1, col_token2 = st.sidebar.columns(2)
                with col_token1:
                    if st.sidebar.button("✅ Verificar Token"):
                        if token_ingresado == str(st.session_state.token_registro):
                            datos = st.session_state.datos_pendientes
                            
                            # REGISTRO AUTOMÁTICO REAL EN LA PLATAFORMA DE FIREBASE
                            exito, msg = registrar_usuario_firebase(datos["email"], datos["pass"])
                            
                            if exito:
                                asunto_master = "🚨 Alerta DaDiMAC: Nueva solicitud de autorización de registro"
                                cuerpo_master = f"""
                                <h3>Solicitud de Acceso Pendiente</h3>
                                <p>El siguiente usuario ha verificado su casilla y se ha registrado automáticamente en Firebase Auth:</p>
                                <ul>
                                    <li><b>Usuario Contable:</b> {datos['email']}</li>
                                    <li><b>Fecha/Hora:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
                                    <li><b>Estado en Firebase:</b> Registrado. (Proceda a habilitarlo en su consola si corresponde).</li>
                                </ul>
                                <p>Para permitirle el acceso, recuerde ingresar a su consola web de Firebase Auth y activar este usuario.</p>
                                """
                                enviar_correo_smtp(CORREO_MASTER, asunto_master, cuerpo_master)
                                
                                st.sidebar.info("📩 Cuenta creada con éxito en Firebase. Tu acceso al panel se encuentra retenido por seguridad. Debes esperar a que se te notifique por tu correo la autorización de acceso una vez que la gerencia verifique la alerta manualmente.")
                                st.session_state.token_registro = None
                                st.session_state.datos_pendientes = None
                            else:
                                st.sidebar.error(msg)
                        else:
                            st.sidebar.error("❌ Token incorrecto. Verifique el código.")
                with col_token2:
                    if st.sidebar.button("🔄 Cancelar"):
                        st.session_state.token_registro = None
                        st.session_state.datos_pendientes = None
                        st.rerun()
            else:
                if st.sidebar.button("📧 Solicitar Token de Verificación"):
                    if nuevo_email and len(nueva_pass) >= 6:
                        token_generado = random.randint(100000, 999999)
                        asunto_usuario = f"🔑 Código de Verificación DaDiMAC: {token_generado}"
                        cuerpo_usuario = f"""
                        <h2>Verificación de Identidad - DaDiMAC</h2>
                        <p>Tu código de un solo uso para comprobar tu casilla e iniciar tu proceso de alta automática en Firebase es:</p>
                        <h1 style='color:#2678FE; letter-spacing: 4px;'>{token_generado}</h1>
                        <p>Introdúcelo en la barra lateral del sistema.</p>
                        """
                        if enviar_correo_smtp(nuevo_email, asunto_usuario, cuerpo_usuario):
                            st.session_state.token_registro = token_generado
                            st.session_state.datos_pendientes = {"email": nuevo_email, "pass": nueva_pass}
                            st.rerun()
                        else:
                            st.sidebar.error("❌ Error de envío. Verifique que el correo ingresado sea válido.")
                    else:
                        st.sidebar.error("⚠️ El correo es obligatorio y la contraseña debe tener 6 caracteres o más.")
            
            if st.sidebar.button("⬅️ Volver al Login"):
                st.session_state.token_registro = None
                st.session_state.datos_pendientes = None
                st.session_state.pantalla_actual = "login"
                st.rerun()
                
        elif st.session_state.pantalla_actual == "recuperar":
            st.sidebar.header("🔄 Restablecer Clave")
            email_recup = st.sidebar.text_input("Introduce tu Correo registrado:", key="rec_email_input").strip().lower()
            
            if st.sidebar.button("🚀 Enviar Enlace Seguro"):
                if email_recup:
                    exito, mensaje = enviar_correo_restablecimiento(email_recup)
                    if exito:
                        st.sidebar.info(mensaje)
                    else:
                        st.sidebar.error(mensaje)
                else:
                    st.sidebar.error("⚠️ Escribe tu correo.")
                    
            if st.sidebar.button("⬅️ Volver al Login"):
                st.session_state.pantalla_actual = "login"
                st.rerun()
                
        return False
    else:
        st.sidebar.success(f"👤 Sesión Activa\n{st.session_state.usuario_email}")
        st.sidebar.caption("🔒 Autenticación en la Nube vía Firebase")
        if st.sidebar.button("🔒 Cerrar Sesión"):
            st.session_state.autenticado = False
            st.session_state.usuario_email = None
            st.session_state.pantalla_actual = "login"
            st.rerun()
        return True
