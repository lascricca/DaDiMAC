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

# CORREO_MASTER: Tu bandeja personal donde centralizas las auditorías si fuese necesario.
CORREO_MASTER = "dadimacalarma@gmail.com"


def inicializar_sesion():
    """Mantiene la persistencia del estado de autenticación en la nube"""
    if "autenticado" not in st.session_state:
        st.session_state.autenticado = False
        st.session_state.usuario_email = None
        st.session_state.pantalla_actual = "login"
    if "esperando_verificacion" not in st.session_state:
        st.session_state.esperando_verificacion = False
#--------
# Parte 2
#--------
def enviar_correo_restablecimiento(email):
    """Dispara un correo electrónico de recuperación de clave vía Firebase Auth"""
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


def registrar_y_verificar_usuario(email, password):
    """
    Registra al usuario en Firebase mediante HTTP
    y le dispara el flujo de verificación de enlace nativo de Google de forma obligatoria.
    """
    payload_signup = {"email": email, "password": password, "returnSecureToken": True}
    try:
        respuesta_signup = requests.post(URL_SIGN_UP, json=payload_signup, headers=HEADERS_JSON)
        
        if respuesta_signup.status_code == 200:
            datos_signup = respuesta_signup.json()
            id_token = datos_signup.get("idToken")
            
            # Forzar a Firebase a enviar el correo con el link de verificación oficial
            payload_verify = {"requestType": "VERIFY_EMAIL", "idToken": id_token}
            respuesta_verify = requests.post(URL_PASSWORD_RESET, json=payload_verify, headers=HEADERS_JSON)
            
            if respuesta_verify.status_code == 200:
                return True, "🎉 Cuenta registrada. Es obligatorio que valides el enlace seguro enviado a tu correo antes de poder solicitar la activación."
            else:
                return True, "🎉 Cuenta registrada, pero el enlace no se pudo enviar automáticamente. Contacte a soporte."
        else:
            datos = respuesta_signup.json()
            error_msg = datos.get("error", {}).get("message", "Error al registrar")
            if error_msg == "EMAIL_EXISTS":
                error_msg = "Este correo electrónico ya está registrado en la plataforma."
            return False, f"⚠️ {error_msg}"
    except Exception as e:
        return False, f"❌ Error de conexión con Firebase: {str(e)}"


def validar_usuario_firebase(email, password):
    """
    Valida el inicio de sesión contra Firebase y verifica de forma estricta:
    1. Que el usuario haya validado el link enviado a su correo.
    2. Que la Gerencia lo haya habilitado manualmente en la consola.
    """
    payload = {
        "email": email,
        "password": password,
        "returnSecureToken": True
    }
    try:
        respuesta = requests.post(URL_SIGN_IN, json=payload, headers=HEADERS_JSON)
        if respuesta.status_code == 200:
            datos = respuesta.json()
            
            # ESCUDO 1: Verificar si el usuario ya hizo clic en el link de su correo
            # La API de Firebase retorna un booleano en el campo 'registered' o requiere inspeccionar el token.
            # Para asegurar la lectura del estado 'emailVerified' sin decodificar JWT localmente, 
            # evaluamos la respuesta nativa de la cuenta en el perfil.
            email_verificado = datos.get("registered", False) 
            
            # Hacemos una segunda mini-petición ligera para extraer los metadatos reales del perfil (emailVerified)
            id_token = datos.get("idToken")
            url_get_user = f"https://googleapis.com{API_KEY}"
            res_perfil = requests.post(url_get_user, json={"idToken": id_token}, headers=HEADERS_JSON)
            
            if res_perfil.status_code == 200:
                datos_perfil = res_perfil.json().get("users", [{}])[0]
                # Si el usuario NO ha validado el enlace de su correo electrónico, se le rebota inmediatamente
                if not datos_perfil.get("emailVerified", False):
                    return False, "⚠️ Correo No Validado: Primero debes ingresar a tu bandeja de entrada y hacer clic en el enlace seguro enviado por Google para activar tu cuenta."
            
            email_autenticado = datos.get("email").strip().lower()
            return True, email_autenticado
            
        else:
            datos = respuesta.json()
            error_code = datos.get("error", {}).get("message", "Error de acceso")
            
            # ESCUDO 2: Captura si el usuario ya validó su correo pero tú lo mantienes deshabilitado en tu consola Firebase Auth
            if error_code in ["USER_DISABLED", "ADMIN_DISABLED"]:
                return False, "🔒 Acceso Retenido: Tu correo ha sido verificado con éxito, pero tu acceso al panel requiere la activación manual de la Gerencia. Se te notificará una vez aprobado."
            
            if error_code in ["EMAIL_NOT_FOUND", "INVALID_PASSWORD", "INVALID_LOGIN_CREDENTIALS"]:
                error_code = "Credenciales incorrectas o inválidas."
            return False, f"⚠️ {error_code}"
    except Exception as e:
        return False, f"❌ Error de red: {str(e)}"
#--------
# Parte 3
#--------
def login_sidebar():
    """Despliega la pasarela de control de identidad en la barra lateral mediante API REST"""
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
            
            if st.session_state.esperando_verificacion:
                st.sidebar.info("📩 Proceso Inicializado: Tu cuenta ha sido enviada a Firebase Auth de forma exitosa.")
                st.sidebar.warning("⚠️ Recuerda revisar tu bandeja de entrada (o correo no deseado/spam) para validar tu dirección mediante el enlace seguro enviado por Google.")
                
                # Aviso de retención exigido
                st.sidebar.error("🔒 Estado: Acceso Retenido temporalmente por la administración. Debes esperar a que se te notifique por tu correo la autorización de acceso una vez que la gerencia verifique la alerta manualmente en la consola.")
                
                if st.sidebar.button("🔄 Entendido, ir al Login"):
                    st.session_state.esperando_verificacion = False
                    st.session_state.pantalla_actual = "login"
                    st.rerun()
            else:
                # CAMBIO CRÍTICO: Se elimina el flujo SMTP y se invoca la validación nativa HTTP de Firebase
                if st.sidebar.button("📧 Registrar Cuenta e Iniciar Validación"):
                    if nuevo_email and len(nueva_pass) >= 6:
                        exito, msg = registrar_y_verificar_usuario(nuevo_email, nueva_pass)
                        if exito:
                            st.session_state.esperando_verificacion = True
                            st.rerun()
                        else:
                            st.sidebar.error(msg)
                    else:
                        st.sidebar.error("⚠️ El correo es obligatorio y la contraseña debe tener 6 caracteres o más.")
            
            if not st.session_state.esperando_verificacion:
                if st.sidebar.button("⬅️ Volver al Login"):
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
